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

Firmware builds run on GitHub Actions (`build.yaml`); ZMK is pinned to a fixed
revision in `config/west.yml` (Zephyr 4.1 era). Flash the matching
`sofle_ergomech_left`/`sofle_ergomech_right` UF2 from the workflow artifacts,
plus `settings_reset` when bonds need clearing.

## Layers

See [keymap.svg](keymap.svg) for the full picture and [LAYERS.md](LAYERS.md)
for details.

| # | Layer | Access | Encoder |
|---|-------|--------|---------|
| 0 | BASE | default | smooth scroll |
| 1 | LOWER | hold left inner thumb (single tap-hold) | arrow down/up |
| 2 | RAISE | hold right inner thumb (single tap-hold) | window minimize/maximize (GUI+Down/Up) |
| 3 | NAV | double tap-hold left inner thumb | scroll (stepped) |
| 4 | WORK | double tap-hold right inner thumb | volume |
| 5 | SYSTEM | hold NAV + WORK together (conditional layer) | volume |

Layer highlights:

- **BASE** — QWERTY; both outer thumb keys are a tap dance: single tap ALT,
  double tap play/pause.
- **LOWER** — F-row, right-hand numpad with brackets, mouse buttons on the
  left home row (MB1/MB2/MB3 plus MB4/MB5), BLE profile select on the bottom
  row, copy (`Ctrl+C`) and plain paste (`Ctrl+Shift+V`).
- **RAISE** — navigation cluster (`Home/PgDn/PgUp/End`) above vim-style
  arrows on the right hand, `Del`/`Backspace`; the trackpad switches from
  cursor movement to scrolling while this layer is held.
- **NAV** — COSMIC window management: `Super+arrows` to focus, close
  (`Super+Q`), float (`Super+G`), maximize (`Super+M`), workspaces
  (`Super+W`), and `Ctrl+Alt+Del`.
- **WORK** — `Ctrl+Alt+Break/End/Del` chords (remote session control) and
  NumLock.
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
