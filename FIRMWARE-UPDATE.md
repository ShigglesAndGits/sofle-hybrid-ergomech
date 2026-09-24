# September 2026 stability update

## Changes and evidence

- **ZMK:** `9ebbeff0a8b69a42f14aec022cdf16c7a107b9e0`, current main at investigation time.
- **Zephyr:** `10ba6d0cb38bc3d258775d27982f707599320085`, current `v4.1.0+zmk-fixes`.
  This is ZMK's supported base, not an upgrade to standalone Zephyr 4.3+.
  Compared with the August 1 build (`9df4b12b5af3`), it adds fixes for controller
  prepare-pipeline overflow and peripheral assertions during connection updates
  with simultaneous flash operations.
- **nice-view-gem:** `0a50fe209d929c916c5664c6affd0f4977c6b012`, explicitly pinned.
- **Split pointing transport:** local adaptation of
  [ZMK PR #3110](https://github.com/zmkfirmware/zmk/pull/3110), upstream head
  `c25d74b507c1b59d49f1fc7adfb2b44e50645db5`, by tomori-k. Notifications move
  out of the input callback to the existing peripheral notification workqueue.
  This changes the transport used by the Cirque trackpad, not its hardware driver.
  The PR is unmerged; our adaptation fixes its successful-overflow-retry path
  falling through to `-ENODEV` without resubmitting work. Queue size is 32.
- Removed ineffective `CONFIG_BT_SMP_SC_PAIR_ONLY=n`. ZMK forcibly selects `y`;
  August CI already compiled with `y`. This does not change effective security.
- The build now explicitly applies the patch, runs the host regression test,
  verifies pins and selected Kconfig values, and retains diagnostic artifacts.

[ZMK issue #3480](https://github.com/zmkfirmware/zmk/issues/3480) reports a close
hardware/symptom match: Sofle, two nRF52840 boards, intermittent central freezes
requiring power cycling. The reporter confirmed the maintainer's controller fix
with 4 faults/67 h on control versus 0/60.5 h and 0/63.1 h on fixed variants.
We have not captured that assertion on this physical keyboard, so it remains
a strong candidate, not a proven diagnosis. Increasing ACL TX buffers is not
equivalent to fixing this separate controller scheduling pipeline.

## Build and patch maintenance

Use GitHub Actions, or inside the pinned build container run:

```sh
python3 scripts/build.py sofle-left
python3 scripts/build.py sofle-right
python3 scripts/build.py settings-reset
```

Each command creates a fresh temporary west workspace and writes a new
`build-output/<target>/` directory. It intentionally refuses an existing output
directory to avoid mixing artifacts. The patch must apply cleanly; a future
ZMK bump that conflicts will fail rather than silently omit it. Root-manifest
Zephyr override is imported after ZMK so ZMK's LVGL/hal_stm32 overrides survive.

`tests/test_split_input_queue.py <patched-zmk-path>` compiles the actual patched
C section against host queue/workqueue/notification doubles. It tests deferred
sending, full-queue replacement and return status, failed retry, unknown input
device, and recovery after notification errors. The overflow test fails against
unmodified PR #3110 and passes with this adaptation. It is not a radio/concurrency
simulation or evidence of long-term hardware stability.

Patch provenance lives in `patches/0001-split-input-notification-queue.patch`.
When upstream merges a suitable fix, replace this adaptation with that ZMK
revision and remove the local patch and obsolete test plumbing together.

## Settings reset and flashing

Settings reset erases host bonds, split-half pairing, and other persistent ZMK
settings. It is separate from the code update and does not itself prove the cause
of the new profile issue.

1. Download the complete successful `firmware` artifact. Keep left, right, and
   reset images from the **same run**.
2. Remove the Sofle pairing from each host that will be paired again, including
   the host using the formerly retained working slot.
3. Connect one half over USB and double-tap its reset button to enter the UF2
   bootloader. Copy `settings-reset.uf2` to its bootloader drive. Let it boot and
   run for several seconds (at least five) before entering the bootloader again.
4. Flash `sofle-left.uf2` to the **left** half or `sofle-right.uf2` to the
   **right** half as appropriate. Repeat reset + correct firmware on the other
   half. The same nice!nano reset image is used on both halves.
5. Power both halves fully off (USB disconnected and battery switches off), then
   turn both on near each other to establish their split connection. Confirm
   keys on both halves work, initially over USB if useful.
6. Select an empty Bluetooth profile and pair one host. Use a distinct slot for
   each distinct host; avoid trying to give the same host multiple slots.
7. Profile selection saves after a 60-second debounce in this configuration.
   Wait over a minute after selecting the desired startup slot before testing
   power-cycle persistence.

Do not leave the settings-reset image installed as normal firmware.

## Verification and rollback

- Confirm both halves, trackpad motion, scrolling, and Bluetooth pairing.
- Exercise normal work/personal host switching and sustained trackpad use.
- A successful build or a brief test does not demonstrate the intermittent
  freeze is fixed. Track hours/days of normal use and any recurrence.
- Left-half USB logging remains **deferred**, as in the August build. No
  immediate logging was introduced. Routine debug logs include keystrokes;
  filter diagnostic captures before retaining/sharing them.
- If a freeze recurs, record whether left/right keys, trackpad, display, and USB
  still respond. Keep the matching `zmk.elf`, `resolved.config`, and
  `west-frozen.yml`; these identify the exact binary and symbolize faults.
- The rollback baseline is Actions run
  [30704395526](https://github.com/ShigglesAndGits/sofle-hybrid-ergomech/actions/runs/30704395526),
  config commit `dbcd05d430975f2eacbe948b5f04101f18efaf96`. Use its original
  downloaded UF2s rather than rebuilding that commit: it had floating Zephyr
  and display dependencies. Resetting settings cannot restore erased bonds;
  rollback may still require re-pairing.
