#!/usr/bin/env python3
"""Check the explicitly selected experimental variant; no hardware access."""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
module=runpy.run_path(str(root/'tools/patch-side-deghost.py'))
metadata=json.loads((root/'patches/raise2-v1.5.0-deghost-experiment.json').read_text())
stock_path=Path(sys.argv[1]).resolve();stock=stock_path.read_bytes()
normal=module['maps']['patch'](stock);result=module['patch'](stock)
assert hashlib.sha256(result).hexdigest()==metadata['output_sha256']
assert len(result)==metadata['size_bytes']==len(stock)
offset=module['ADDRESS']-module['IMAGE_BIAS']
assert normal[offset:offset+2]==module['BEFORE'] and result[offset:offset+2]==module['AFTER']
allowed=set(range(8,12))|set(range(20,24))|set(range(offset,offset+2))
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(normal,result)))
module['maps']['validate'](result)
for wrong in (stock[:-1],stock+b'\0',normal,result):
    try:module['patch'](wrong)
    except ValueError:pass
    else:raise AssertionError('Unexpected input accepted')
with tempfile.TemporaryDirectory() as tmp:
    bad,output=Path(tmp)/'bad.bin',Path(tmp)/'output.bin'
    bad.write_bytes(b'not firmware')
    cli=[sys.executable,'-O',str(root/'tools/patch-side-deghost.py')]
    attempt=subprocess.run(cli+[str(bad),str(output)],capture_output=True)
    assert attempt.returncode!=0 and not output.exists()
    output.write_bytes(b'preserve existing output')
    attempt=subprocess.run(cli+[str(stock_path),str(output)],capture_output=True)
    assert attempt.returncode!=0 and output.read_bytes()==b'preserve existing output'
print('Optional deghost patch: exact hash/CRCs/boundaries, rejected inputs, optimized-input checks and output preservation passed')
