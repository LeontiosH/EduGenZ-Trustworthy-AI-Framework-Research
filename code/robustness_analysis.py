"""Reproduce additional version-12 sensitivity checks. Does not alter earlier analyses.
Usage: python analyse_robustness.py data/responses.csv OUTPUT_DIRECTORY
"""
from data_io import load_legacy_rows
from pathlib import Path
import sys, json, csv, hashlib
import numpy as np
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import rankdata, spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

source=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rows=load_legacy_rows(source)
x=np.asarray([r[4:88] for r in rows[4:]],float)
assert x.shape==(87,84) and np.isin(x,[0,1,2,3]).all()
instit=np.asarray([r[1] for r in rows[4:]])
roles=np.asarray([r[2] for r in rows[4:]])
codes=list(dict.fromkeys(rows[0][4:88])); headers=np.asarray(rows[0][4:88])
sums=np.column_stack([x[:,headers==c].sum(1) for c in codes])
counts=np.column_stack([(x[:,headers==c]>0).sum(1) for c in codes])
y=np.divide(sums,counts,out=np.full_like(sums,np.nan),where=counts>0)*10/3
def pooled(mask): return sums[mask].sum(0)/counts[mask].sum(0)*10/3
allmask=np.ones(87,bool); base=pooled(allmask)
def write(name,records):
    with (out/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader();w.writerows(records)
def ranks(v):return rankdata(-v,method='average')
cases=[('All participants',allmask,'Primary')]
cases += [('Without '+c,instit!=c,'Institution omission') for c in np.unique(instit)]
cases += [('Without '+c,roles!=c,'Role omission') for c in np.unique(roles)]
summaries=[];scores=[]
for name,mask,kind in cases:
    v=pooled(mask);complete=mask & np.isfinite(y).all(1)
    p=PCA().fit(StandardScaler().fit_transform(y[complete]))
    direction=p.components_[0]*np.sign(p.components_[0].sum())
    record=dict(Scenario=name,Type=kind,N=int(mask.sum()),Complete_profiles=int(complete.sum()),
                PC1_percent=float(p.explained_variance_ratio_[0]*100),
                PC1_min_aligned_coefficient=float(direction.min()),
                Rank_correlation=float(spearmanr(base,v).statistic),
                Maximum_absolute_change=float(np.max(abs(v-base))),
                First_ranked=codes[int(np.argmax(v))],
                Ranking=' > '.join(codes[i] for i in np.argsort(-v)))
    summaries.append(record);scores.append(v)
equal_part=np.nanmean(y,axis=0)
equal_inst=np.mean([pooled(instit==c) for c in np.unique(instit)],axis=0)
for name,v in [('Equal participant weights',equal_part),('Equal institution weights',equal_inst)]:
    scores.append(v)
    summaries.append(dict(Scenario=name,Type='Alternative weighting',N=87,Complete_profiles='',PC1_percent='',PC1_min_aligned_coefficient='',
                          Rank_correlation=float(spearmanr(base,v).statistic),Maximum_absolute_change=float(np.max(abs(v-base))),
                          First_ranked=codes[int(np.argmax(v))],Ranking=' > '.join(codes[i] for i in np.argsort(-v))))
write('sensitivity_scenarios.csv',summaries)
write('requirement_scores_by_scenario.csv',[dict(Scenario=r['Scenario'],**{c:float(v[j]) for j,c in enumerate(codes)}) for r,v in zip(summaries,scores)])
rng=np.random.default_rng(20261105)
w=rng.multinomial(87,np.ones(87)/87,size=20000)
b=w@sums/(w@counts)*10/3
top=np.isclose(b,b.max(axis=1,keepdims=True),rtol=0,atol=1e-12)
credits=top/top.sum(1,keepdims=True)
branks=rankdata(-b,axis=1,method='average')
boot=[]
for j,c in enumerate(codes):
    boot.append(dict(Requirement=c,Mean=float(base[j]),CI_low=float(np.quantile(b[:,j],.025)),
                     CI_high=float(np.quantile(b[:,j],.975)),Top_rank_credit_percent=float(credits[:,j].mean()*100),
                     Median_rank=float(np.median(branks[:,j])),Rank_2_5_percentile=float(np.quantile(branks[:,j],.025)),
                     Rank_97_5_percentile=float(np.quantile(branks[:,j],.975))))
write('bootstrap_priorities.csv',boot)
write('bootstrap_rank_frequencies.csv',[dict(Requirement=c,Rank=float(k),Fraction=float(np.mean(branks[:,j]==k))) for j,c in enumerate(codes) for k in np.unique(branks[:,j])])
write('institution_profile_scores.csv',[dict(Institution=c,N=int((instit==c).sum()),**{code:float(v) for code,v in zip(codes,pooled(instit==c))}) for c in np.unique(instit)])
payload=dict(source=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),seed=20261105,
             bootstrap_replicates=20000,codes=codes,software={'Python':sys.version.split()[0],'NumPy':np.__version__,'scikit-learn':sklearn.__version__},
             omission_PC1_range=[min(r['PC1_percent'] for r in summaries[1:9]),max(r['PC1_percent'] for r in summaries[1:9])],
             omission_max_score_change=max(r['Maximum_absolute_change'] for r in summaries[1:9]),
             scenarios=summaries,bootstrap=boot,
             interpretation='Conditional nonzero importance. Whole-participant bootstrap within the observed sample. No external validation or population weighting. PCA is refitted and restandardised within each omission subset. Weighting scenarios change summaries only; PCA is not reweighted.')
(out/'robustness_summary.json').write_text(json.dumps(payload,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'svg.fonttype':'none'})
fig=plt.figure(figsize=(14,8.5));gs=fig.add_gridspec(2,2,width_ratios=[1.6,1],height_ratios=[1,1],wspace=.4,hspace=.6)
ax=fig.add_subplot(gs[:,0]);a=np.asarray(scores)
im=ax.imshow(a,cmap='YlGnBu',vmin=7,vmax=9,aspect='auto')
ax.set_xticks(range(7),codes);ax.set_yticks(range(len(summaries)),[r['Scenario'] for r in summaries])
for i in range(len(summaries)):
    for j in range(7):ax.text(j,i,f'{a[i,j]:.2f}',ha='center',va='center',fontsize=9,color='white' if a[i,j]>=8.2 else '#152536')
ax.set_title('A  Importance under omission and weighting checks',loc='left',fontsize=12,pad=16,fontweight='bold')
fig.colorbar(im,ax=ax,orientation='horizontal',pad=.09,shrink=.8,label='Conditional mean importance (displayed colour range: 7-9)')
ax=fig.add_subplot(gs[0,1]);p=[r['PC1_percent'] for r in summaries[:9]]
ax.barh(np.arange(len(p)),p,color=['#153E57']+['#4C9AAB']*8)
ax.set_yticks(range(len(p)),[r['Scenario'].replace('Without ','- ') for r in summaries[:9]],fontsize=8)
ax.invert_yaxis();ax.axvline(p[0],color='#D55E00',ls='--',lw=1);ax.set_xlim(0,90)
for i,v in enumerate(p):ax.text(v+1,i,f'{v:.1f}',va='center',fontsize=8)
ax.set_xlabel('Variance explained by PC1 (%)');ax.set_title('B  Refit profile structure',loc='left',fontsize=12,fontweight='bold',pad=16)
ax=fig.add_subplot(gs[1,1]);vals=[r['Top_rank_credit_percent'] for r in boot]
ax.barh(codes,vals,color=['#A7BDC7' if c!='PDG' else '#009E73' for c in codes]);ax.invert_yaxis();ax.set_xlim(0,105)
for i,v in enumerate(vals):ax.text(v+1,i,f'{v:.2f}',va='center',fontsize=8)
ax.set_xlabel('First-rank share of bootstrap replicates (%)')
ax.set_title('C  Bootstrap first-rank shares',loc='left',fontsize=12,fontweight='bold',pad=16)
for ax in fig.axes:
    if ax in [fig.axes[0]]:continue
    ax.spines[['top','right']].set_visible(False)
fig.subplots_adjust(left=.19,right=.96,top=.93,bottom=.1)
fig.savefig(out/'CEAI_Fig15_Robustness.png',dpi=300,bbox_inches='tight',facecolor='white')
plt.close(fig)
print(json.dumps({k:payload[k] for k in ['omission_PC1_range','omission_max_score_change','bootstrap']},indent=2))
