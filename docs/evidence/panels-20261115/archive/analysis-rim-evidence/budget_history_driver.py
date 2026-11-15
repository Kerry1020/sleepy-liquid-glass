"""Call only after complete history handback; freezes bytes before decode."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parent
assert len(sys.argv)==2,'Pass explicitly handed-back complete history directory'
C=Path(sys.argv[1]).resolve();m=json.loads((C/'matrix.json').read_text());assert m['status']=='passed' and len(m['captures'])==16
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(C.iterdir()) if p.is_file() and p.suffix in ['.png','.json']}
for p in [O/'budget-analysis-plan.md',O/'budget-analysis-plan.json',O/'budget_history_driver.py',O/'budget_analyze_history.py',O/'budget_complete_history_derivatives.py']:files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(O/'budget-history-predecode.json').write_text(json.dumps({'status':'before-first-budget-history-output-decode','candidate':str(C),'files':files},indent=2)+'\n')
# Original official historical diagnostic only writes into the selected output.
legacy=P/'analysis-alert-baseline/analyze_alert_baseline.py';ns={'__file__':str(legacy),'__name__':'budget_historical_template'};exec(compile(legacy.read_text(),str(legacy),'exec'),ns)
saved=sys.argv;sys.argv=[str(legacy),'--android',str(C),'--output',str(O/'budget-history')]
try:ns['main']()
finally:sys.argv=saved
for name in ['budget_analyze_history.py','budget_complete_history_derivatives.py']:
    p=O/name;exec(compile(p.read_text(),str(p),'exec'),{'__file__':str(p),'__name__':'budget_frozen_analysis'})
