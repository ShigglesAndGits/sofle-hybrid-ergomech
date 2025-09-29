# Planned Keyboard Configuration Changes

This document outlines the planned changes to the Sofle Hybrid Ergomech keyboard configuration.

## Analysis of Current Configuration

Your Sofle Hybrid Ergomech keyboard is a sophisticated ZMK configuration with:

### **Current Layer Structure:**
- **BASE (0)**: Standard QWERTY with optimized thumb cluster
- **LOWER (1)**: Numbers, symbols, mouse controls, navigation (PG_UP/PG_DN/HOME/END on right thumb cluster)
- **RAISE (2)**: Function keys, media controls (C_PLAY_PAUSE, C_NEXT, etc. on right thumb cluster)  
- **NAV (3)**: Window management with COSMIC macros
- **WORK (4)**: System management and shortcuts
- **SYSTEM (5)**: Activated by NAV+WORK combination
- **RESIZE (6-7)**: Window resizing functionality
- **GAMING (8)**: Gaming-optimized layout
- **ENCODER_DIR (10)**: Mouse and scroll controls

### **Current Encoder Configuration:**
- **BASE layer**: `<&inc_dec_kp DOWN UP>` (Arrow navigation)
- **LOWER layer**: `<&encoder_scroll_alt>` (Scroll using MOVE_UP/MOVE_DOWN)
- **RAISE layer**: `<&win_vertical_encoder>` (Window minimize/maximize)

### **Current Trackpad Scrolling:**
- On RAISE layer: Converts trackpad movement to scrolling via `zip_xy_to_scroll_mapper`
- No scrolling inversion mentioned in current config

### **Current Media Controls:**
- Located on RAISE layer right thumb cluster: C_PLAY_PAUSE, C_NEXT, C_PP, C_PREVIOUS, C_STOP

### **Current Alt Keys:**
- LALT on position in BASE layer thumb cluster
- RALT on right side of BASE layer

---

## PLAN for Requested Changes

### **1. Double Tap Alt to Pause/Play Media**
**Implementation:** Create a tap dance behavior for ALT keys that triggers media play/pause on double tap.

**Changes needed:**
- Add new tap dance behavior `td_alt_media` 
- Replace `&kp LALT` and `&kp RALT` in BASE layer with `&td_alt_media`
- Behavior: Single tap = ALT, Double tap = C_PLAY_PAUSE

### **2. Fix Trackpad Scrolling Inversion**
**Current Issue:** Left/right trackpad movement needs inversion for scrolling
**Implementation:** Modify the `zip_xy_to_scroll_mapper` processor chain to invert X-axis movement

**Changes needed:**
- Add X-axis inversion processor to the trackpad input chain
- Keep Y-axis scrolling as-is
- Apply only to scrolling behavior, not cursor movement

### **3. Swap Encoder Behaviors Between BASE and LOWER Layers**
**Current:**
- BASE: Arrow navigation (`DOWN UP`)
- LOWER: Scroll behavior (`encoder_scroll_alt`)

**Target:**
- BASE: Scroll behavior (move from LOWER)
- LOWER: Arrow navigation with inverted direction (`UP DOWN` instead of `DOWN UP`)

**Changes needed:**
- BASE layer: Change from `<&inc_dec_kp DOWN UP>` to `<&encoder_scroll_alt>`
- LOWER layer: Change from `<&encoder_scroll_alt>` to `<&inc_dec_kp UP DOWN>`

### **4. Add PG_UP/PG_DN/HOME/END to Both RAISE and LOWER Layers**
**Current:**
- LOWER layer right thumb cluster: `&kp END  &kp PG_UP  &kp HOME  &kp PAGE_DOWN`
- RAISE layer right thumb cluster: Media controls

**Target:**
- RAISE layer: Replace media controls with navigation keys (same as LOWER)
- LOWER layer: Keep existing navigation keys
- Both layers will have: `&kp END  &kp PG_UP  &kp HOME  &kp PAGE_DOWN`

**Changes needed:**
- RAISE layer thumb cluster: Replace `&kp C_PLAY_PAUSE  &kp C_NEXT  &kp C_PP  &kp C_PREVIOUS  &kp C_STOP` with `&kp END  &kp PG_UP  &kp HOME  &kp PAGE_DOWN`
- LOWER layer: No changes needed (already has the navigation keys)

### **5. Update Documentation**
**Files to update:**
- `README.md`: Update layer descriptions and feature lists
- `LAYERS.md`: Update detailed layer documentation with new key mappings
- Reflect new encoder behaviors, ALT tap dance, and navigation key availability

**Changes needed:**
- Update encoder behavior descriptions
- Document new ALT double-tap functionality
- Update layer key mapping diagrams
- Reflect navigation keys now available on both LOWER and RAISE layers
