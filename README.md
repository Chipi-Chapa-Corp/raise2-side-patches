# Raise 2 side application patches

Reproducible patches to the official Dygma Raise 2 side application. This project
does not contain the complete side firmware source and does not build that
application from source. It never flashes hardware.

## Current patch

The 1.5.0 backlight and underglow map handlers append a new layer when updating
an existing layer. Streaming maps therefore grows their layer vector continually.
Two four-byte Thumb instruction replacements skip that allocation while keeping
the existing bounds checks, map writes and configuration flags. Application and
seal CRC32 fields are recomputed. All other file bytes and the application size
remain unchanged.

Exact input, output, offsets and bytes are recorded in
[`patches/raise2-v1.5.0.json`](patches/raise2-v1.5.0.json).
The output is identical to the side image used with Splash revisions 2 through 7.
This is not a patch for the separately reported intermittent LED freeze; that
physical fault's cause has not been established.

## Generate and test

Use Python 3, download the official image, then run:

```bash
curl --fail --location --output /tmp/raise2-stock-keyscanner.bin \
  https://github.com/Dygmalab/Firmware-release/releases/download/Raise2_v1.5.0/keyscanner.bin
python tools/patch-side-led-maps.py \
  /tmp/raise2-stock-keyscanner.bin /tmp/raise2-patched-keyscanner.bin
python tests/test_patch.py /tmp/raise2-stock-keyscanner.bin
```

The patcher rejects every input except the exact released image and verifies
the complete output hash. Checks remain active under `python -O`. The CLI refuses
in-place modification and existing output files. Firmware images are generated
locally and excluded from Git.

The Neuron integration and instruction-emulation tests live in
[`Chipi-Chapa-Corp/NeuronWireless_raise2`](https://github.com/Chipi-Chapa-Corp/NeuronWireless_raise2/tree/raise2-v1.5.0-splash).
Its `side-patches` submodule pins this repository to an exact commit. The
corresponding source correction is in the
[`DefyCommunications` fork](https://github.com/Chipi-Chapa-Corp/DefyCommunications/tree/raise2-v1.5.0-splash).

## Limits

The intended changes do not touch reset vectors, the bootloader, radio code or
key scanning. Limited scope and passing software tests do not establish that
custom firmware or every recovery path is safe on hardware. The user reported
successful use of this side image; recovery after a failed side update remains
untested. Keep an official rollback package before installing custom firmware.

The MIT license applies to the patching tools and metadata in this repository;
it does not relicense Dygma firmware downloaded separately.

## Optional CS anti-ghost experiment

`tools/patch-side-deghost.py` is a separate experimental variant. The ordinary
map patcher and its output remain unchanged. The experiment adds one changed
instruction byte at execution address `0x1000a272` (two-byte instruction window):
`SUBS r3,#0xA0` becomes `SUBS r3,#0xA2`. The released initializer then writes
IS31FL3743B function-page register 02h as B1 instead of B3. This changes only the
CS pull-up selection from 2kΩ to 0.5kΩ during off time. SW pull-down, phase,
global LED current, PWM values and the two allocation fixes remain unchanged.

The [manufacturer datasheet](https://www.lumissil.com/assets/pdf/core/IS31FL3743B_DS.pdf)
describes this as an available de-ghost setting (Table 8 and the de-ghost section).
The stronger setting is a candidate for testing a subtle red phase reported on
all fading keys; it is not an established physical fix. It does not add PWM
resolution or fix the unavoidable lowest PWM 1→0 transition. No hardware safety,
power-consumption or physical rollback test is claimed. Metadata records the
exact input/output hashes, extra instruction bytes and CRC handling in
`patches/raise2-v1.5.0-deghost-experiment.json`.

Run it only as an explicitly selected experiment:

```bash
python tools/patch-side-deghost.py /path/to/official-1.5.0/keyscanner.bin /path/to/new-keyscanner.bin
```

Both patchers require the original official image and refuse unexpected inputs
or overwriting the input/output file. This tool never opens a keyboard or flashes
firmware. The main firmware checkout supplies emulation tests for the emitted
register bytes and a separately named test package, keeping ordinary r12 intact.
