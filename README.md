# Sofle Hybrid Ergomech ZMK Configuration

This repository contains my custom ZMK configuration for the Sofle Hybrid keyboard, featuring an ergonomic layout with multiple layers optimized for programming, system management, and window control.

## Layout Overview

The keyboard uses 8 distinct layers:


1. **BASE (0)** - Standard QWERTY layout with optimized thumb cluster
2. **LOWER (1)** - Numbers, symbols, and basic functions
3. **RAISE (2)** - Additional symbols and media controls
4. **NAV (3)** - Navigation and text editing
5. **WORK (4)** - Workspace and application management
6. **SYSTEM (5)** - System controls (activated by NAV + WORK)
7. **RESIZE_LAYER (6)** - Window resizing controls
8. **RESIZE_SHIFT (7)** - Additional window management (activated by RESIZE + LOWER)

## Special Features

### Display Features


- OLED display on left shield only (right shield display disabled)
- WPM (Words Per Minute) counter
- Layer status indicator
- Battery status with percentage
- Output status indicator
- 10-second display timeout when idle
- 1-second refresh rate

### Tap Dance Layers

- `td_layer_nav`: Single tap for LOWER, double tap for NAV
- `td_layer_work`: Single tap for RAISE, double tap for WORK

### Window Management

- COSMIC window management macros for floating, maximizing, and fullscreen
- Dedicated resize layer with directional controls
- Window movement and snapping capabilities

### System Controls

- Media playback controls
- Volume control via encoder
- System management shortcuts (Ctrl+Alt+Del, etc.)
- Quick screenshot capability (Super+Shift+S)
- Terminal launcher (Super+T)

### Conditional Layers

- SYSTEM layer activates automatically when NAV and WORK are held together
- RESIZE_SHIFT activates when RESIZE_LAYER and LOWER are combined

### Encoder Configuration
- Default: Volume control
- NAV layer: Workspace switching (Super+Tab / Super+Shift+Tab)
- WORK layer: Application switching (Alt+Tab / Alt+Shift+Tab)
- Resize layer: Window size adjustment

## Layer Details

### Base Layer

- Standard QWERTY layout
- Optimized thumb cluster with Space, Enter, and layer access
- Shift keys on both sides
- GUI, Alt, and Ctrl modifiers readily accessible

### Navigation Layer (NAV)

- Arrow keys in vim-style HJKL configuration
- Page Up, Page Down, Home, and End
- Text selection and manipulation
- Encoder for workspace switching

### Work Layer (WORK)

- Window and workspace management
- Application switching via encoder
- Task management shortcuts
- Numlock key in upper-right position

### System Layer

- Activated by combining NAV + WORK
- System controls and power management
- Special function keys

## Contributing

This is a personal configuration that's constantly evolving. Feel free to use it as inspiration for your own layout!

## License

This configuration is released under the MIT License. See the included license file for details.
