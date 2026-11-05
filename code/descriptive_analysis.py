from pathlib import Path
import csv, json, sys
import numpy as np
from data_io import load_legacy_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'results/descriptive'
OUT.mkdir(parents=True, exist_ok=True)
source = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/responses.csv'
rows = load_legacy_rows(source)
X = np.array([r[4:88] for r in rows[4:]], dtype=float)
assert X.shape == (87,84) and np.isin(X,[0,1,2,3]).all()
main = np.array(rows[0][4:88]); sub = np.array(rows[1][4:88])
main_names = dict(zip(['HAO','TRS','PDG','TPR','DnDF','SEW','ACC'], ['Human agency and oversight','Technical robustness and safety','Privacy and data governance','Transparency','Diversity, non-discrimination and fairness','Societal and environmental well-being','Accountability']))
sub_names = dict(zip(['HAA','HO','RAS','GS','A','PFPR','PR','DG','TRC','EXP','COM','AUB','AUD','SP','EWB','IWS','ISLD','AU','RM'], ['Human agency and autonomy','Human oversight','Resilience to attack and security','General safety','Accuracy','Reliability, fallback plans and reproducibility','Privacy','Data governance','Traceability','Explainability','Communication','Avoidance of unfair bias','Accessibility and universal design','Stakeholder participation','Environmental well-being','Impact on work and skills','Impact on society at large or democracy','Auditability','Risk management']))
B=50000; seed=20261105
rng=np.random.default_rng(seed)
weights=rng.multinomial(87,np.full(87,1/87),size=B).astype(float)
def calculate(headers,names):
    output=[]
    for code in dict.fromkeys(headers):
        a=X[:,headers==code]; valid=a>0
        sums=np.where(valid,a,0).sum(axis=1); counts=valid.sum(axis=1)
        boot_counts=weights@counts
        boot=(weights@sums)/np.where(boot_counts>0,boot_counts,np.nan)*10/3
        lo,hi=np.nanquantile(boot,[.025,.975])
        vals=a[valid]*10/3
        output.append(dict(Code=code,Name=names[code],Items=a.shape[1],Participants=int((counts>0).sum()),Relevant_ratings=int(counts.sum()),Non_relevant_ratings=int((~valid).sum()),Relevant_percent=100*valid.mean(),Mean=float(vals.mean()),SD_ratings=float(vals.std(ddof=1)),CI_lower=float(lo),CI_upper=float(hi)))
    return output
results={'Requirements':calculate(main,main_names),'Subcategories':calculate(sub,sub_names)}
assert sum(r['Relevant_ratings'] for r in results['Requirements'])==6462
assert sum(r['Non_relevant_ratings'] for r in results['Requirements'])==846
for key, records in results.items():
    with (OUT/(key.lower()+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
sample=[]
for j,variable in [(1,'Institution'),(3,'Gender'),(2,'Relationship to EduGenZ')]:
    values=[r[j] for r in rows[4:]]
    for level in sorted(set(values)):
        count=values.count(level)
        sample.append(dict(Characteristic=variable,Level=level,N=count,Percent=count/87*100))
with (OUT/'sample_characteristics.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=sample[0].keys());w.writeheader();w.writerows(sample)
tex=[r'% Requires \usepackage{longtable,array}. Captions precede tables.',r'% PFPR is the workbook code for the subcategory called RFPR in the taxonomy.',r'% Retain the mean as the pooled-rating estimand; CIs resample whole participants.']
for key,records in results.items():
    tex += [r'\begin{longtable}{@{}p{0.47\linewidth}rrr@{}}',r'\caption{Descriptive importance scores across trustworthiness '+key.lower()+r'.}\label{tab:descriptive-'+key.lower()+r'}\\',r'\hline',r'Requirement or subcategory & Items & Ratings & Mean (95\% CI) \\',r'\hline',r'\endfirsthead',r'\hline',r'Requirement or subcategory & Items & Ratings & Mean (95\% CI) \\',r'\hline',r'\endhead',r'\hline',r'\endfoot',r'\hline',r'\multicolumn{4}{@{}p{0.97\linewidth}@{}}{\footnotesize Notes: Ratings denotes the number of non-zero item ratings; it is not the participant count. Means pool relevant ratings and are multiplied by $10/3$ (possible range: approximately 3.33--10). Confidence intervals are percentile intervals from 50,000 bootstrap samples of the 87 participants, retaining all items for each sampled participant. Questionnaire items are held fixed. Zero-coded judgements are excluded from importance summaries.}\\',r'\endlastfoot']
    for r in records:
        code='RFPR' if r['Code']=='PFPR' else r['Code']
        tex.append(f"{r['Name']} ({code}) & {r['Items']} & {r['Relevant_ratings']} & {r['Mean']:.2f} ({r['CI_lower']:.2f}--{r['CI_upper']:.2f}) "+r'\\')
    tex += [r'\end{longtable}','']
(OUT/'corrected_descriptive_tables.tex').write_text('\n'.join(tex))
method=r'''Descriptive importance scores were calculated by pooling non-zero item ratings within each requirement and subcategory. Means were rescaled by multiplying by $10/3$. To account for repeated ratings within participants, 95\% confidence intervals were calculated using a participant-level percentile bootstrap with 50,000 resamples. Each resample selected 87 participants with replacement and retained their complete item-response sets; the pooled mean was then recalculated after excluding zero-coded responses. The questionnaire items were held fixed.'''
(OUT/'methods_replacement.tex').write_text(method)
(OUT/'README.txt').write_text('Source: '+source.name+'\nParticipant records: Excel rows 5–91; items E:CJ (84).\nAll 7,308 item responses are observed; 846 are zero (non-relevance), and 6,462 are 1–3.\nThe mean matches the pooled-rating definition in computeALTAI_full.m. Participants with more relevant item ratings contribute more ratings to that mean.\n95% CIs replace the previous independence-based normal CIs with percentile bootstrap CIs. Whole participants are resampled; items are fixed.\nResamples: 50,000; NumPy default_rng seed: 20261105.\nSD_ratings is the spread of individual scaled ratings, not the SD of participant means.\nPFPR in the workbook is reported as RFPR in the LaTeX taxonomy. No item assignments changed.\nSample characteristics are calculated from the workbook. Age is absent; no age statistics were recalculated.\nNo mixed-effects or rank-based tests were rerun.\n')
(OUT/'results.json').write_text(json.dumps(results,indent=2))
