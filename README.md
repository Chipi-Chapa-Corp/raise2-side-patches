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
