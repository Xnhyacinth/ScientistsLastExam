#!/usr/bin/env python3
"""Replay every task wrapper against a frozen baseline from the same source/runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sle.metric_visibility import search_visible_metrics
from sle.provenance import finalize_report_trust, source_provenance
from sle.registry import list_tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text())
    provenance = source_provenance(ROOT)
    revision = (baseline.get('source_provenance') or {}).get('git_revision')
    if baseline.get('trusted_evidence') is not True or not revision:
        raise SystemExit('baseline must be trusted evidence with a source revision')
    if baseline.get('environment', {}).get('python') != sys.version:
        raise SystemExit('use the same interpreter as the baseline')
    unchanged = subprocess.run(['git', 'diff', '--exit-code', revision, 'HEAD', '--',
                                'sle', 'benchmarks', 'requirements-upstream.txt'],
                               cwd=ROOT, capture_output=True)
    if unchanged.returncode or provenance.get('source_tree_dirty') is not False:
        raise SystemExit('baseline/runtime source drift or dirty source')
    specs = list_tasks(None)
    old = {row['task']: row for row in baseline['tasks']}
    if len(old) != len(baseline['tasks']) or set(old) != {s.task_id for s in specs}:
        raise SystemExit('baseline inventory differs from current inventory')
    report = {'schema_version': 1, 'evidence_scope': 'PUBLIC_WRAPPER_BASELINE_REPLAY_ONLY',
              'source_provenance': provenance, 'baseline': str(args.baseline),
              'baseline_sha256': hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
              'tasks': []}
    with tempfile.TemporaryDirectory(prefix='sle_wrapper_audit_') as temporary:
        for index, spec in enumerate(specs, 1):
            record = old[spec.task_id]
            digest = hashlib.sha256(spec.initial_program_path.read_bytes()).hexdigest()
            if digest != record['candidate_sha256']:
                raise SystemExit('baseline candidate drift: ' + spec.task_id)
            expected = search_visible_metrics(record['runs'][0]['metrics'])
            expected.setdefault('raw_score', expected['combined_score'])
            output = Path(temporary) / 'metrics.json'
            row = {'task': spec.task_id, 'candidate_sha256': digest, 'passed': False}
            try:
                result = subprocess.run([
                    sys.executable, str(spec.task_dir / 'frontier_eval/run_eval.py'),
                    '--candidate', str(spec.initial_program_path), '--metrics-out', str(output),
                    '--timeout', str(args.timeout)], capture_output=True, text=True,
                    timeout=args.timeout + 180)
                row['returncode'] = result.returncode
                actual = json.loads(output.read_text()) if output.is_file() else None
                row['public_metrics'] = actual
                row['expected_public_metrics'] = expected
                row['passed'] = bool(result.returncode == 0 and not result.stderr
                                     and actual == expected and json.loads(result.stdout) == actual)
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                row['failure_kind'] = type(error).__name__
            report['tasks'].append(row)
            print('[%d/%d] %s passed=%s' % (index, len(specs), spec.task_id, row['passed']), flush=True)
    report['inventory_count'] = len(specs)
    report['passed_count'] = sum(row['passed'] for row in report['tasks'])
    finalize_report_trust(report, report['passed_count'] == len(specs))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
