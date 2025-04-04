# Sofle Hybrid Ergomech ZMK Configuration with Cirque Trackpad

This repository contains a custom ZMK firmware configuration for the Sofle Hybrid keyboard by Ergomech Store, featuring an integrated Cirque Pinnacle trackpad on the right half and a multi-layer keymap optimized for programming and system management.

## Key Features

*   **Integrated Trackpad:** Cirque Pinnacle GlidePoint trackpad on the right keyboard half via I2C.
*   **Custom Keymap:** Multi-layer layout (8 layers) leveraging tap-dance and conditional layers for efficient access.
*   **Extensive Macros:** Predefined macros for COSMIC window management, system shortcuts, and text snippets.
*   **Rotary Encoders:** Configured for volume control, workspace/app switching, and window resizing depending on the active layer.
*   **OLED Display:** Shows WPM, active layer, battery status (%), and output connection status.

## Trackpad Integration Details

This configuration integrates a Cirque Pinnacle trackpad using Pete Johanson's external ZMK module.

*   **Hardware:** Cirque Pinnacle GlidePoint Trackpad (e.g., TM040040)
*   **Connection:** I2C on the **right** keyboard half.
*   **Driver Module:** [petejohanson/cirque-input-module](https://github.com/petejohanson/cirque-input-module)

### Pinout (nice!nano v2 Controller)

*   **SDA:** P0.29 (nice!nano pin D2) -> Trackpad SDA
*   **SCL:** P0.31 (nice!nano pin D3) -> Trackpad SCL
*   **DR (Data Ready/Interrupt):** P0.08 (nice!nano pin D0) -> Trackpad DR
*   **VCC:** nice!nano VCC (3.3V) -> Trackpad VCC
*   **GND:** nice!nano GND -> Trackpad GND

### Firmware Configuration Steps

To replicate this trackpad setup in your ZMK configuration:

1.  **Add the West Module:** Add the `cirque-input-module` to your `config/west.yml`:
    ```yaml
    manifest:
      remotes:
        # ... other remotes
        - name: petejohanson
          url-base: https://github.com/petejohanson
      projects:
        # ... other projects (like zmk)
        - name: cirque-input-module
          url: https://github.com/petejohanson/cirque-input-module
          revision: main # Or a specific commit/tag
          path: modules/cirque-input-module
      self:
        path: config
    ```
    Run `west update` afterwards.

2.  **Enable Kconfig Options:** Add the following to your `.conf` file (e.g., `config/sofle_ergomech.conf`):
    ```kconfig
    # Enable I2C and Pointing Device Support
    CONFIG_ZMK_POINTING=y
    CONFIG_I2C=y
    CONFIG_INPUT_PINNACLE=y
    ```

3.  **Configure Device Tree (`.overlay` / `.dtsi`):**
    *   **Define Split Input Node (in `boards/shields/sofle_ergomech/sofle_ergomech.dtsi`):** Ensure a split input node exists for the trackpad.
        ```devicetree
        / {
            // ... other nodes ...

            split_inputs {
                #address-cells = <1>;
                #size-cells = <0>;

                glidepoint_split: glidepoint_split@0 {
                    compatible = "zmk,input-split";
                    reg = <0>;
                    // Link to physical device added in peripheral overlay
                };
            };

            glidepoint_listener: glidepoint_listener {
                compatible = "zmk,input-listener";
                device = <&glidepoint_split>; // Point listener to the split device
                status = "disabled"; // Disabled by default, enabled on central overlay
            };
        };

        &pro_micro_i2c { // Or your board's I2C node
             status = "okay";
             // ... other I2C devices like OLED ...
        };
        ```
    *   **Define Physical Device (in `boards/shields/sofle_ergomech/sofle_ergomech_right.overlay`):** Define the trackpad on the I2C bus of the right side.
        ```devicetree
        #include "sofle_ergomech.dtsi" // Or your base shield dtsi

        // Link physical device to the split node defined in dtsi
        &glidepoint_split {
            device = <&glidepoint>;
        };

        // Define and enable physical device node
        &pro_micro_i2c { // Or your board's I2C node
            status = "okay"; // Ensure I2C bus is enabled

            glidepoint: glidepoint@2a { // Use 0x2a address
                compatible = "cirque,pinnacle";
                reg = <0x2a>; // Use address 0x2a
                status = "okay"; // Enable the device on this side
                dr-gpios = <&pro_micro 0 GPIO_ACTIVE_HIGH>; // Map DR to nice!nano D0 (P0.08)
                x-invert; // Invert X axis (adjust as needed)
                rotate-90; // Rotate (swap) X and Y axes (adjust as needed)
                sensitivity = "1x"; // Set sensitivity (1x=highest, 4x=lowest)
            };
        };
        ```
    *   **Enable Listener on Central Side (in `boards/shields/sofle_ergomech/sofle_ergomech_left.overlay`):** Enable the listener on the central (left) side.
        ```devicetree
        #include "sofle_ergomech.dtsi" // Or your base shield dtsi

        &glidepoint_listener {
            status = "okay"; // Enable listener on the central side
        };
        ```

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

*   **BASE:** Left: Volume Down/Up, Right: Scroll Down/Up
*   **LOWER:** Left: Scroll Left/Right, Right: Scroll Left/Right
*   **RAISE:** Left: Workspace Prev/Next, Right: Workspace Prev/Next
*   **NAV:** Left: App Switch Prev/Next, Right: App Switch Prev/Next
*   **WORK:** Left: Volume Down/Up, Right: Volume Down/Up
*   **SYSTEM:** Left: Volume Down/Up, Right: Volume Down/Up
*   **RESIZE:** Left: Resize Horizontal (Left/Right), Right: Resize Horizontal (Left/Right)
*   **RESIZE_SHIFT:** Left: Resize Vertical (Down/Up), Right: Resize Vertical (Down/Up)

## Building the Firmware

1.  Ensure you have a ZMK development environment set up.
2.  Clone this repository.
3.  Navigate to the `zmk/app` directory within your ZMK toolchain setup.
4.  Run `west update` to fetch the main ZMK code and the `cirque-input-module`.
5.  Build the firmware using west:
    ```bash
    # For Left Side (nice_nano_v2)
    west build -d build/left -b nice_nano_v2 -- -DSHIELD=sofle_ergomech_left -DZMK_CONFIG="/path/to/this/repo/config"

    # For Right Side (nice_nano_v2)
    west build -d build/right -b nice_nano_v2 -- -DSHIELD=sofle_ergomech_right -DZMK_CONFIG="/path/to/this/repo/config"
    ```
    (Replace `/path/to/this/repo/config` with the absolute path to the `config` directory of this repository).
6.  Flash the generated `.uf2` files from `build/left/zephyr/zmk.uf2` and `build/right/zephyr/zmk.uf2` to the respective controllers.

## License

This configuration is released under the MIT License.
