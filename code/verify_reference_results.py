"""Compare regenerated CSV results to the supplied reference numerical exports."""
from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
checked=[]
for folder in ['descriptive','nonparametric','extended','robustness','students']:
 for ref in sorted((ROOT/'reference_results'/folder).glob('*.csv')):
  out=ROOT/'results'/folder/ref.name
  if not out.exists():continue
  a,b=read(ref),read(out)
  assert len(a)==len(b),(ref.name,'row count')
  for i,(ra,rb) in enumerate(zip(a,b)):
   assert set(ra)==set(rb),(ref.name,'columns')
   for key in ra:
    va,vb=ra[key],rb[key]
    try:
     fa,fb=float(va),float(vb)
     ok=(math.isnan(fa) and math.isnan(fb)) or math.isclose(fa,fb,rel_tol=1e-8,abs_tol=1e-10)
    except (ValueError,TypeError):ok=va==vb
    assert ok,(ref.name,i,key,va,vb)
  checked.append({'file':str(ref.relative_to(ROOT/'reference_results')),'rows':len(a),'status':'matches'})
if not checked:raise SystemExit('No regenerated outputs to compare. Full reanalysis requires authorised access to the embargoed data.')
report={'checked_files':len(checked),'checks':checked,'scope':'Python numerical exports only. MATLAB mixed-effects reference coefficients were supplied, not refitted here.'}
(ROOT/'docs/verification_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
