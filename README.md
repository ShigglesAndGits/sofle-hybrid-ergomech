# Sofle Hybrid Ergomech ZMK Configuration with Cirque Trackpad

This repository contains a custom ZMK firmware configuration for the Sofle Hybrid keyboard by Ergomech Store, featuring an integrated Cirque Pinnacle trackpad on the right half and a multi-layer keymap optimized for system navigation.

## Key Features

*   **Integrated Trackpad:** Cirque Pinnacle GlidePoint trackpad on the right keyboard half via I2C.
*   **Custom Keymap:** Multi-layer layout (8 layers) leveraging tap-dance and conditional layers for efficient access.
*   **Extensive Macros:** Predefined macros for COSMIC DE window management, Windows 11 window management, system shortcuts, and text snippets.
*   **Left Rotary Encoder:** Configured for volume control, workspace/app switching, and window resizing depending on the active layer.
*   **OLED Display:** Shows WPM, active layer, battery status (%), and output connection status.

## Trackpad Integration Details

This configuration integrates a Cirque Pinnacle trackpad using Pete Johanson's external ZMK module.

*   **Hardware:** Cirque Pinnacle GlidePoint Trackpad TM040040
*   **Connection:** I2C on the **right** keyboard half.
*   **Driver Module:** [petejohanson/cirque-input-module](https://github.com/petejohanson/cirque-input-module)

### Pinout (nice!nano v2 Controller)

*   **SDA:** P0.29 (nice!nano pin D2) -> Trackpad SDA
*   **SCL:** P0.31 (nice!nano pin D3) -> Trackpad SCL
*   **DR (Data Ready/Interrupt):** P0.08 (nice!nano pin D0) -> Trackpad DR
*   **VCC:** nice!nano VCC (3.3V) -> Trackpad VCC
*   **GND:** nice!nano GND -> Trackpad GND

## Keymap Layers Overview

This configuration utilizes 8 layers:

1.  **BASE (0):** Standard QWERTY layout with thumb cluster access to layers and modifiers.
2.  **LOWER (1):** Accessed via tap/hold on left thumb. Contains numbers (numpad-style on right), symbols, F-keys, and Bluetooth controls.
3.  **RAISE (2):** Accessed via tap/hold on right thumb. Contains F-keys, media controls, and additional symbols.
4.  **NAV (3):** Accessed via double-tap on left thumb. Contains navigation keys (arrows via macros), window management macros (COSMIC), and mouse button bindings (currently W=&kp MB3, E=&kp MB2, R=&kp MB1). *Note: The current pushed version has these reverted to &trans.*
5.  **WORK (4):** Accessed via double-tap on right thumb. Contains system management shortcuts (Ctrl+Alt+...), Numlock toggle.
6.  **SYSTEM (5):** Activated automatically when NAV (3) and WORK (4) are held simultaneously. Contains Bluetooth management and system function keys (F1-F12).
7.  **RESIZE_LAYER (6):** Accessed via `&mo 6` (currently mapped to `td_ctrl_resize` tap-dance on LCTRL). Used for window resizing via encoder.
8.  **RESIZE_SHIFT (7):** Activated automatically when RESIZE\_LAYER (6) and LOWER (1) are held simultaneously. Used for alternate window resizing via encoder.

### Tap Dance

*   **Left Thumb:** Tap for LOWER (1), Double-Tap for NAV (3) (`&td_layer_nav`)
*   **Right Thumb:** Tap for RAISE (2), Double-Tap for WORK (4) (`&td_layer_work`)
*   **Left Ctrl:** Tap for LCTRL, Hold for RESIZE\_LAYER (6) (`&td_ctrl_resize`)

### Encoder Actions

*   **BASE:** Mouse Wheel Down/Up
*   **LOWER:** Arrow Down/Up
*   **RAISE:** Arrow Left/Right
*   **NAV:** Volume Down/Up
*   **WORK:** Volume Down/Up
*   **SYSTEM:** Volume Down/Up
*   **RESIZE:** Resize Horizontal (Left/Right)
*   **RESIZE_SHIFT:** Resize Vertical (Down/Up)

## License

This configuration is released under the MIT License.
