# Sofle Hybrid Ergomech ZMK Configuration

Custom ZMK firmware for a [Sofle Hybrid](https://ergomech.store/) split keyboard:
wireless, trackpad-equipped, and tuned for COSMIC desktop window management.

## Hardware

| | Left half | Right half |
|---|---|---|
| Controller | nice!nano v2 | nice!nano v2 |
| Split role | Central (talks to hosts) | Peripheral (talks to left half) |
| Display | nice!view with [nice-view-gem](https://github.com/M165437/nice-view-gem) custom screen | none |
| Pointing | — | Cirque Pinnacle trackpad (I2C, tap-to-click) |
| Encoder | EC11 | EC11 |
| Power | 18650 cell | 18650 cell |

Firmware builds run on GitHub Actions (`build.yaml`). ZMK, Zephyr's supported
4.1 fixes branch, and nice-view-gem are pinned to exact revisions in
`config/west.yml`; the build image is pinned by digest. `scripts/build.py`
applies the reviewed split-input patch and verifies the resolved dependencies.
The `firmware` artifact contains `sofle-left/sofle-left.uf2`,
`sofle-right/sofle-right.uf2`, and `settings-reset/settings-reset.uf2`, plus
resolved configs, manifests, checksums, and ELF symbols for diagnostics.

See [FIRMWARE-UPDATE.md](FIRMWARE-UPDATE.md) for the September 2026 fixes,
their limitations, reset/flash sequence, and rollback baseline.

## Layers

See [keymap.svg](keymap.svg) for the full picture and [LAYERS.md](LAYERS.md)
for details.

| # | Layer | Access | Encoder |
|---|-------|--------|---------|
| 0 | BASE | default | smooth scroll |
| 1 | LOWER | hold left inner thumb (plain momentary, instant) | arrow down/up |
| 2 | RAISE | hold right inner thumb (single tap-hold) | window minimize/maximize (GUI+Down/Up) |
| 3 | WORK | double tap-hold right inner thumb | volume |
| 4 | SYSTEM | hold LOWER + RAISE together (tri-layer) | volume |

Layer highlights:

- **BASE** — QWERTY. Left outer thumb is a tap dance (tap ALT, double-tap
  play/pause, 100ms term). Right thumb cluster outward from Enter: `Del`,
  **Alt+Tab** (tap = quick-switch, hold = cycle via key repeat), and a
  **sticky Ctrl+Alt** on the edge — tap it, then tap a target key and both
  mods apply, no simultaneous holding (`Ctrl+Alt+Del` = two thumb taps).
- **LOWER** — F-row, right-hand numpad with brackets, mouse buttons on the
  left home row (MB1/MB2/MB3 plus MB4/MB5), BLE profile select on the bottom
  row, copy (`Ctrl+C`) and plain paste (`Ctrl+Shift+V`).
- **RAISE** — navigation cluster (`Home/PgDn/PgUp/End`) above vim-style
  arrows on the right hand, `Del`/`Backspace`; the trackpad switches from
  cursor movement to scrolling while this layer is held.
- **WORK** — `Ctrl+Alt+Break/End/Del` chords (daily RDP driver) and NumLock.
- **SYSTEM** — F-row, `&bt BT_CLR`, BLE profile select, misc system keys.

## Bluetooth

Five BLE profiles; select with `&bt BT_SEL 0-4` on LOWER or SYSTEM, clear the
active profile's bond with `&bt BT_CLR` on SYSTEM. Windows-compat decisions
(static address instead of RPA, legacy-pairing fallback, 1M PHY) are documented
inline in `config/sofle_ergomech.conf`; split-link tuning notes live in the
per-half `.conf` files under `boards/shields/sofle_ergomech/`.

## Regenerating the keymap diagram

```sh
pipx install keymap-drawer
keymap -c keymap_drawer.config.yaml parse -z config/sofle_ergomech.keymap -o sofle_ergomech.yaml
keymap -c keymap_drawer.config.yaml draw sofle_ergomech.yaml -j config/info.json -o keymap.svg
```

## License

MIT.
