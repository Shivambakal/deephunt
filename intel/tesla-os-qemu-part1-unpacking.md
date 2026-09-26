# Tesla Model 3 ICE Firmware on QEMU — Part 1: Unpacking
Source: https://cn0xroot.wordpress.com/2026/09/19/root-tesla-os-on-qemu-part-1-unpacking/
Date saved: 2026-09-26

## Summary
- Researcher 0xroot documented unpacking a 59.28 GiB eMMC dump of a Tesla Model 3 ICE (In-Car Entertainment) unit (Intel Elkhart Lake platform) for the Tesla bug bounty program, using AI (Claude Code) to record the workflow.
- Firmware protections mapped: LUKS1 data volumes with TPM 2.0-sealed keys, dm-verity RSA-signed squashfs rootfs, custom `iasImage` container (magic `ipk.`) with RSA-2048 signature verified by a kexec two-stage bootloader.
- Core puzzle: the squashfs didn't fit its partition — reversed `verity-init` with radare2 to recover a dm-linear拼接 formula (partition 2/3 + tail of the LVM partition), then found a 3072-byte systematic offset caused by a page-truncation (`>>12<<3`) semantic lost when translating disassembly to a rebuild script.
- Key lesson: when re-implementing arithmetic from disassembly, preserve exact bit-truncation semantics; "looks reasonable" values can hide constant offsets discoverable only via brute-force window search against a "must be a valid metadata block" constraint.

## Agent relevance
- Firmware/embedded recon playbook: always start with read-only partition-table + bootlog analysis; device boot logs often reveal proprietary container formats directly (here `bootlog.0` gave the `iasImage` header layout).
- Detection fingerprints for similar targets: GPT with A/B `rootfs-a/b-legacy` + LVM data layout, `ipk.` magic, verity magic `0xba01ba01`, LUKS magic `4C55 4B53 BABE`, TPM-sealed `vcrypt` tokens with TCG OID `2.23.133.10.1.3`.
- If agent encounters automotive/IoT scope: check for squashfs+dm-verity, TPM sealing (physical extraction boundary — flag as manual-only), and public buildroot repos for version comparison.
