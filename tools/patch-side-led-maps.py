#!/usr/bin/env python3
"""Patch only the two faulty RAM-map update paths in the official Raise2 1.5.0 app.

No flashing. Requires the exact released input; leaves the program address, size,
version, radio payload, vectors and all other application instructions unchanged.
See README.md and patches/raise2-v1.5.0.json.
"""

# SPDX-License-Identifier: MIT
import argparse
import hashlib
from pathlib import Path
import struct
import zlib

STOCK_SHA256 = 'd01083b72600f77226f815fcc0828dcc08fb215dd2a6fa12a5fb88890a940186'
PATCHED_SHA256 = '1bf7b886df75ef50ff0a0f5a410a3d53ae0c40bfa96aedd2e3e607da2ad0ebc7'
STOCK_URL = 'https://github.com/Dygmalab/Firmware-release/releases/download/Raise2_v1.5.0/keyscanner.bin'
IMAGE_BIAS = 0x10005000
# At these points r0 is vector.end(), and the existing bounds check succeeded.
# Keep end() in r2 and skip emplace_back(). The subsequent normal map write and
# configuration flags are unchanged. Thumb MOVS r2,r0; B <existing next block>.
PATCHES = (
    (0x10015CEA, bytes.fromhex('a3689842'), bytes.fromhex('020006e0')),
    (0x10015DE2, bytes.fromhex('a3689842'), bytes.fromhex('020007e0')),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(image):
    require(len(image) >= 28, "Truncated application header")
    version, size, seal_crc, start, length, program_crc, program_version = struct.unpack_from('<7I', image)
    require((version, size, start, length, program_version) == (1, 28, 0x6000, 0x33E68, 0x01000000), "Unexpected application layout")
    seal = bytearray(image[:size])
    seal[8:12] = bytes(4)
    require(zlib.crc32(seal) == seal_crc, 'Seal CRC mismatch')
    require(zlib.crc32(image[0x1000:0x1000 + length]) == program_crc, 'Application CRC mismatch')


def patch(image):
    require(hashlib.sha256(image).hexdigest() == STOCK_SHA256, 'Input must be the exact official Raise2 1.5.0 keyscanner.bin')
    validate(image)
    result = bytearray(image)
    for address, expected, replacement in PATCHES:
        offset = address - IMAGE_BIAS
        require(result[offset:offset + len(expected)] == expected, "Unexpected instruction bytes")
        result[offset:offset + len(expected)] = replacement
    length = struct.unpack_from('<I', result, 16)[0]
    struct.pack_into('<I', result, 20, zlib.crc32(result[0x1000:0x1000 + length]))
    result[8:12] = bytes(4)
    struct.pack_into('<I', result, 8, zlib.crc32(result[:28]))
    validate(result)
    allowed = set(range(8, 12)) | set(range(20, 24))
    for address, expected, _ in PATCHES:
        allowed.update(range(address - IMAGE_BIAS, address - IMAGE_BIAS + len(expected)))
    require(len(result) == len(image), "Application size changed")
    require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(image, result))), "Changes outside declared patch windows")
    require(hashlib.sha256(result).hexdigest() == PATCHED_SHA256, "Unexpected patched output hash")
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = patch(args.input.read_bytes())
    require(args.input.resolve() != args.output.resolve(), "Refusing to replace the original input")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(result)
    print(hashlib.sha256(result).hexdigest(), args.output)


if __name__ == '__main__':
    main()
