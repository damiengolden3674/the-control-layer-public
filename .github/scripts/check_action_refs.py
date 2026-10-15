#!/usr/bin/env python3
"""Require immutable GitHub Actions references and nonpersisted checkout tokens."""
from pathlib import Path
import re
import sys

USE_START = re.compile(r'^\s*(?:-\s*)?uses\s*:')
USE_REF = re.compile(r'^\s*(?:-\s*)?uses\s*:\s*([^\s#]+)(?:\s+#.*)?\s*$')
REMOTE_PIN = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*@[a-fA-F0-9]{40}$')
DOCKER_PIN = re.compile(r'^docker://[^@\s]+@sha256:[a-fA-F0-9]{64}$')
STEP_START = re.compile(r'^\s*-\s*(?:uses|name|id|run)\s*:')
CREDENTIALS_OFF = re.compile(r'^\s*persist-credentials:\s*(?:false|[\'\"]false[\'\"])\s*(?:#.*)?$', re.I)

def immutable_reference(ref):
    if ref.startswith('./'):
        return True
    if ref.startswith('docker://'):
        return bool(DOCKER_PIN.fullmatch(ref))
    return bool(REMOTE_PIN.fullmatch(ref))

def review(files):
    errors=[]
    checked=0
    for path in sorted(files):
        lines=path.read_text(encoding='utf-8').splitlines()
        for i,line in enumerate(lines):
            if not USE_START.match(line):
                continue
            match=USE_REF.fullmatch(line)
            if not match:
                errors.append(f'{path}:{i+1}: unparsable uses declaration')
                continue
            ref=match.group(1)
            checked+=1
            if not immutable_reference(ref):
                errors.append(f'{path}:{i+1}: mutable/unpinned action reference: {ref}')
            if ref.startswith('actions/checkout@'):
                indent=len(line)-len(line.lstrip())
                step_lines=[]
                for next_line in lines[i+1:]:
                    if len(next_line)-len(next_line.lstrip()) <= indent and STEP_START.match(next_line):
                        break
                    step_lines.append(next_line)
                if not any(CREDENTIALS_OFF.fullmatch(x) for x in step_lines):
                    errors.append(f'{path}:{i+1}: persist-credentials: false required')
    if checked == 0:
        errors.append('No action references scanned')
    return checked,errors

def self_test():
    assert immutable_reference('actions/checkout@11d5960a326750d5838078e36cf38b85af677262')
    assert immutable_reference('./.github/actions/example')
    assert immutable_reference('org/repo/.github/workflows/build.yml@' + 'a'*40)
    for bad in ['actions/checkout@v4','actions/checkout@v7',
                'actions/upload-artifact@main','actions/checkout@deadbeef',
                'docker://image:latest']:
        assert not immutable_reference(bad),bad

if __name__=='__main__':
    self_test()
    paths=[p for suffix in ('*.yml','*.yaml') for p in Path('.github/workflows').glob(suffix)]
    n, failures=review(paths)
    if failures:
        for failure in failures:
            print(f'REF_POLICY_FAIL: {failure}',file=sys.stderr)
        sys.exit(1)
    print(f'ACTION_SHA_PIN_AND_CREDENTIALS_POLICY=PASS checked={n}')
