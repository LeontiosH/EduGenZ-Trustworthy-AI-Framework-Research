"""Read-only numeric checks for MainManuscriptCEAI(2).tex review.
Usage: python audit_version12.py data/responses.csv OUTPUT_DIRECTORY
Does not refit mixed models or modify prior data, figures, or analyses.
"""
from data_io import load_legacy_rows
from pathlib import Path
import csv, json, hashlib, sys
import numpy as np, scipy
from scipy.stats import mannwhitneyu, kruskal

source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
rows=load_legacy_rows(source)
x=np.array([r[4:88] for r in rows[4:]],float)
assert x.shape==(87,84) and np.isin(x,[0,1,2,3]).all()
institution=np.array([r[1] for r in rows[4:]])
gender=np.array([r[3] for r in rows[4:]])
role=np.array([r[2] for r in rows[4:]])
design=np.column_stack([np.ones(87)]+[(v==c).astype(int) for v in [institution,gender,role] for c in sorted(set(v))[1:]])
records=[];design_records=[]
for level in [0,1]:
    header=np.array(rows[level][4:88])
    for c in dict.fromkeys(header):
        v=x[:,header==c];n=(v>0).sum(1)
        score=np.divide(v.sum(1),n,out=np.full(87,np.nan),where=n>0)*10/3
        ok=np.isfinite(score);f=score[ok&(gender=='Female')];m=score[ok&(gender=='Male')]
        test=mannwhitneyu(f,m,alternative='two-sided',method='asymptotic',use_continuity=True)
        itest=kruskal(*[score[ok&(institution==g)] for g in np.unique(institution)])
        rtest=kruskal(*[score[ok&(role==g)] for g in np.unique(role)])
        records.append(dict(Level='Requirement' if level==0 else 'Subcategory',Code='RFPR' if c=='PFPR' else c,
                            Female_n=len(f),Male_n=len(m),Female_median=float(np.median(f)),Male_median=float(np.median(m)),
                            Mann_Whitney_U_female=float(test.statistic),Gender_p=float(test.pvalue),Institution_KW_p=float(itest.pvalue),Role_KW_p=float(rtest.pvalue)))
        d=design[ok];design_records.append(dict(Level='Requirement' if level==0 else 'Subcategory',Code=c,
                                                Participants=int(ok.sum()),Full_fixed_design_columns=d.shape[1],
                                                Full_fixed_design_rank=int(np.linalg.matrix_rank(d)),
                                                Item_count=int((header==c).sum())))
def write(name,r):
    with (out/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
write('version12_nonparametric_audit.csv',records)
write('fixed_design_rank_check.csv',design_records)
summary=dict(source=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),N=87,
             gender_labels={str(c):int((gender==c).sum()) for c in np.unique(gender)},
             ratings=int(x.size),non_relevant_ratings=int((x==0).sum()),relevant_ratings=int((x>0).sum()),
             all_gender_tests_estimable=all(np.isfinite(r['Gender_p']) for r in records),
             nominal_gender_findings=[r for r in records if r['Gender_p']<.05],
             full_fixed_design_rank_all=int(np.linalg.matrix_rank(design)),
             source_code_diagnosis="Supplied MATLAB code compares gender_cat to lowercase 'male'/'female'; workbook contains 'Male'/'Female'. Both nonparametric loops require case-insensitive selection.",
             inference="Audit values are two-sided asymptotic Mann-Whitney tests with tie and continuity correction, without multiplicity adjustment. They are independent Python checks, not MATLAB execution or mixed-model estimates.",
             limitations="Fixed-design rank checks do not recover which model MATLAB fitted. The workbook does not include age.",
             software={'Python':sys.version.split()[0],'NumPy':np.__version__,'SciPy':scipy.__version__})
(out/'audit_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:summary[k] for k in ['N','all_gender_tests_estimable','nominal_gender_findings']},indent=2))
