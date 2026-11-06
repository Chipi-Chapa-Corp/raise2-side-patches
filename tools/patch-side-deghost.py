#!/usr/bin/env python3
"""EXPERIMENT: map-allocation fixes plus a stronger CS anti-ghost pull-up.

Accepts only the official 1.5.0 input. Does not flash. Changes the generated
IS31FL3743B PG2/02 write from B3 to B1 (CS pull-up 2k to 0.5k during off time).
This is a documented setting, not a confirmed fix for the reported red tail.
"""
from pathlib import Path
import argparse
import hashlib
import runpy
import struct
import zlib

maps = runpy.run_path(str(Path(__file__).with_name('patch-side-led-maps.py')))
IMAGE_BIAS = maps['IMAGE_BIAS']
ADDRESS = 0x1000A272
BEFORE = bytes.fromhex('a03b')
AFTER = bytes.fromhex('a23b')
OUTPUT_SHA256 = 'f06a49cbb88f257665de466b7bd53bb86b98df0264955c8e0d9c159fa192562b'


def patch(stock):
    result = bytearray(maps['patch'](stock))
    offset = ADDRESS - IMAGE_BIAS
    maps['require'](result[offset:offset+2] == BEFORE, 'Unexpected deghost-setting instruction')
    result[offset:offset+2] = AFTER
    length = struct.unpack_from('<I', result, 16)[0]
    struct.pack_into('<I', result, 20, zlib.crc32(result[0x1000:0x1000+length]))
    result[8:12] = bytes(4)
    struct.pack_into('<I', result, 8, zlib.crc32(result[:28]))
    maps['validate'](result)
    allowed = set(range(8,12)) | set(range(20,24)) | set(range(offset,offset+2))
    normal = maps['patch'](stock)
    maps['require'](len(result)==len(normal) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(normal,result))), 'Changes outside declared experiment window')
    maps['require'](hashlib.sha256(result).hexdigest()==OUTPUT_SHA256, 'Unexpected experimental output hash')
    return bytes(result)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=patch(args.input.read_bytes())
    maps['require'](args.input.resolve()!=args.output.resolve(),'Refusing to replace original input')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as stream:stream.write(result)
    print(hashlib.sha256(result).hexdigest(),args.output)
