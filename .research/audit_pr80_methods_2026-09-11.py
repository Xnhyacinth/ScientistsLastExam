"""Fixed method qualification pilot. Never imports a candidate or oracle in this driver."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sle.algorithms.common import runtime_source_sha256, task_package_sha256
from sle.evaluate import evaluate_candidate
from sle.registry import find_task


def digest(value):
    if not isinstance(value,bytes):
        value=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--expected-revision',required=True)
    p.add_argument('--private-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if revision!=args.expected_revision:
        raise ValueError('wrong source revision')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise ValueError('source checkout must be clean before this fixed pilot')
    if sys.version_info[:2]!=(3,8) or sys.platform!='linux':
        raise ValueError('requires the fixed Linux Python 3.8 environment')
    import numpy,scipy
    if (numpy.__version__,scipy.__version__)!=('1.24.4','1.10.1'):
        raise ValueError('wrong scientific dependency versions')
    private=args.private_root.resolve(); output=args.output.resolve()
    if ROOT==private or ROOT in private.parents or private.exists() or output.exists():
        raise ValueError('private directory must be new and outside checkout; output must be new')
    private.mkdir(mode=0o700,parents=True);private.chmod(0o700)
    spec=find_task('DataPrivacy/SparseVectorAudit',include_uncertified=True)
    paths={'baseline':spec.initial_program_path,
           'positional_reference':spec.task_dir/'verification/reference_positional.py',
           'first_position_only':spec.task_dir/'verification/reference_library_scan.py',
           'no_scan':spec.task_dir/'verification/ablation_no_scan.py',
           'no_library':spec.task_dir/'verification/ablation_no_library.py',
           'positional_no_confirmation':spec.task_dir/'verification/probe_positional_no_confirmation.py',
           'legacy_no_confirmation':spec.task_dir/'verification/probe_legacy_no_confirmation.py'}
    sources={k:v.read_bytes() for k,v in paths.items()}
    report={'schema_version':1,'scope':'fixed public-method qualification pilot; not model calibration or global evidence',
            'source_revision':revision,'runtime_source_sha256':runtime_source_sha256(),
            'task_package_sha256':task_package_sha256(spec),'task_id':spec.task_id,
            'upstream_task_head':'4bb95061846a28a3025f4eb05cdd52210e12b11a',
            'candidate_plan_sha256':{k:digest(v) for k,v in sources.items()},
            'planned_calls':14,'completed_calls':0,'model_calls':0,'scientific_admission':'not_assessed',
            'timeout_seconds':300,'runtime':{'python':sys.version,'numpy':numpy.__version__,'scipy':scipy.__version__,
            'thread_environment':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}},'candidates':{}}
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    for name,source in sources.items():
        record={'candidate_sha256':digest(source),'runs':[]};report['candidates'][name]=record
        for repeat in (1,2):
            with tempfile.TemporaryDirectory(prefix='sle_pr80_pilot_') as tmp:
                candidate=Path(tmp)/'solution.py';candidate.write_bytes(source)
                started=time.monotonic()
                metrics=evaluate_candidate(spec,candidate,timeout_s=300)
                elapsed=time.monotonic()-started
            raw=private/('%s_%d.json'%(name,repeat))
            raw.write_text(json.dumps(metrics,indent=2,sort_keys=True,allow_nan=False)+'\n');raw.chmod(0o600)
            report['completed_calls']+=1
            record['runs'].append({'repeat':repeat,'wall_seconds':elapsed,'full_metrics_sha256':digest(metrics),
                                   'metrics':{k:v for k,v in metrics.items() if type(v) in (float,int,bool)}})
            output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
            print(json.dumps({'name':name,'repeat':repeat,'valid':metrics.get('valid'),'score':metrics.get('combined_score'),'seconds':elapsed}),flush=True)
            if metrics.get('infrastructure_failure'):
                raise RuntimeError('infrastructure failure; fixed pilot stopped')
        record['repeat_identical']=record['runs'][0]['full_metrics_sha256']==record['runs'][1]['full_metrics_sha256']
    report['runtime_unchanged']=runtime_source_sha256()==report['runtime_source_sha256']
    report['task_unchanged']=task_package_sha256(spec)==report['task_package_sha256']
    report['candidate_sources_unchanged']=all(paths[n].read_bytes()==s for n,s in sources.items())
    output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')


if __name__=='__main__':main()
