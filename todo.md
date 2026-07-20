# TODO

- [x] Right thumb buttons resolved 2026-07: Enter / Del / Alt+Tab /
      sticky Ctrl+Alt (outward from inner). RCTRL and K_CMENU retired.
- [ ] Gaming layer: revisit later — needs a trigger decision (&tog from
      SYSTEM?) and plain instant mods, no tap dances
- [ ] Consider zmk-tri-state "swapper" module for the Alt+Tab key if
      hold-to-cycle via key repeat feels clumsy (adds reverse cycling)
- [x] BLE stage 1 (1M PHY restore) flashed 2026-07 — wedges persisted,
      correlated with a failing Windows BT controller flapping the link.
- [x] BLE stage 2 applied: `CONFIG_BT_BUF_ACL_TX_COUNT=8` +
      `CONFIG_BT_BUF_EVT_RX_COUNT=16`, to keep the split link alive when a
      dead host link pins the shared TX pool. Replacement Windows machine
      also inbound (addresses the trigger itself).
- [ ] After the replacement machine arrives, confirm whether wedges are
      fully gone; if so the flaky controller was the trigger and the buffer
      headroom is belt-and-suspenders.

Done (kept for context): encoder direction swap, 2x scroll speed, trackpad
scroll-only on RAISE, trackpad tap-to-click. A gaming layer existed briefly
and is no longer present in the keymap.
