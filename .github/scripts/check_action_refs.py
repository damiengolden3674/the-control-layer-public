#!/usr/bin/env python3
"""Fail-closed canonical GitHub Actions action-reference and checkout-token audit.

Only conventional block-style YAML action references are accepted. Noncanonical
action uses declarations must be rewritten before CI is accepted. Local composite
actions are traversed recursively; this is not a full YAML interpreter.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import sys

USE_REF = re.compile(r'^\s*(?:-\s*)?uses\s*:\s*([^\s#]+)(?:\s+#.*)?\s*$')
USE_LIKE = re.compile(r'''(?<![\w-])['"]?uses['"]?\s*:''')
REMOTE_PIN = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*@[a-fA-F0-9]{40}$')
DOCKER_PIN = re.compile(r'^docker://[^@\s]+@sha256:[a-fA-F0-9]{64}$')
STEP_START = re.compile(r'^\s*-\s*[A-Za-z_][A-Za-z0-9_-]*\s*:')
WITH_START = re.compile(r'^with\s*:\s*(?:#.*)?$')
CREDENTIALS_KEY = re.compile(r'^persist-credentials\s*:')
CREDENTIALS_OFF = re.compile(r'''^persist-credentials:\s*(?:false|['"]false['"])\s*(?:#.*)?$''', re.I)
BLOCK_SCALAR = re.compile(r'^\s*(?:-\s*)?[\w-]+\s*:\s*[|>][-+0-9]?\s*(?:#.*)?$')
ANCHOR_OR_ALIAS = re.compile(r'^\s*(?:-\s*)?(?:<<\s*:|[\w-]+\s*:\s*[&*][\w-]+)')
PERSISTENCE = re.compile(r'\bpersist-credentials\s*:')

def indentation(line):
    return len(line) - len(line.lstrip())

def immutable_reference(ref):
    if ref.startswith('./'):
        return True
    if ref.startswith('docker://'):
        return bool(DOCKER_PIN.fullmatch(ref))
    return bool(REMOTE_PIN.fullmatch(ref))

def checkout_credentials_disabled(step, field_indent):
    with_positions = [
        i for i, line in enumerate(step)
        if indentation(line) == field_indent and WITH_START.fullmatch(line.strip())
    ]
    if len(with_positions) != 1:
        return False
    i = with_positions[0]
    child_indent = None
    values = []
    for line in step[i+1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        depth = indentation(line)
        if depth <= field_indent:
            break
        if child_indent is None:
            child_indent = depth
        if depth == child_indent and CREDENTIALS_KEY.match(stripped):
            values.append(bool(CREDENTIALS_OFF.fullmatch(stripped)))
    return len(values) == 1 and values[0]

def extract_step(lines, position):
    line = lines[position]
    use_indent = indentation(line)
    dash = line.lstrip().startswith('- ')
    step_indent = use_indent if dash else use_indent - 2
    if step_indent < 0:
        return None
    start = None
    for j in range(position, -1, -1):
        text = lines[j]
        if STEP_START.match(text) and indentation(text) == step_indent:
            start = j
            break
        if j < position and text.strip() and indentation(text) < step_indent:
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start+1, len(lines)):
        text = lines[j]
        if text.strip() and not text.lstrip().startswith('#') and indentation(text) <= step_indent:
            end = j
            break
    return lines[start:end], step_indent + 2

def local_metadata(ref, repo_root):
    target = (repo_root / ref[2:]).resolve()
    if not target.is_relative_to(repo_root.resolve()) or not target.is_dir():
        return None
    candidates = [target / 'action.yml', target / 'action.yaml']
    existing = [candidate for candidate in candidates if candidate.is_file()]
    return existing[0] if len(existing) == 1 else None

def review(files, repo_root=None):
    root = Path.cwd().resolve() if repo_root is None else Path(repo_root).resolve()
    pending = list(files)
    seen = set()
    checked = 0
    errors = []
    while pending:
        path = Path(pending.pop(0)).resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            if not path.is_relative_to(root):
                raise ValueError('outside repository')
            lines = path.read_text(encoding='utf-8').splitlines()
        except (OSError, ValueError) as exc:
            errors.append(f'{path}: unreadable audit file: {type(exc).__name__}')
            continue
        scalar_indent = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            depth = indentation(line)
            if scalar_indent is not None:
                if depth > scalar_indent:
                    continue
                scalar_indent = None
            if BLOCK_SCALAR.fullmatch(line):
                scalar_indent = depth
                continue
            if ANCHOR_OR_ALIAS.match(line):
                errors.append(f'{path}:{i+1}: YAML anchors/aliases require canonical rewrite')
            if PERSISTENCE.search(line) and not stripped.startswith('persist-credentials:'):
                # Noncanonical credential keys must not evade the direct input check.
                if not stripped.startswith('#'):
                    errors.append(f'{path}:{i+1}: noncanonical checkout-credential input')
            if not USE_LIKE.search(line):
                continue
            match = USE_REF.fullmatch(line)
            if not match:
                errors.append(f'{path}:{i+1}: noncanonical or unparsable uses declaration')
                continue
            ref = match.group(1)
            checked += 1
            if not immutable_reference(ref):
                errors.append(f'{path}:{i+1}: mutable or invalid action reference: {ref}')
            if ref.startswith('./'):
                metadata = local_metadata(ref, root)
                if metadata is None:
                    errors.append(f'{path}:{i+1}: unresolved local action metadata: {ref}')
                elif metadata.resolve() not in seen:
                    pending.append(metadata)
            if ref.lower().startswith('actions/checkout@'):
                step = extract_step(lines, i)
                if step is None or not checkout_credentials_disabled(*step):
                    errors.append(f'{path}:{i+1}: checkout must set one direct with.persist-credentials: false')
    if checked == 0:
        errors.append('No action references scanned')
    return checked, errors

def self_test():
    assert immutable_reference('actions/checkout@11d5960a326750d5838078e36cf38b85af677262')
    assert immutable_reference('./.github/actions/example')
    assert immutable_reference('org/repo/.github/workflows/build.yml@' + 'a' * 40)
    for bad in ('actions/checkout@v4', 'actions/checkout@v7',
                'actions/upload-artifact@main', 'actions/checkout@deadbeef',
                'docker://image:latest'):
        assert not immutable_reference(bad), bad
    ref = 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262'
    prefix = 'jobs:\n  demo:\n    steps:\n'
    cases = [
        ('normal_checkout', prefix + f'      - uses: {ref}\n        with:\n          persist-credentials: false\n', True),
        ('mixed_case_without_flag', prefix + f'      - uses: Actions/Checkout@{ref.split("@")[1]}\n', False),
        ('env_spoof', prefix + f'      - uses: {ref}\n        env:\n          persist-credentials: false\n', False),
        ('nested_spoof', prefix + f'      - uses: {ref}\n        with:\n          nested:\n            persist-credentials: false\n', False),
        ('missing_flag', prefix + f'      - uses: {ref}\n', False),
        ('true_flag', prefix + f'      - uses: {ref}\n        with:\n          persist-credentials: true\n', False),
        ('duplicate_flag', prefix + f'      - uses: {ref}\n        with:\n          persist-credentials: false\n          persist-credentials: true\n', False),
        ('with_before_uses', prefix + f'      - name: Good\n        with:\n          persist-credentials: false\n        uses: {ref}\n', True),
        ('flow_style_uses', prefix + f'      - {{uses: {ref}}}\n', False),
        ('quoted_uses', prefix + f'      - "uses": {ref}\n', False),
        ('mutable_v7', prefix + '      - uses: actions/checkout@v7\n        with:\n          persist-credentials: false\n', False),
        ('script_scalar_ignored', prefix + f'      - uses: {ref}\n        with:\n          persist-credentials: false\n      - run: |\n          echo "uses: actions/checkout@v7"\n', True),
    ]
    with TemporaryDirectory() as temp:
        root = Path(temp)
        workflow_dir = root / '.github/workflows'
        workflow_dir.mkdir(parents=True)
        workflow = workflow_dir / 'audit.yml'
        for name, body, expected_ok in cases:
            workflow.write_text(body, encoding='utf-8')
            _, failures = review([workflow], root)
            assert (not failures) == expected_ok, (name, failures)
        action = root / '.github/actions/local'
        action.mkdir(parents=True)
        metadata = action / 'action.yml'
        workflow.write_text(prefix + '      - uses: ./.github/actions/local\n', encoding='utf-8')
        metadata.write_text('name: local\nruns:\n  using: composite\n  steps:\n    - uses: actions/checkout@v7\n', encoding='utf-8')
        _, failures = review([workflow], root)
        assert failures and any('mutable' in x for x in failures), failures
        metadata.write_text(f'name: local\nruns:\n  using: composite\n  steps:\n    - uses: {ref}\n      with:\n        persist-credentials: false\n', encoding='utf-8')
        _, failures = review([workflow], root)
        assert not failures, failures
    print('ACTION_POLICY_ADVERSARIAL_FIXTURES=PASS cases=14')

if __name__ == '__main__':
    self_test()
    files = []
    for suffix in ('*.yml','*.yaml'):
        files.extend(Path('.github/workflows').glob(suffix))
        files.extend(Path('.github/actions').rglob('action'+suffix[1:]))
        root_action = Path('action'+suffix[1:])
        if root_action.is_file():
            files.append(root_action)
    count, errors = review(files)
    if errors:
        for err in errors:
            print('REF_POLICY_FAIL:',err,file=sys.stderr)
        sys.exit(1)
    print(f'ACTION_SHA_PIN_AND_CREDENTIALS_POLICY=PASS checked={count}')
