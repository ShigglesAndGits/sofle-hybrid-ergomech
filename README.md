# Sofle Ergomech ZMK Configuration

This document outlines the features and layout of the ZMK firmware configuration for the Sofle Ergomech keyboard.

## Overview

This configuration features multiple layers, custom behaviors like tap-dance and hold-tap, macros for common tasks and window management (primarily targeting COSMIC DE), and layer-dependent encoder functions.

## Layers

The keymap utilizes several layers accessible through momentary (`mo`), tap-dance (`td`), and conditional activation.

*   **BASE (Layer 0): Default**
    *   Standard QWERTY layout.
    *   Left Thumb: Tap-Dance for `NAV` (tap) / `LOWER` (hold).
    *   Right Thumb: Tap-Dance for `WORK` (tap) / `RAISE` (hold).
    *   Left Thumb Cluster: `LALT`, `LGUI`, `LCTRL` (Tap for Ctrl, Double-Tap for Resize Mode), `SPACE`.
    *   Right Thumb Cluster: `ENTER`, `RCTRL`, `RGUI`, `RALT`.
    *   Rightmost Column (Pinky): `MINUS`, `BACKSPACE`, `SQT`, `RSHIFT`. Arrow keys on right thumb cluster bottom row.

*   **LOWER (Layer 1): Symbols & Numbers**
    *   Accessed by **holding** the left thumb key.
    *   Contains F-keys (F1-F12), number pad layout on the right side, common symbols (`!@#$%^&*()`, `[]{}`, `|`, `+`, `=`, `/`, `*`, `.`), mouse keys (`mkp`), and Bluetooth profile selection (`BT_SEL 0-4`).
    *   Includes `Ctrl+Alt+Del` macro.

*   **RAISE (Layer 2): F-Keys & Media**
    *   Accessed by **holding** the right thumb key.
    *   Contains F-keys (F1-F12) mirrored on both halves.
    *   Includes media control keys (`C_PLAY_PAUSE`, `C_NEXT`, `C_PREVIOUS`, `C_STOP`).

*   **NAV (Layer 3): Navigation & COSMIC WM**
    *   Accessed by **tapping** the left thumb key.
    *   Focuses on window and workspace navigation, primarily using COSMIC DE shortcuts:
        *   Window Actions: Close (`cs_close`: Super+Q), Resize Mode (`cs_resize`: Super+R), Float (`cs_float`: Super+G), Maximize (`cs_max`: Super+M), Workspace View (`cs_wk`: Super+W).
        *   Window Movement: Move Left/Right/Up/Down (`mv_l/r/u/d`: Super+Shift+Arrow).
        *   Window Navigation: Focus Left/Right/Up/Down (`nav_l/r/u/d`: Super+Arrow).
    *   Includes `Ctrl+Alt+Del` macro.

*   **WORK (Layer 4): IT & Macros**
    *   Accessed by **tapping** the right thumb key.
    *   Contains IT-related macros: `Ctrl+Alt+Pause`, `Ctrl+Alt+End`, `Ctrl+Alt+Del`.
    *   (Future: Intended for text snippets and other work-related macros).

*   **SYSTEM (Layer 5): System & Bluetooth**
    *   **Conditional Layer:** Activated when **both** `NAV` (Layer 3) and `WORK` (Layer 4) are active (i.e., tapping both thumb keys).
    *   Contains F-keys (F1-F12), Bluetooth controls (`BT_CLR`, `BT_SEL 0-4`), and system keys (`DEL`, `END`, `PAUSE_BREAK`, `ESC`).

*   **RESIZE (Layer 6): Window Resizing**
    *   Accessed via the `cs_resize` macro (Super+R on `NAV` layer) or double-tapping `LCTRL` on the `BASE` layer.
    *   Dedicated to window resizing using encoders.

*   **RESIZE_SHIFT (Layer 7): Window Resizing (Vertical)**
    *   **Conditional Layer:** Activated when **both** `RESIZE` (Layer 6) and `LOWER` (Layer 1) are active (i.e., holding the left thumb key while in Resize mode).
    *   Dedicated to vertical window resizing using encoders.

## Encoder Functions

The rotary encoders have different functions depending on the active layer:

*   **BASE:** Scroll Up / Down
*   **LOWER:** Mouse Scroll Up / Down
*   **RAISE:** Switch Workspace (Super+Tab / Super+Shift+Tab)
*   **NAV:** Switch Application (Alt+Tab / Alt+Shift+Tab)
*   **WORK:** Volume Up / Down
*   **SYSTEM:** Volume Up / Down
*   **RESIZE:** Horizontal Resize (via Left/Right Arrow Keys)
*   **RESIZE_SHIFT:** Vertical Resize (via Up/Down Arrow Keys)

## Special Features

*   **Tap-Dance:**
    *   Left Thumb: Tap for `NAV`, Hold for `LOWER`.
    *   Right Thumb: Tap for `WORK`, Hold for `RAISE`.
    *   Left Ctrl: Tap for `LCTRL`, Double-Tap to activate `RESIZE` layer.
*   **Conditional Layers:**
    *   `SYSTEM` layer activates when `NAV` and `WORK` are held simultaneously.
    *   `RESIZE_SHIFT` layer activates when `RESIZE` and `LOWER` are held simultaneously.
*   **Macros:**
    *   Screenshot: `meta_shift_s` (Super+Shift+S)
    *   Launch Terminal: `launch_terminal` (Super+T)
    *   Windows Task Manager: `wn_task` (Ctrl+Shift+Esc)
    *   COSMIC Window Management: See `NAV` layer description.
    *   IT Tools: `services_msc`, `ctrlAltDel`, `ctrlAltPause`, `ctrlAltEnd`.
    *   Text Snippets: `good_morning`, `good_afternoon`, `thank_you`, `closing_case`, `following_up` (available on various layers, check keymap for specifics - currently not assigned to easily accessible keys).
*   **Cirque Trackpad:**
    *   A Cirque Pinnacle trackpad is implemented on the right keyboard half.
    *   It communicates via I2C (address `0x2a`) with the right microcontroller.
    *   Trackpad input data is sent over the split connection to the left (central) half for processing.
    *   Configuration (in `sofle_ergomech_right.overlay`): X-axis is inverted, sensitivity is set to `1x`.