#!/usr/bin/env python3
"""Require immutable GitHub Actions references and nonpersisted checkout tokens."""
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import sys

USE_START = re.compile(r'^\s*(?:-\s*)?uses\s*:')
USE_REF = re.compile(r'^\s*(?:-\s*)?uses\s*:\s*([^\s#]+)(?:\s+#.*)?\s*$')
REMOTE_PIN = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*@[a-fA-F0-9]{40}$')
DOCKER_PIN = re.compile(r'^docker://[^@\s]+@sha256:[a-fA-F0-9]{64}$')
STEP_START = re.compile(r'^\s*-\s*[A-Za-z_][A-Za-z0-9_-]*\s*:')
CREDENTIALS_OFF = re.compile(r'^\s*persist-credentials:\s*(?:false|[\'\"]false[\'\"])\s*(?:#.*)?$', re.I)
WITH_START = re.compile(r'^with\s*:\s*(?:#.*)?$')

def immutable_reference(ref):
    if ref.startswith('./'):
        return True
    if ref.startswith('docker://'):
        return bool(DOCKER_PIN.fullmatch(ref))
    return bool(REMOTE_PIN.fullmatch(ref))

def checkout_credentials_disabled(step_lines, field_indent):
    """Require a direct checkout with: input, not an env value or nested string."""
    for i, line in enumerate(step_lines):
        depth = len(line) - len(line.lstrip())
        if depth != field_indent or not WITH_START.fullmatch(line.strip()):
            continue
        child_indent = None
        for child in step_lines[i+1:]:
            stripped = child.strip()
            if not stripped or stripped.startswith('#'):
                continue
            child_depth = len(child) - len(child.lstrip())
            if child_depth <= field_indent:
                break
            if child_indent is None:
                child_indent = child_depth
            if child_depth == child_indent and CREDENTIALS_OFF.fullmatch(child):
                return True
        return False
    return False

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
                field_indent = indent + (2 if line.lstrip().startswith('- ') else 0)
                if not checkout_credentials_disabled(step_lines, field_indent):
                    errors.append(f'{path}:{i+1}: persist-credentials: false required as direct checkout with: input')
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
    checkout = 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262'
    fixture = 'jobs:\n  test:\n    steps:\n      - uses: ' + checkout + '\n'
    cases = [
        ('        with:\n          persist-credentials: false\n', True),
        ('        env:\n          persist-credentials: false\n', False),
        ('        with:\n          nested:\n            persist-credentials: false\n', False),
        ('        with:\n          persist-credentials: true\n', False),
        ('', False),
    ]
    with TemporaryDirectory() as temp:
        path = Path(temp) / 'workflow.yml'
        for suffix, allowed in cases:
            path.write_text(fixture + suffix, encoding='utf-8')
            _, failures = review([path])
            assert (not failures) == allowed, (suffix, failures)

if __name__=='__main__':
    self_test()
    paths=[p for suffix in ('*.yml','*.yaml') for p in Path('.github/workflows').glob(suffix)]
    n, failures=review(paths)
    if failures:
        for failure in failures:
            print(f'REF_POLICY_FAIL: {failure}',file=sys.stderr)
        sys.exit(1)
    print(f'ACTION_SHA_PIN_AND_CREDENTIALS_POLICY=PASS checked={n}')
