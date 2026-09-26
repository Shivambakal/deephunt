# Tesla Model 3 ICE Firmware on QEMU — Part 2: Debugging + Fixing
Source: https://cn0xroot.wordpress.com/2026/09/20/root_tesla_os_on_qemu_part_2_debugging_fixing/
Date saved: 2026-09-26

## Summary
- Continuation of the Tesla ICE (Model 3, Intel Elkhart Lake) QEMU project: bypassing integrity checks, fixing the boot chain, and debugging the full graphics stack to get the real car UI rendering and touch-interactive in QEMU.
- Bypassed dm-verity RSA verification with a minimal custom init (no signature check), fixed LVM re-format loops, RCU-stall panics, quota feature-bit re-adds, kernel-module version mismatches, and a Mesa DRI driver ABI mismatch (2020-era client libs vs 2024-era drivers).
- Transplanted an Ubuntu 22.04 Xorg/Mesa/libinput graphics stack into the 4.14 rootfs to achieve full 2D UI rendering; binary-patched `libQtCarUIFramework.so` plus a touch-proxy to get real touch interaction (temperature 72→70 verified via gdb).
- Found and fixed real sandbox/permission defects along the way: touchscreen event sandbox gaps, seccomp policies missing `clock_gettime` for `QtCarDvServer`/`inductivechargerd`, AppArmor denials — plus achieved a guest-internal root shell.

## Agent relevance
- Methodology value: a masterclass in systematic root-cause debugging (bisect, cross-validate via independent signals, never trust "looks fixed") — encode as the agent's debugging doctrine for complex targets.
- For automotive/IoT in-scope targets: enumerate sandbox layers (seccomp/kafel profiles, AppArmor, dm-verity) and check for under-specified syscall filters; Qt/Car-framework binaries are rich audit targets.
- Note Tesla's defense-in-depth as a reference model: factory key injection, TPM sealing, LUKS, dm-verity, seccomp, AppArmor — use as a checklist of layers to test individually when assessing hardened embedded targets.
