#!/usr/bin/env python3
"""Check the released input, exact output, change boundaries and refusal paths."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
patcher = runpy.run_path(str(root / 'tools/patch-side-led-maps.py'))
metadata = json.loads((root / 'patches/raise2-v1.5.0.json').read_text())
stock = Path(sys.argv[1]).read_bytes()
patched = patcher['patch'](stock)
assert len(stock) == metadata['input']['size_bytes']
assert hashlib.sha256(patched).hexdigest() == metadata['output']['sha256']
allowed = set(range(8, 12)) | set(range(20, 24))
for item in metadata['instruction_patches']:
    offset = int(item['file_offset'], 16)
    before, after = bytes.fromhex(item['before']), bytes.fromhex(item['after'])
    assert stock[offset:offset+4] == before and patched[offset:offset+4] == after
    allowed.update(range(offset, offset+4))
assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(stock, patched)))
for wrong in (stock[:-1], stock + b'\0', bytes([stock[0] ^ 1]) + stock[1:], patched):
    try:
        patcher['patch'](wrong)
    except ValueError:
        pass
    else:
        raise AssertionError('Patcher accepted an unrecognized input')
with tempfile.TemporaryDirectory() as directory:
    bad, output = Path(directory) / 'wrong.bin', Path(directory) / 'output.bin'
    bad.write_bytes(b'not firmware')
    result = subprocess.run([sys.executable, '-O', str(root / 'tools/patch-side-led-maps.py'),
                             str(bad), str(output)], capture_output=True)
    assert result.returncode != 0 and not output.exists(), 'Optimized Python bypassed input checks'
print('Side patch: exact output, declared change boundaries and corrupted/optimized-input rejection passed')
