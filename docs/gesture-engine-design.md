# Gesture Engine — Design Document

**Status:** Draft. Open questions inline as `[RESEARCH]` and `[VERIFY]` markers.
**Target hardware:** Sofle Ergomech (Hybrid), nice!nano v2, Cirque Pinnacle GlidePoint over I2C (right shield), nice-view-gem display on left.
**Target stack:** Zephyr 4.1, ZMK on `main` (post-HWMv2 migration).
**Ambition:** smoothest, most intentional pointing-input feel available in any open-source keyboard firmware.

This is a living design contract. Code in the gesture-engine module conforms to this document; if the code needs to diverge, this document is updated first.

---

## 1. Purpose & scope

Build a ZMK input processor that takes raw absolute-mode events from the upstream Zephyr Pinnacle driver and emits clean, well-shaped relative motion / scroll / button events to ZMK's HID pipeline.

### In scope

- Tap detection with distance + time thresholds, configurable button
- Drag-lock (tap-tap-and-hold to lock the primary button, tap again to release)
- Cursor motion (absolute coordinates → relative deltas with sub-pixel accumulator)
- Inertial cursor (post-release coasting with time-constant decay)
- Circular scroll (rim-initiated angular tracking → scroll wheel)
- Right-side vertical edge scroll (rim-initiated)
- Top-side horizontal edge scroll (rim-initiated)
- Per-axis acceleration curves (configurable)
- Configurable layer-conditional behavior swaps (e.g., RAISE makes the whole touchpad a scroll surface)

### Out of scope (initial release)

- Multi-finger gestures — the Cirque GlidePoint sensor is single-touch
- Gestures that require fingerprint-like contact-shape information — Cirque only reports position + Z
- OS-side gesture engines (this is firmware-side, OS-agnostic by design)

### Non-goals

- Matching libinput feature-for-feature — we're optimizing for *feel*, not breadth
- General-purpose touchpad driver — this is tightly coupled to Cirque Pinnacle on our hardware

---

## 2. Hardware context

### Cirque Pinnacle 1CA027 ASIC

The trackpad-side controller. Single-touch capacitive sensor. The ASIC can operate in two output modes:

- **Relative mode**: outputs (dx, dy) deltas + a few button bits per sample. Some firmware features (tap, glide-extend, edge scroll, secondary tap) are implemented inside the ASIC itself and only available here.
- **Absolute mode**: outputs (x, y, z) absolute coordinates. The ASIC-internal gestures are NOT available — we have to implement everything in our driver.

We choose **absolute mode** because:
1. We need precise position information for circular scroll, edge zones, and rim detection.
2. ASIC-internal gestures aren't tunable to the level we want.
3. Upstream Zephyr 4.1 driver supports absolute mode natively via `data-mode = "absolute"`.

The Z value: **`[RESOLVED — R1]`** Read the upstream Zephyr driver's sample-parsing code:

```c
sample->abs_z = rx[3] & 0x3F;          // 6-bit, range 0-63
```

```c
static bool pinnacle_is_idle_sample(const union pinnacle_sample *sample) {
    return (sample->abs_x == 0 && sample->abs_y == 0 && sample->abs_z == 0);
}
```

Conclusion: **Z exists, is a 6-bit (0–63) contact-strength/signal-magnitude indicator, NOT true force/pressure.** The user was right that it's not pressure-sensitive in the conventional sense (no piezo element). But it's perfectly usable as a binary touch-presence signal:
- Finger present → x, y, z all nonzero
- No finger → x = y = z = 0

The chip uses the same convention internally for `is_idle_sample()`. We adopt the same convention. P4 (Z-based touch detection) stays in the design. Threshold should be low (probably 1–4 out of 63) since we're testing presence, not classifying contact quality.

### nRF52840 (on nice!nano v2)

- ARM Cortex-M4F with **single-precision FPU only**
- 256 KB RAM, 1 MB flash, plenty of headroom
- Double-precision floats emulate in software (slow) — **rule: only `float`, never `double` in the hot path**

### ZMK split architecture

- **Right shield** = peripheral. Reads Cirque over I2C. Forwards input events over BLE split protocol to central.
- **Left shield** = central. Receives events from peripheral, runs the gesture engine, emits HID reports to the host.
- **Where the gesture engine runs**: on the central (left) side. The peripheral's role is just to relay raw Cirque events. This means:
  - The input event flow on the central side is: BLE split → input subsystem → our gesture processor → HID output
  - Latency includes the BLE split hop. Our gesture engine doesn't get the events at the exact moment the finger touched the trackpad — they're already ~one BLE interval delayed.

`[VERIFY]` — confirm that ZMK's split-input protocol preserves event timestamps. If the central re-stamps events with its own arrival time (rather than the peripheral's sample time), velocity calculations will be slightly off because the BLE jitter contributes to apparent "time between samples". Probably not a deal-breaker but worth knowing.

### nice-view-gem display

Not directly relevant to gesture engine, but worth noting that the display is on the central. Heavy work in the gesture engine could compete with display rendering for CPU time. We need to keep the gesture engine's hot path tight.

---

## 3. Design principles

These principles are derived from reading halfdane's source carefully and noting where their implementation surfaced bugs or felt sub-optimal. Each rule below is anchored in a specific lesson we don't want to repeat.

### P1: Sample-oriented, not event-oriented

Pinnacle absolute mode emits three events per sample: ABS_X, ABS_Y, ABS_Z (with `sync` set only on Z). Halfdane assumed two events per sample (X-Y alternation), which desyncs against the upstream driver. We accumulate (x, y, z) across the three events and act only when we see the `sync` flag, treating each fully-synced sample as the atomic unit of input.

### P2: Float32 only

nRF52840 has single-precision hardware float only. `double` emulates in software. All gesture math uses `float`. No exceptions in the hot path.

### P3: Subpixel accumulators everywhere

Absolute-mode coordinates are integer (Pinnacle reports up to 2048 across the active area). Deltas can be sub-1-unit. If we truncate to int every sample, we lose motion — particularly noticeable on slow precise movements. Every output-rate scaling carries a `float` remainder accumulator. Integer events emit only when the accumulated value crosses 1.0, with the remainder kept.

### P4: Touch-state from Z, not from timeouts (if Z is available)

If the Pinnacle Z value reliably signals contact, use it: `Z > Z_threshold` = touching, `Z = 0` = not touching. The touch start/end edge is exact, no timeout heuristics needed. If Z turns out to be useless on our part, fall back to halfdane's pattern: a delayed work item fires after N ms of no events. `[RESEARCH]` — pending.

### P5: One canonical state machine, mutually exclusive states

At any moment, we are in exactly one of:
- `IDLE` — no finger touching
- `MAYBE_TAP` — finger just landed, haven't decided what it is yet
- `MOVING` — committed to cursor motion
- `CIRCULAR_SCROLL` — committed to circular scroll
- `EDGE_SCROLL_VERTICAL` — committed to right-side vertical scroll
- `EDGE_SCROLL_HORIZONTAL` — committed to top-side horizontal scroll
- `DRAG_LOCKED` — primary button held, cursor motion continues until next tap
- `INERTIAL_COAST` — no finger, coast remaining velocity until decay

State transitions are explicit, logged at DBG level, and have unambiguous trigger conditions. No "I'm tracking circular AND tap AND inertial simultaneously" like halfdane's parallel-handler design.

### P6: Deadbands and thresholds

Raw signals never reach output. Every gesture has a deadband:
- Tap → minimum distance moved must be < tap_max_distance OR it's not a tap
- Circular scroll → minimum accumulated angle before emitting first scroll event (prevents finger-wobble misfires)
- Inertial cursor → minimum release velocity OR no coast
- Cursor motion → optional minimum frame-to-frame delta to suppress jitter at slow speeds

Defaults aim for "almost zero deadband" with a hand-tuned knob for users who want stricter filtering.

### P7: Time-constant decay, not per-tick multiplier

Halfdane decays inertia by a flat percent each tick (`v *= 0.7` every ~15ms). This couples decay feel to sample rate. We use exponential decay with a configurable time constant τ: `v = v0 * exp(-t/τ)`. Decay feel is independent of sample rate, intuitive to tune ("velocity halves every 200 ms").

### P8: Recency-weighted velocity estimation

For inertial activation, velocity is computed as an exponentially-weighted moving average over the last ~5 samples, not the single most recent sample. A jittery last sample doesn't ruin the fling direction.

### P9: Configurable everything, sensible defaults

Every threshold, time constant, deadband, and rate is a DT property with a default value backed by reasoning in this doc. Users who like the defaults change nothing; users who want to tune have a single point of customization (the overlay).

### P10: Logging discipline

Every state transition and every threshold crossing logs at `LOG_DBG`. In production builds (`CONFIG_ZMK_LOG_LEVEL=2` info or lower), these compile out completely. In a debug build, the log tells the full story of what the gesture engine decided and why.

---

## 4. Architecture

### 4.1 Module shape

A single Zephyr input processor, registered via DT with `compatible = "zmk,input-processor-gesture-engine"` (note: distinct name from halfdane's to avoid namespace collision if their module is ever ALSO loaded).

Internally, four logical units:

```
┌──────────────────────────────────────────────────────────┐
│  Input Processor: handle_event()                          │
│  (called once per ABS_X / ABS_Y / ABS_Z event)            │
└──────────────────┬───────────────────────────────────────┘
                   │ accumulates events until SYN_REPORT
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Sample Builder                                           │
│  Emits a Sample{x, y, z, t} on sync                       │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│  Touch State Machine                                      │
│  Owns current State + transitions                         │
│  Dispatches to gesture handlers based on State            │
└─┬──────────┬──────────┬──────────┬──────────┬───────────┘
  │          │          │          │          │
  ▼          ▼          ▼          ▼          ▼
┌────┐  ┌────┐  ┌──────┐  ┌──────┐  ┌────────┐
│Tap │  │Move│  │Circ. │  │Edge  │  │Inertial│
│    │  │    │  │Scroll│  │Scroll│  │Cursor  │
└────┘  └────┘  └──────┘  └──────┘  └────────┘
```

Each gesture module exposes a small interface (`on_enter`, `on_sample`, `on_exit`) — the state machine calls these based on state transitions. Only one gesture module is active at a time (P5).

### 4.2 File layout

```
modules/sofle-gesture-engine/
├── CMakeLists.txt
├── Kconfig
├── zephyr/
│   └── module.yml
├── dts/
│   ├── bindings/
│   │   └── zmk,input-processor-gesture-engine.yaml
│   └── behaviors/
│       └── gesture_engine.dtsi
└── src/
    ├── gesture_engine.c          # Input processor entry, sample builder
    ├── state_machine.c           # State + transitions, dispatch
    ├── state_machine.h
    ├── gesture_tap.c
    ├── gesture_tap.h
    ├── gesture_move.c
    ├── gesture_move.h
    ├── gesture_circular_scroll.c
    ├── gesture_circular_scroll.h
    ├── gesture_edge_scroll.c
    ├── gesture_edge_scroll.h
    ├── gesture_inertial.c
    ├── gesture_inertial.h
    ├── velocity_estimator.c      # EWMA velocity, shared utility
    ├── velocity_estimator.h
    └── math_util.h               # atan2f convention, deadband helpers
```

### 4.3 Threading model

**`[R2] resolved.`** Zephyr 4.1 defaults `CONFIG_INPUT_MODE_THREAD=y` — input events are dequeued and dispatched on a **dedicated input thread**, separate from both the system work queue and any IRQ handler. The full event path:

1. Pinnacle IRQ fires on data-ready GPIO → schedules a work item
2. Work item runs on **system work queue** → reads I2C, calls `input_report_abs()` × 3
3. `input_report_abs()` enqueues events on the input subsystem message queue
4. **Dedicated input thread** dequeues events, calls our processor's `handle_event()` synchronously per event
5. Our `handle_event()` updates state, may mutate event or emit downstream
6. Our delayed work items (INERTIAL_COAST tick, drag-lock timer) fire on **system work queue thread**

Implications:

- **Input thread and system work queue are different threads** → real concurrency between gesture handlers (input thread) and coast/timer callbacks (sys workqueue).
- **The race we must handle**: INERTIAL_COAST tick is running on sys workqueue when a new finger touch arrives on input thread. Both want to mutate the state machine.
- **Solution**: Input thread, on receiving a new touch event, calls `k_work_cancel_delayable_sync()` on the coast work item. This **blocks briefly** waiting for any in-flight coast tick to complete before proceeding. After return, no coast tick is running and none can start. State machine transition proceeds safely. No long-term locks needed.
- **State variable atomicity**: gesture state is read/written by both threads but transitions are gated by `cancel_sync`, so we don't need atomics. The state variable is naturally `_Atomic`-aligned and reads are consistent on Cortex-M4.

**Stack size**: `CONFIG_INPUT_THREAD_STACK_SIZE` defaults to 1024 in upstream Zephyr — likely too small once we add float math (atan2f, expf, sqrtf). Bump to 2048 minimum, 4096 if profiling shows it.

### 4.3.1 Input thread starvation concern

Long-running gesture handlers block the next input event from being processed. Our hot path needs to stay tight (target: < 200 µs per sample on the central). Math is the main risk:
- atan2f: ~5 µs on M4F
- sqrtf: ~3 µs on M4F  
- expf: ~20 µs on M4F (the worst — used in inertial decay)

Mitigation: only call expf during the coast tick (already on sys workqueue, not input thread). The input-thread hot path uses only atan2f + multiplies. Budget: ~50 µs per sample including bookkeeping. Plenty of margin against 200 µs.

### 4.4 ZMK split protocol concern

The gesture engine runs on the central. Events come from the peripheral over BLE split. `[VERIFY]` — confirm:
1. Event payload preserves type/code/value exactly
2. Sync flag is propagated correctly
3. Whether timestamps survive (if not, we use central-side `k_uptime_get()` for sample timestamps)

---

## 5. State machine (formal)

### States

| State | Description | Emits movement? | Emits scroll? | Emits buttons? |
|---|---|:-:|:-:|:-:|
| `IDLE` | No finger on pad | — | — | — |
| `MAYBE_TAP` | Touching, < tap_window_ms elapsed | No (suppressed) | — | — |
| `MOVING` | Touching, committed to cursor motion | Yes | — | — |
| `CIRCULAR_SCROLL` | Touching, committed to angular scroll | No | Yes (vertical) | — |
| `EDGE_SCROLL_VERTICAL` | Touching, committed to right-edge scroll | No | Yes (vertical) | — |
| `EDGE_SCROLL_HORIZONTAL` | Touching, committed to top-edge scroll | No | Yes (horizontal) | — |
| `DRAG_LOCKED` | Primary button held, cursor motion ongoing | Yes | — | Holds primary |
| `INERTIAL_COAST` | No finger, coasting motion | Yes (decaying) | — | — |

### Transitions

```
                       ┌─────────────────────────┐
                       │                         │
                       ▼                         │
                   ┌───────┐                     │
        ┌──────────│ IDLE  │──────────┐          │
        │          └───────┘          │          │
        │  finger-down                │          │
        │  (Z>thr OR first event)     │ finger-up & vel>thr
        │                             │ (no other state)
        ▼                             │          │
   ┌───────────┐                   ┌────────────┐│
   │MAYBE_TAP  │──────────────────▶│INERTIAL    ││
   └───────────┘  finger-up,       │COAST       ││
        │         no other state   └────────────┘│
        │                             │  velocity decays
        │  decision criteria reached  │  to zero
        │  (see § 6)                  │          │
        ├─────────┬──────────┬────────┴──────┬───┘
        │         │          │               │
        ▼         ▼          ▼               ▼
    ┌──────┐ ┌────────┐ ┌──────────┐  ┌─────────────┐
    │MOVING│ │CIRC.   │ │EDGE_SCR. │  │DRAG_LOCKED  │
    │      │ │SCROLL  │ │V or H    │  │             │
    └───┬──┘ └────┬───┘ └────┬─────┘  └──────┬──────┘
        │        │           │               │
   finger-up    f-up        f-up        on next tap
        │        │           │               │
        ▼        ▼           ▼               ▼
       (vel-eval to maybe enter INERTIAL_COAST, else IDLE)
```

### Decision criteria for `MAYBE_TAP → committed state`

`MAYBE_TAP` exits when ONE of these becomes true:
1. **Total distance moved exceeds `tap_max_distance`** → committed to motion. Then sub-decide:
   - Started in `circular_scroll_rim` AND first motion has angular component → `CIRCULAR_SCROLL`
   - Started in `edge_scroll_right_band` AND first motion is more Y than X → `EDGE_SCROLL_VERTICAL`
   - Started in `edge_scroll_top_band` AND first motion is more X than Y → `EDGE_SCROLL_HORIZONTAL`
   - Otherwise → `MOVING`
2. **Time exceeds `tap_window_ms`** AND distance < tap_max_distance → committed to motion (likely a hold-then-drag intent). Go to `MOVING`.
3. **Finger lifts** before either of the above → it was a tap. Emit tap event (with possible drag-lock follow-through logic, see § 6).

This is meaningfully better than halfdane's "wait fixed timeout, then tap if not touching" — we exit `MAYBE_TAP` as soon as we *know* it's not a tap (motion exceeded), rather than waiting the full timeout. This eliminates the "sluggish beginning of regular touches" issue halfdane's `prevent_movement_during_tap` flag tried to work around.

---

## 6. Per-gesture algorithms

### 6.1 Tap (and drag-lock)

**Tap criteria**: finger lifts while in `MAYBE_TAP` state. Emit `BTN_n` press + release.

**Drag-lock criteria** (extension): after a tap is emitted, watch for a follow-up touch within `drag_lock_window_ms` (default 250 ms). If a touch begins in that window AND ends with distance > tap_max_distance, we enter `DRAG_LOCKED` state — the primary button is held while the finger moves. State exits on the next tap.

This solves the click-and-drag problem cleanly: tap-tap-drag = locked drag. No need to hold a keyboard key while moving the trackpad.

```
tap-tap-drag sequence:
  finger down → MAYBE_TAP
  finger up   → tap emitted, drag_lock_window timer starts
  finger down (within window) → ENTER DRAG_LOCKED (button pressed)
  finger moves                → cursor moves while button held
  finger up                   → release button, → INERTIAL_COAST or IDLE
```

**Tunables** (defaults sourced from libinput's tuned values where available — see `[R5]`). Two independent toggles control the drag behavior, mirroring libinput's model:

- `tap-window-ms` — max duration of a tap (default 180 ms; libinput uses 180 — 15+ years of touchpad tuning agree).
- `tap-max-distance` — max movement during tap window in sensor units (default 60; libinput uses 1.3 mm, which on Cirque GlidePoint Circle 40mm with default Zephyr scaling ≈ 58 sensor units).
- `tap-button` — which mouse button to send (default `MB1`)
- `drag-enable` (boolean, default `true`) — does a tap followed by a touch within `drag-window-ms` start a drag at all? Disabling means taps are always just clicks; the follow-up-touch pattern is ignored.
- `drag-window-ms` — time after first tap during which a second touch starts a drag (default 180 ms; libinput uses 160 ms base + 20 ms/finger).
- `drag-lock-mode` — what happens to the held button at end of a drag. Three values:
  - `off` — finger lift releases the button immediately. Classic tap-and-drag.
  - `sticky` (default per `[D3]`) — finger lift keeps button held; next finger-down resumes the drag; a single tap releases.
  - `timeout` — finger lift keeps button held for `drag-lock-release-timeout-ms`, then auto-releases if no new touch arrives.
- `drag-lock-release-timeout-ms` — only used when `drag-lock-mode = timeout` (default 300 ms; matches libinput's `DEFAULT_DRAGLOCK_TIMEOUT_PERIOD`).

### 6.2 Cursor motion

**On each `MOVING` state sample**:
1. Compute `dx = x - prev_x`, `dy = y - prev_y` in sensor units
2. Apply per-axis acceleration curve (see § 6.5)
3. Apply CPI scaling (`cursor-scale-num / cursor-scale-den`) with `float` math
4. Accumulate into `remainder_x`, `remainder_y`
5. Emit `INPUT_REL_X = floor(remainder_x)`, `INPUT_REL_Y = floor(remainder_y)`
6. Keep fractional parts in remainders for next sample

**Tunables**:
- `cursor-scale-num` / `cursor-scale-den` — CPI multiplier
- `cursor-deadband` — minimum delta to emit (default 0, no deadband)
- `acceleration-curve` — `linear` / `quadratic` / `cubic` (default `quadratic`)

### 6.3 Circular scroll

**Two-phase design** — borrows from QMK's well-validated approach (see `[R7]`). Touch in the rim alone is NOT enough to enter scroll mode; we additionally validate that the motion is tangential (along the rim) rather than radial (toward/away from center). This prevents false-positive scrolls when the user touches the rim and moves toward the center for a normal cursor action.

**State sub-machine** (inside the top-level `CIRCULAR_SCROLL` state, technically a sub-state of `MAYBE_TAP`):

```
        MAYBE_TAP
            │ touch in rim
            ▼
      ┌─────────────────┐
      │ SCROLL_DETECTING│  — cursor motion suppressed
      └─┬───────────┬───┘
        │           │
   <trigger_px      ≥ trigger_px moved
   no decision yet  │
        │     ┌─────┴────────────┐
        │     │ measure angle    │
        │     │ relative to      │
        │     │ radial direction │
        │     └─────┬────────────┘
        │           │
        │      ┌────┴────┐
        │      │         │
        │   tangential  radial
        │   (>50°)      (<50°)
        │      │         │
        ▼      ▼         ▼
      (still   SCROLL_VALID  NOT_SCROLL
       detecting)  │         (release suppression,
                   │          fall back to MOVING)
                   ▼
              emit wheel
              clicks based
              on angle accum
```

**Algorithm details:**

1. **Entry to SCROLL_DETECTING**: touch lands and `radial_distance / active_radius >= (1 - circular-scroll-rim-pct/100)`. Record `(x0, y0)` and start tracking. Cursor motion is suppressed during this phase.
2. **In SCROLL_DETECTING, per sample**: compute distance from initial touch point. If less than `circular-scroll-trigger-px` units moved, stay in DETECTING.
3. **At `trigger_px`**: compute the angle of the motion vector relative to the radial direction from center. If the angle is greater than `circular-scroll-trigger-angle` (default 50°), motion is mostly tangential → transition to SCROLL_VALID. Otherwise (motion is mostly radial, e.g., the user is reaching toward the center for a click) → transition to NOT_SCROLL, release the suppressed cursor events.
4. **In SCROLL_VALID, per sample**: compute current angle from center `θ = atan2f(y - cy, x - cx)`. Accumulate angular delta `Δθ` (normalized to `[-π, π]`). When `|angle_accum| >= 2π / wheel-clicks`, emit `INPUT_REL_WHEEL` with `sign(angle_accum)` and subtract that quantum from the accumulator. Keep the remainder for sub-click precision.

This guards against the two failure modes that plague naive circular-scroll implementations:
- False positive: user touches rim for cursor work, gets stuck in scroll mode (solved by tangential validation)
- Jitter spurious scrolls: tiny angle wiggle generates output (solved by quantized emit on accumulator threshold)

**Tunables** (defaults from QMK `[R7]`):
- `circular-scroll-enable` (boolean)
- `circular-scroll-rim-pct` — width of the activation rim as percent of radius (default 33; QMK uses 33, more forgiving than libinput-style narrow bands)
- `circular-scroll-trigger-px` — motion required to validate (default 16; QMK uses 16)
- `circular-scroll-trigger-angle-deg` — minimum angle of tangentiality to commit (default 50; QMK uses 50)
- `circular-scroll-wheel-clicks` — scroll units per full revolution (default 18; QMK uses 18 ≈ one click every 20°)
- `circular-scroll-direction` — `clockwise-down` / `clockwise-up` (default clockwise-down, matches macOS)

### 6.4 Edge scroll

**Right-side vertical scroll**:
- **Initiation**: touch starts in the rightmost `edge-scroll-right-pct` of the active area
- **Algorithm**: on each sample, `dy = y - prev_y`. Accumulate into `scroll_accum`. When `abs(scroll_accum) >= edge-scroll-emit-pixels`, emit `INPUT_REL_WHEEL` and decrement accumulator.

**Top-side horizontal scroll**:
- Mirror of right-side but for X-axis motion in the topmost `edge-scroll-top-pct` of active area
- Emits `INPUT_REL_HWHEEL`

**Tunables** (defaults from libinput `[R5]`):
- `edge-scroll-right-enable`, `edge-scroll-top-enable` (booleans)
- `edge-scroll-right-pct` / `edge-scroll-top-pct` — activation band width (default 12)
- `edge-scroll-emit-pixels` — sensor units per scroll unit (default 130; libinput uses 3 mm ≈ 134 sensor units on Cirque GlidePoint Circle)
- `edge-scroll-lock-timeout-ms` — if finger rests motionless in edge zone for this long, stop emitting scroll until movement resumes (default 300 ms; matches libinput's `DEFAULT_SCROLL_LOCK_TIMEOUT`)

### 6.5 Inertial cursor (coast)

**Entry condition**: `MOVING` state ends (finger lifts), AND release velocity > `inertial-velocity-threshold`.

**Velocity estimation** at release time:
- Maintain an EWMA of `(dx, dy, dt)` triples updated each sample with `α = inertial-velocity-ewma-alpha` (default 0.4)
- At release, use the EWMA as the initial coast velocity

**Coast loop** (in delayed work, ticks every `inertial-tick-ms` default 16 ms ≈ 60fps):
1. Decay velocity: `v *= exp(-tick_ms / decay_time_constant_ms)`
2. If `|v| < min_step` AND remainders < 1, stop coasting → IDLE
3. Otherwise accumulate `v * tick_ms` into remainders
4. Emit `INPUT_REL_X / INPUT_REL_Y` for integer parts
5. Reschedule self

**Tunables**:
- `inertial-cursor-enable` (boolean)
- `inertial-velocity-threshold` — min velocity to trigger coast (default tuned during hardware test)
- `inertial-decay-time-constant-ms` — τ for exponential decay (default 250 ms — feel: "half velocity ~170 ms after release")
- `inertial-tick-ms` — coast emission rate (default 16 ms ≈ 60 fps)
- `inertial-min-velocity` — stop coasting below this (default 0.05 units/ms)

### 6.6 Per-axis acceleration curve

Smooth feel benefits from non-linear acceleration: slow motion = pixel-precise, fast motion = larger steps. Mapping `|d| -> scale`:

- `linear`: `scale = 1.0`
- `quadratic` (default): `scale = 1.0 + accel_strength * |d| / accel_threshold`
- `cubic`: `scale = 1.0 + accel_strength * (|d| / accel_threshold)^2`

**Tunables**:
- `acceleration-curve` (enum)
- `acceleration-threshold` — speed at which acceleration kicks in (default 4 units/sample)
- `acceleration-strength` — multiplier (default 1.5)

---

## 7. DT binding contract

`[DRAFT]` — full YAML to follow once we settle defaults below. Sketch:

```yaml
compatible: "zmk,input-processor-gesture-engine"

properties:
  # active-area mapping (defaults match Cirque defaults under upstream driver)
  active-range-x-min:       { type: int, default: 128 }
  active-range-x-max:       { type: int, default: 1920 }
  active-range-y-min:       { type: int, default: 64 }
  active-range-y-max:       { type: int, default: 1472 }

  # touch state detection
  use-z-for-touch:          { type: boolean }   # [RESEARCH] toggle pending Z verification
  touch-z-threshold:        { type: int, default: 30 }
  touch-end-timeout-ms:     { type: int, default: 30 }  # fallback if Z unreliable

  # tap + drag
  tap-enable:                  { type: boolean }
  tap-window-ms:               { type: int, default: 180 }
  tap-max-distance:            { type: int, default: 60 }
  tap-button:                  { type: int, default: 0 }  # MB1=0, MB2=1, MB3=2
  drag-enable:                 { type: boolean }  # default true via Kconfig
  drag-window-ms:              { type: int, default: 180 }
  drag-lock-mode:              { type: string, default: "sticky", enum: ["off", "sticky", "timeout"] }
  drag-lock-release-timeout-ms:{ type: int, default: 300 }

  # cursor motion
  cursor-scale-num:         { type: int, default: 1 }
  cursor-scale-den:         { type: int, default: 1 }
  cursor-deadband:          { type: int, default: 0 }
  acceleration-curve:       { type: string, default: "quadratic", enum: ["linear", "quadratic", "cubic"] }
  acceleration-threshold:   { type: int, default: 4 }
  acceleration-strength:    { type: int, default: 150 }  # /100 = 1.5x

  # circular scroll
  circular-scroll-enable:        { type: boolean }
  circular-scroll-rim-pct:       { type: int, default: 15 }
  circular-scroll-emit-degrees:  { type: int, default: 20 }
  circular-scroll-direction:     { type: string, default: "clockwise-down" }

  # edge scroll
  edge-scroll-right-enable: { type: boolean }
  edge-scroll-top-enable:   { type: boolean }
  edge-scroll-right-pct:    { type: int, default: 12 }
  edge-scroll-top-pct:      { type: int, default: 12 }
  edge-scroll-emit-pixels:  { type: int, default: 50 }

  # inertial cursor
  inertial-cursor-enable:               { type: boolean }
  inertial-velocity-threshold:          { type: int, default: 2 }
  inertial-velocity-ewma-alpha:         { type: int, default: 40 }  # /100 = 0.4
  inertial-decay-time-constant-ms:      { type: int, default: 250 }
  inertial-tick-ms:                     { type: int, default: 16 }
  inertial-min-velocity:                { type: int, default: 5 }   # /100 = 0.05 u/ms
```

---

## 8. Test & tuning plan

Hardware-in-the-loop iteration is the only way to dial in the defaults. Process:

1. **Build a debug variant** with extensive `LOG_DBG` instrumentation enabled. Output state transitions, decision triggers, velocity samples to USB CDC (we know how to do this safely now, post-`a4cd9e1` lesson — no `LOG_MODE_IMMEDIATE` for production-feel testing, only for hang diagnosis).

2. **Test each gesture in isolation** before composing. Order:
   - (a) Touch detection — verify state machine `IDLE ↔ MAYBE_TAP ↔ MOVING ↔ IDLE` transitions on raw touch
   - (b) Cursor motion alone — disable all other gestures, tune scale/deadband/acceleration
   - (c) Tap — verify thresholds, no accidental taps during fast cursor work
   - (d) Drag-lock — verify tap-tap-drag works, no false positives
   - (e) Inertial cursor — tune τ and threshold, target: "fling feels like the cursor has gentle momentum, not too clingy, not too sluggish"
   - (f) Circular scroll — tune rim percent and emit-degrees, target: "smooth scroll wherever I want it, no accidents during normal use"
   - (g) Edge scroll — tune band widths and emit-pixels
   - (h) All gestures composed — verify mutual-exclusion is intact, no surprising state transitions

3. **Articulate-feel feedback loop**: user describes feel in concrete terms ("inertia coasts too far", "circular scroll picks up on accidental edge-touches", "tap misfires when I scrub fast"), we map to specific tunable, iterate.

4. **Tunable sanity bounds**: every DT property has a "this is the minimum sensible value" and "this is the maximum sensible value" in a comment. Outside this range = footgun.

---

## 9. Open questions & research log

Items I need to resolve before writing code (or that user testing must answer):

### Pending research (I do this)

- **`[R1] ✅ RESOLVED.`** Z is a 6-bit (0-63) contact-strength indicator, not true pressure. The chip itself uses (x=y=z=0) as its idle/no-touch flag, confirming Z is reliable as a presence signal. P4 (Z-based touch detection) stays in the design. See §2 for details.
- **`[R2] ✅ RESOLVED.`** Input events dispatch on a dedicated input thread (Zephyr 4.1 default `CONFIG_INPUT_MODE_THREAD=y`). Delayed work fires on system work queue. Sync via `k_work_cancel_delayable_sync` on touch events; no long-term locks. Stack bump to 2048 minimum. See §4.3 for full analysis.
- **`[R3] ✅ RESOLVED.`** The split payload structure in [zmk/app/src/split/bluetooth/service.c](https://github.com/zmkfirmware/zmk/blob/main/app/src/split/bluetooth/service.c) is:
  ```c
  struct zmk_split_input_event_payload {
      .type, .code, .value, .sync
  };
  ```
  All four event fields preserved across BLE. **Timestamps are NOT carried**; the central re-stamps with `k_uptime_get()` on arrival. Position-based gestures (circular scroll, edge scroll, tap distance threshold) are unaffected. Inertia velocity is the only victim — BLE jitter (~5ms on a ~15ms Pinnacle sample interval) contaminates measured `dt`. **Design choice:** for inertia velocity estimation, use position deltas per sample with the configured Pinnacle sample rate as a constant assumption, not the measured `dt`. EWMA smoothing on top (P8) further reduces jitter sensitivity. For tap-window timing, central-side `k_uptime_get()` is correct anyway (user perceives tap duration at host).
- **`[R4] ✅ RESOLVED.`** The upstream driver emits exactly three events per sample with sync set only on the third:
  ```c
  input_report_abs(dev, INPUT_ABS_X, sample->abs_x, false /* not sync */, ...);
  input_report_abs(dev, INPUT_ABS_Y, sample->abs_y, false /* not sync */, ...);
  input_report_abs(dev, INPUT_ABS_Z, sample->abs_z, true  /* SYNC */,     ...);
  ```
  Our sample-builder design is correct: accumulate (x, y, z) and act on the sync flag. The atomic sample unit is exactly the (X, Y, Z) triple.
- **`[R5] ✅ RESOLVED.`** Mined libinput defaults from [`src/evdev-mt-touchpad-tap.c`](https://github.com/mix-mirror/libinput/blob/main/src/evdev-mt-touchpad-tap.c) and [`src/evdev-mt-touchpad-edge-scroll.c`](https://github.com/mix-mirror/libinput/blob/main/src/evdev-mt-touchpad-edge-scroll.c):
  - `DEFAULT_TAP_TIMEOUT_PERIOD = 180 ms` → adopted as `tap-window-ms` default
  - `DEFAULT_TAP_MOVE_THRESHOLD = 1.3 mm` → adopted as `tap-max-distance = 60` sensor units (on Cirque GlidePoint Circle ≈ 58 units)
  - `DEFAULT_DRAG_TIMEOUT_PERIOD_BASE = 160 ms` (+ 20 ms/finger) → adopted as `drag-lock-window-ms = 180`
  - `DEFAULT_DRAGLOCK_TIMEOUT_PERIOD = 300 ms` → adopted as `drag-lock-release-timeout-ms` for the timeout-release mode
  - `DEFAULT_SCROLL_THRESHOLD = 3 mm` → adopted as `edge-scroll-emit-pixels = 130`
  - `DEFAULT_SCROLL_LOCK_TIMEOUT = 300 ms` → adopted as `edge-scroll-lock-timeout-ms`
  
  These give us defensible starting points backed by 15 years of touchpad UX tuning; we'll iterate from here. Inertial scrolling (different math) and pointer acceleration curves left for hardware testing — libinput's accel is complex and our nonlinear quadratic default should be fine.
- **`[R6] ✅ RESOLVED.`** Yes — ZMK supports up to 2 param cells per processor invocation (`param1`, `param2` in [`zmk_input_processor_entry`](https://github.com/zmkfirmware/zmk/blob/main/app/include/drivers/input_processor.h)). Cells are declared via `#input-processor-cells = <N>` in the binding (halfdane uses 0 cells via `ip_zero_param.yaml`). **Design decision**: we use **zero cells** like halfdane did. Layer-conditional behavior comes from the input-listener's existing `layers = <RAISE>;` mechanism (which we already use for RAISE-as-scroll), not from per-invocation params. Simpler, and the use case for per-invocation params (running the same processor with different settings) doesn't apply here — we'd just register multiple processor instances if we needed variant behaviors.
- **`[R7] ✅ RESOLVED.`** QMK's [`drivers/sensors/cirque_pinnacle_gestures.{h,c}`](https://github.com/qmk/qmk_firmware/blob/master/drivers/sensors/cirque_pinnacle_gestures.c) is the goldmine — they've been doing absolute-mode Cirque gestures for years on physical keyboards. Key insights adopted:
  - Two-phase circular scroll with a `SCROLL_DETECTING` validation state (see §6.3 redesign).
  - Tangential-vs-radial angle validation prevents false-positive scrolls when user reaches toward center.
  - Default values: `outer_ring_pct = 33`, `trigger_px = 16`, `trigger_ang = 50°`, `wheel_clicks = 18`. We adopt all four as our defaults.
  - QMK has a separate `cursor_glide` system (= inertial cursor); their implementation lives in `pointing_device_drivers.c`. Worth a deeper look during the inertial-cursor implementation phase to compare against our exp-decay design — they likely use a simpler linear decay, but their thresholds for "fling magnitude" are useful prior art.

### Pending hardware verification (user does this once we have a build)

- **`[H1]` Z values observed during normal touch.** Log raw Z, finger range. If always 0 or near-noise, P4 falls back.
- **`[H2]` Effective sample rate.** Observed ms-between-samples. Determines real-world `delta_time` for velocity calc.
- **`[H3]` Subjective feel sweep** of each tunable. Done after each gesture lands. Defaults will move based on this.

### Design decisions (resolved)

- **`[D1] ✅ DECIDED: B`** — multi-processor architecture. The gesture engine is composed of cooperating processors (sample_builder → state_machine → individual gesture handlers as separate processor nodes), wired together in the input-listener chain. More LOC up front; pays back in composability — combined with D2=A, this is what enables per-layer gesture set swapping without monolithic mode flags. The file layout in §4.2 already reflects this — each gesture module is independently addressable.

- **`[D2] ✅ DECIDED: A`** — per-layer gesture sets. Different layers can have completely different processor chains in their input-listener block. Default layer gets the full engine; RAISE gets a scroll-only chain; future layers (precision mode, navigation mode) get their own profiles. The cost is more DT wiring per layer, but combined with D1=B that wiring is just composing existing processor nodes, not configuring monolithic internals.

- **`[D3] ✅ DECIDED: all three modes configurable; default = `sticky`** — mirrors libinput's model. Three release behaviors after a drag, controlled by `drag-lock-mode`:
  - `off` (Mode A from original D3 framing): finger lift → button released immediately. Best for short/simple drags.
  - `sticky` (Mode B, **default per user preference**): finger lift → button stays held; next finger-down resumes the drag; a single tap releases. Best for long/multi-segment drags (drawing curves, multi-stage selections, the user's workflow).
  - `timeout`: finger lift → button stays held for `drag-lock-release-timeout-ms` (default 300 ms, matches libinput); auto-releases if no new touch arrives.
  - All three implemented; user toggles via DT property. See §6.1 tunables.

- **`[D4] ✅ DECIDED: snappy (cancel on touch)`** — new touch during INERTIAL_COAST immediately cancels the coast (calls `k_work_cancel_delayable_sync` on the coast tick) and transitions to MAYBE_TAP for the new touch. Future option `inertial-on-touch = cancel | absorb` may be added if users want the continuous-feel alternative, but default behavior is locked as cancel.

---

**Next step:** I work through `[R1]` through `[R7]` and update this doc with findings. Then we discuss `[D1]` through `[D4]` and lock down decisions. Then code skeleton.
