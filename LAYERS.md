# Layer Reference

Authoritative source: `config/sofle_ergomech.keymap` (each layer has an ASCII
diagram comment kept in sync with its bindings). Visual reference:
[keymap.svg](keymap.svg), regenerated with keymap-drawer (see README).

## 0 — BASE

Standard QWERTY. Number row on top, `Grave`/`Minus` on the corners, shifts on
both bottom corners.

Thumb cluster (left→right across both halves): outer tap-dance ALT (double
tap = play/pause, 100ms term), `GUI`, `Ctrl`, `Space`, `&mo LOWER` (plain
momentary — instant), then RAISE/WORK tap dance, `Enter`, `Del`, `Alt+Tab`
(tap = quick-switch between the two most recent windows; press-and-hold =
the switcher stays open and key repeat cycles it forward), and sticky
`Ctrl+Alt` (`&sk LC(LALT)`) on the outer edge: tap it, release, and both
mods apply to the next keypress (1s timeout). `Ctrl+Alt+Del` is therefore
two adjacent-cluster thumb taps with no holding.

Encoder: smooth scroll (`&msc MOVE_UP/DOWN`, magnitude set by
`ZMK_POINTING_DEFAULT_MOVE_VAL` in the keymap header).

## 1 — LOWER (hold left inner thumb — instant)

- Top row: `F1`–`F12`.
- Right hand: numpad layout (`7 8 9` / `4 5 6` / `1 2 3`, bottom `0 / . *`)
  with `( ) [ ] { }` on the two outer columns and `| =` on the edge.
  Numpad `+` lives on RAISE's top-right corner; the inner right thumb is
  transparent here so LOWER + that thumb reaches SYSTEM via the tri-layer.
- Left hand: mouse buttons — `MB2 MB3 MB1` on the home row, `MB4`/`MB5` above,
  copy (`Ctrl+C`) and plain paste (`Ctrl+Shift+V`) on the inner column,
  `Backspace`/`Insert` on the outer column.
- Bottom row left: `&bt BT_SEL 0-4` (BLE profile select).

Encoder: arrow `Down`/`Up` steps.

## 2 — RAISE (hold right inner thumb)

- Right hand: `Home PgDn PgUp End` row above vim-style arrows
  (`← ↓ ↑ →`), `Del`, `Backspace`, `\`, `+` on the corner.
- Trackpad: converted to a scroller while held
  (`zip_xy_scaler 1 4` + `zip_xy_to_scroll_mapper`), cursor movement off.

Encoder: window minimize/maximize (`GUI+Down` / `GUI+Up`).

## 3 — WORK (double tap-hold right inner thumb)

- `Ctrl+Alt+Break`, `Ctrl+Alt+End`, `Ctrl+Alt+Del` on the right home row
  (RDP session control — daily use)
- `NumLock` above them

Encoder: volume down/up.

## 4 — SYSTEM (hold LOWER + RAISE simultaneously)

Conditional tri-layer (`if-layers = <LOWER RAISE>`).

- Top row: `F1`–`F12`
- `&bt BT_CLR` (clears the *active profile's* bond — use with intent)
- `&bt BT_SEL 0-4` on the left home row
- `Del End Pause Esc` cluster on the right

Encoder: volume down/up.
