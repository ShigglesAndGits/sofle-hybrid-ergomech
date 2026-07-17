# TODO

- [x] Right thumb buttons resolved 2026-07: Enter / Del / Alt+Tab /
      sticky Ctrl+Alt (outward from inner). RCTRL and K_CMENU retired.
- [ ] Gaming layer: revisit later — needs a trigger decision (&tog from
      SYSTEM?) and plain instant mods, no tap dances
- [ ] Consider zmk-tri-state "swapper" module for the Alt+Tab key if
      hold-to-cycle via key repeat feels clumsy (adds reverse cycling)
- [ ] BLE stability: verify the 1M PHY restore (2026-07). If wedges persist
      after a few days, apply stage 2: `CONFIG_BT_BUF_ACL_TX_COUNT=8` +
      `CONFIG_BT_BUF_EVT_RX_COUNT=16` (EVT_RX must exceed ACL_TX — that
      static assert is why the old =10 overrides were dropped, not because
      the defaults are adequate).

Done (kept for context): encoder direction swap, 2x scroll speed, trackpad
scroll-only on RAISE, trackpad tap-to-click. A gaming layer existed briefly
and is no longer present in the keymap.
