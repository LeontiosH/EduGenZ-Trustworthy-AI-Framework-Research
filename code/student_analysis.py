"""Student-role sensitivity extension. Original files and analyses are not modified.
Usage: python analyse_student_priorities.py [data/responses.csv] [output_directory]
"""
from data_io import load_legacy_rows
from pathlib import Path
from collections import Counter
import csv,json,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/responses.csv'
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'results/students'
OUT.mkdir(parents=True,exist_ok=True)
rows=load_legacy_rows(SOURCE)
X=np.asarray([r[4:88] for r in rows[4:]],float)
role=np.asarray([r[2] for r in rows[4:]]);inst=np.asarray([r[1] for r in rows[4:]])
assert X.shape==(87,84) and np.isin(X,[0,1,2,3]).all()
seed=20261106;B=50000
colors=dict(zip(['HAO','TRS','PDG','TPR','DnDF','SEW','ACC'],['#0072B2','#E69F00','#009E73','#CC79A7','#56B4E9','#D55E00','#6B6B6B']))
def savecsv(name,rs):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
allrecords=[];rankrecords=[];relative_records=[];summaries={}
for k,(group,mask) in enumerate([('Students_all',np.isin(role,['STU','EGZ-M-STU'])),('Students_nonproject',role=='STU')]):
 x=X[mask];n=len(x);rng=np.random.default_rng(seed+k)
 W=rng.multinomial(n,np.full(n,1/n),size=B).astype(float)
 levelrecords={};score=None;boots_main=None
 for level in [0,1]:
  headers=np.asarray(rows[level][4:88]);codes=list(dict.fromkeys(headers));rr=[];profiles=[];bb=[]
  for c in codes:
   v=x[:,headers==c];cnt=(v>0).sum(1);tot=v.sum(1)
   scores=np.divide(tot,cnt,out=np.full(n,np.nan),where=cnt>0)*10/3
   counts=W@cnt;bs=np.divide(W@tot,counts,out=np.full(B,np.nan),where=counts>0)*10/3
   br=counts/(n*v.shape[1])*100
   rr.append(dict(Group=group,Level='Requirement' if level==0 else 'Subcategory',Code='RFPR' if c=='PFPR' else c,N=n,Defined_scores=int((cnt>0).sum()),Items=v.shape[1],Relevance_percent=float(cnt.sum()/v.size*100),Relevance_low=float(np.quantile(br,.025)),Relevance_high=float(np.quantile(br,.975)),Importance=float(tot.sum()/cnt.sum()*10/3),Importance_low=float(np.nanquantile(bs,.025)),Importance_high=float(np.nanquantile(bs,.975))))
   profiles.append(scores);bb.append(bs)
  if level==0:score=np.array(profiles).T;boots_main=np.array(bb).T;maincodes=codes
  allrecords+=rr;levelrecords[level]=rr
 # First-rank credit uses paired draws across all seven requirement means.
 maxv=boots_main.max(1,keepdims=True);tie=np.isclose(boots_main,maxv,atol=1e-12,rtol=0)
 share=(tie/tie.sum(1,keepdims=True)).mean(0)*100
 for c,s in zip(maincodes,share):rankrecords.append(dict(Group=group,Code=c,First_rank_credit_percent=float(s)))
 # Mean centred profile: complete student profiles, equal participant weighting.
 complete=np.isfinite(score).all(1);P=score[complete];C=P-P.mean(1,keepdims=True);nc=len(P)
 wr=np.random.default_rng(seed+100+k).multinomial(nc,np.full(nc,1/nc),size=B).astype(float)
 bootc=wr@C/nc;mean=C.mean(0);lo,hi=np.quantile(bootc,[.025,.975],axis=0)
 assert np.allclose(C.sum(1),0) and np.isclose(mean.sum(),0)
 for j,c in enumerate(maincodes):relative_records.append(dict(Group=group,Code=c,Complete_profiles=nc,Mean_relative_score=float(mean[j]),CI_low=float(lo[j]),CI_high=float(hi[j])))
 order=sorted(levelrecords[0],key=lambda r:-r['Importance'])
 summaries[group]=dict(N=n,Institution_counts=dict(Counter(inst[mask])),Role_counts=dict(Counter(role[mask])),Complete_requirement_profiles=nc,Requirement_order=[r['Code'] for r in order],Top_rank_credit={r['Code']:r['First_rank_credit_percent'] for r in rankrecords if r['Group']==group},Relative_order=[maincodes[i] for i in np.argsort(-mean)])
savecsv('student_relevance_importance.csv',allrecords)
savecsv('student_rank_stability.csv',rankrecords)
savecsv('student_relative_priorities.csv',relative_records)
summary=dict(source=SOURCE.name,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),seed=seed,bootstrap_resamples=B,groups=summaries,scope='Student-role analysis, not verified generational membership, literacy assessment, or systems-thinking performance assessment.',software=dict(Python=sys.version.split()[0],NumPy=np.__version__,Matplotlib=matplotlib.__version__))
(OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2))

req=[r for r in allrecords if r['Group']=='Students_all' and r['Level']=='Requirement']
rel=[r for r in relative_records if r['Group']=='Students_all'];rel57={r['Code']:r for r in relative_records if r['Group']=='Students_nonproject'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':11})
fig,axs=plt.subplots(2,1,figsize=(7.4,8.6),gridspec_kw={'height_ratios':[1.05,1]},layout='constrained')
ax=axs[0]
offsets={'HAO':(-42,13),'TRS':(-48,-21),'PDG':(8,12),'TPR':(-38,-23),'DnDF':(11,-20),'SEW':(10,12),'ACC':(11,-9)}
for r in req:
 c=r['Code'];x=r['Relevance_percent'];y=r['Importance']
 ax.errorbar(x,y,xerr=[[x-r['Relevance_low']],[r['Relevance_high']-x]],yerr=[[y-r['Importance_low']],[r['Importance_high']-y]],fmt='o',color=colors[c],ecolor=colors[c],alpha=.78,capsize=3,ms=7,lw=1)
 dx,dy=offsets[c];ax.annotate(c,(x,y),xytext=(dx,dy),textcoords='offset points',fontweight='bold',color=colors[c],bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
ax.set(xlabel='Relevant item responses (%)',ylabel='Conditional importance (3.33–10)',xlim=(79,98),ylim=(7.0,8.85));ax.grid(alpha=.15)
ax.set_title(f'A  Relevance and importance (n = {summaries["Students_all"]["N"]})',loc='left',fontweight='bold',pad=12)
ax=axs[1];order=np.argsort([-r['Mean_relative_score'] for r in rel]);yy=np.arange(7)
for pos,j in enumerate(order):
 r=rel[j];c=r['Code'];m=r['Mean_relative_score']
 ax.errorbar(m,pos,xerr=[[m-r['CI_low']],[r['CI_high']-m]],fmt='o',color=colors[c],capsize=4,ms=7,lw=1.5)
 ax.plot(rel57[c]['Mean_relative_score'],pos+.15,marker='D',ms=4,mfc='white',mec='#333333',linestyle='none')
ax.axvline(0,color='#777777',ls='--',lw=1);ax.set_yticks(yy,[rel[j]['Code'] for j in order]);ax.invert_yaxis();ax.set(xlabel='Deviation from own mean (score units)',xlim=(-.8,.6));ax.grid(axis='x',alpha=.15)
ax.set_title(f'B  Relative priorities (n = {summaries["Students_all"]["Complete_requirement_profiles"]})',loc='left',fontweight='bold',pad=12)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([],[],marker='o',color='#555555',ls='none',label='All student roles: mean and 95% CI'),Line2D([],[],marker='D',mfc='white',mec='#333333',ls='none',label='Non-project students: mean')],loc='lower right',fontsize=8,frameon=False)
fig.savefig(OUT/'CEAI_Fig16_Student_Priorities.png',dpi=300,facecolor='white');plt.close(fig)
print(json.dumps(summary,indent=2))
