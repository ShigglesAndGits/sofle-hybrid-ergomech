# Detailed Layer Documentation

This document provides in-depth information about each layer's key mappings and special functions.

## Base Layer (0)

The base layer follows a standard QWERTY layout with ergonomic optimizations:

```ascii
┌─────────┬─────┬─────┬─────┬─────┬─────┐                  ┌─────┬─────┬─────┬─────┬─────┬─────────┐
│   `     │  1  │  2  │  3  │  4  │  5  │                  │  6  │  7  │  8  │  9  │  0  │   -     │
├─────────┼─────┼─────┼─────┼─────┼─────┤                  ├─────┼─────┼─────┼─────┼─────┼─────────┤
│   ESC   │  Q  │  W  │  E  │  R  │  T  │                  │  Y  │  U  │  I  │  O  │  P  │ BKSPACE │
├─────────┼─────┼─────┼─────┼─────┼─────┤                  ├─────┼─────┼─────┼─────┼─────┼─────────┤
│   TAB   │  A  │  S  │  D  │  F  │  G  │                  │  H  │  J  │  K  │  L  │  ;  │    '    │
├─────────┼─────┼─────┼─────┼─────┼─────┤                  ├─────┼─────┼─────┼─────┼─────┼─────────┤
│  SHIFT  │  Z  │  X  │  C  │  V  │  B  │                  │  N  │  M  │  ,  │  .  │  /  │  SHIFT  │
└─────────┴─────┴─────┴─────┴─────┴─────┘                  └─────┴─────┴─────┴─────┴─────┴─────────┘
                      ┌─────┬─────┬─────┐                  ┌─────┬─────┬─────┐
                      │ GUI │ ALT │CTRL │                  │ NAV │WORK │ CTL │
                      └─────┴─────┴─────┘                  └─────┴─────┴─────┘
```


### Thumb Cluster

- Left: GUI, ALT, CTRL
- Right: NAV (tap dance), WORK (tap dance), CTRL
- Encoders: Volume control by default


## Navigation Layer (3)

Activated by double-tapping the NAV key. Focuses on text navigation and editing:

- Vim-style navigation:
  - H: Left
  - J: Down
  - K: Up
  - L: Right
- Text manipulation:
  - Word movement
  - Line start/end
  - Page up/down
- Selection tools when combined with shift

## Work Layer (4)

Activated by double-tapping the WORK key. Focused on window and workspace management:

- COSMIC window controls:
  - Float (Super + G)
  - Maximize (Super + M)
  - Fullscreen (Super + F)
  - Close (Super + Q)
- Workspace navigation
- Application switching
- Task management
- Numlock toggle (upper-right position)
  - Convenient access for occasional numpad use

## System Layer (5)

Automatically activated when holding both NAV and WORK:

- Power management
- System shortcuts:
  - Ctrl+Alt+Del
  - Ctrl+Alt+End
  - Ctrl+Alt+Pause
- Task manager access
- System monitoring tools

## Resize Layer (6)

Dedicated to window management:

- Window movement (arrows)
- Window snapping
- Size adjustment
- Position control
- Encoder functions:
  - Left encoder: Horizontal resize
  - Right encoder: Vertical resize

## Resize Shift Layer (7)

Advanced window management features activated by combining RESIZE and LOWER:

- Fine-grained window control
- Advanced snapping options
- Multi-monitor management
- Workspace organization

## Special Features

### Tap Dance Behaviors
- NAV key:
  - Single tap: LOWER layer
  - Double tap: Navigation layer
- WORK key:
  - Single tap: RAISE layer
  - Double tap: Work layer

### Conditional Layers

1. System Layer Activation:
   - Triggered by: NAV + WORK
   - Provides quick access to system controls

2. Resize Shift Activation:
   - Triggered by: RESIZE + LOWER
   - Enables advanced window management

