"""Version-12 exploratory extension; never overwrites the original analyses."""
from data_io import load_legacy_rows
from pathlib import Path
import json, csv, sys, hashlib, warnings
import numpy as np
import scipy
from scipy.stats import spearmanr, rankdata
from scipy.spatial.distance import pdist
import sklearn
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE, trustworthiness
from sklearn.neighbors import NearestNeighbors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[2]).expanduser().resolve() if len(sys.argv)>2 else ROOT/'results/extended'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path(sys.argv[1]).expanduser().resolve() if len(sys.argv)>1 else ROOT/'data/responses.csv'
rows=load_legacy_rows(SOURCE)
X=np.array([r[4:88] for r in rows[4:]],float)
assert X.shape==(87,84) and np.isin(X,[0,1,2,3]).all()
meta={'Institution':np.array([r[1] for r in rows[4:]]),'Relation':np.array([r[2] for r in rows[4:]]),'Gender':np.array([r[3] for r in rows[4:]])}
COLORS=dict(zip(['HAO','TRS','PDG','TPR','DnDF','SEW','ACC'],['#0072B2','#E69F00','#009E73','#CC79A7','#56B4E9','#D55E00','#6B6B6B']))
NAMES={'HAO':'Human agency and oversight','TRS':'Technical robustness and safety','PDG':'Privacy and data governance','TPR':'Transparency','DnDF':'Diversity, non-discrimination and fairness','SEW':'Societal and environmental well-being','ACC':'Accountability'}
seed=20261105
rng=np.random.default_rng(seed)
W=rng.multinomial(87,np.full(87,1/87),size=50000).astype(float)
def write_csv(name,records):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def savefig(fig,name):
    for ext in ['pdf','png','svg']:fig.savefig(OUT/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
    plt.close(fig)
def score_matrix(headers):
    codes=list(dict.fromkeys(headers)); scores=[];coverage=[];summaries=[]
    for code in codes:
        a=X[:,np.array(headers)==code];count=(a>0).sum(1);total=a.sum(1)
        scores.append(total/np.where(count,count,np.nan)*10/3)
        coverage.append(count/a.shape[1])
        bcount=W@count
        importance=W@total/np.where(bcount,bcount,np.nan)*10/3
        relevance=bcount/(87*a.shape[1])*100
        main=code if code in COLORS else rows[0][4+list(headers).index(code)]
        summaries.append(dict(Code=code,Parent=main,Items=a.shape[1],Participants=int((count>0).sum()),Relevant_percent=float(count.sum()/(87*a.shape[1])*100),Relevance_CI_low=float(np.quantile(relevance,.025)),Relevance_CI_high=float(np.quantile(relevance,.975)),Importance=float(total.sum()/count.sum()*10/3),Importance_CI_low=float(np.nanquantile(importance,.025)),Importance_CI_high=float(np.nanquantile(importance,.975))))
    return codes,np.array(scores).T,np.array(coverage).T,summaries
main,Y,coverage,main_summary=score_matrix(rows[0][4:88])
sub,S,sub_coverage,sub_summary=score_matrix(rows[1][4:88])
write_csv('relevance_importance_requirements.csv',main_summary)
write_csv('relevance_importance_subcategories.csv',sub_summary)
complete=np.isfinite(Y).all(1);complete_sub=np.isfinite(S).all(1)
high=complete&(coverage>=.5).all(1)
P=Y[complete];n=len(P)
z=StandardScaler().fit_transform(P)
pca=PCA().fit(z);pc=pca.transform(z)
if pca.components_[0].sum()<0:pca.components_[0]*=-1;pc[:,0]*=-1
loadings=pca.components_.T*np.sqrt(pca.explained_variance_*(n-1)/n)
overall=P.mean(1)
parallel=[]
prng=np.random.default_rng(seed+1)
for _ in range(2000):
    perm=np.column_stack([prng.permutation(z[:,j]) for j in range(7)])
    parallel.append(PCA().fit(perm).explained_variance_)
parallel95=np.quantile(parallel,.95,axis=0)
boot_load=[];boot_var=[];boot_corr=[]
brng=np.random.default_rng(seed+2)
for _ in range(5000):
    ix=brng.integers(0,n,n);zb=StandardScaler().fit_transform(P[ix]);pb=PCA().fit(zb)
    sign=1 if np.dot(pb.components_[0],pca.components_[0])>=0 else -1
    boot_load.append(pb.components_[0]*sign*np.sqrt(pb.explained_variance_[0]*(n-1)/n))
    boot_var.append(pb.explained_variance_ratio_[0])
boot_load=np.array(boot_load)
load_records=[dict(Requirement=c,PC1_loading=float(loadings[j,0]),PC1_CI_low=float(np.quantile(boot_load[:,j],.025)),PC1_CI_high=float(np.quantile(boot_load[:,j],.975)),PC2_loading=float(loadings[j,1])) for j,c in enumerate(main)]
write_csv('PCA_requirement_loadings.csv',load_records)
correlations=[];R=np.eye(7);Ns=np.zeros((7,7),int)
crng=np.random.default_rng(seed+3)
for i in range(7):
    Ns[i,i]=np.isfinite(Y[:,i]).sum()
    for j in range(i+1,7):
        ok=np.isfinite(Y[:,i])&np.isfinite(Y[:,j]);a=Y[ok,i];b=Y[ok,j];rho,p=spearmanr(a,b)
        idx=crng.integers(0,len(a),(5000,len(a)))
        aa=rankdata(a[idx],axis=1);bb=rankdata(b[idx],axis=1)
        aa-=aa.mean(1,keepdims=True);bb-=bb.mean(1,keepdims=True)
        rb=(aa*bb).sum(1)/np.sqrt((aa*aa).sum(1)*(bb*bb).sum(1))
        R[i,j]=R[j,i]=rho;Ns[i,j]=Ns[j,i]=ok.sum()
        correlations.append(dict(Requirement1=main[i],Requirement2=main[j],N=int(ok.sum()),Spearman_rho=float(rho),CI_low=float(np.nanquantile(rb,.025)),CI_high=float(np.nanquantile(rb,.975)),P=float(p)))
pv=np.array([r['P'] for r in correlations]);order=np.argsort(pv)
adj=np.minimum.accumulate((pv[order]*len(pv)/np.arange(1,len(pv)+1))[::-1])[::-1]
for idx,q in zip(order,adj):correlations[idx]['BH_q']=float(min(q,1))
write_csv('requirement_correlations.csv',correlations)
relative=P-P.mean(1,keepdims=True)
relative_pca=PCA().fit(relative);relative_pc=relative_pca.transform(relative)
def fit_summary(a):
    pp=PCA().fit(StandardScaler().fit_transform(a))
    return {'N':len(a),'PC1_percent':float(pp.explained_variance_ratio_[0]*100),'PC1_PC2_percent':float(pp.explained_variance_ratio_[:2].sum()*100)}
sens={'complete_7':fit_summary(P),'half_item_coverage_7':fit_summary(Y[high]),'complete_19':fit_summary(S[complete_sub]),'same_68_participants_7':fit_summary(Y[complete_sub])}
loo=[fit_summary(np.delete(P,i,axis=0))['PC1_percent'] for i in range(n)]
write_csv('PCA_sensitivity.csv',[dict(Analysis=k,**v) for k,v in sens.items()])
# Nonlinear projection is assessed across settings, not selected for appearance.
tsne_records=[];embeddings=[]
for perplexity in [5,15,25]:
 for random_state in [11,29,47]:
    e=TSNE(n_components=2,perplexity=perplexity,init='random',learning_rate='auto',random_state=random_state).fit_transform(z)
    embeddings.append(e)
    tsne_records.append(dict(Perplexity=perplexity,Seed=random_state,Trustworthiness_k5=float(trustworthiness(z,e,n_neighbors=5)),Trustworthiness_k10=float(trustworthiness(z,e,n_neighbors=10)),Pairwise_distance_Spearman=float(spearmanr(pdist(z),pdist(e)).statistic)))
def neighbors(a):
    nb=NearestNeighbors(n_neighbors=11).fit(a).kneighbors(a,return_distance=False)
    return np.array([[j for j in row if j!=i][:10] for i,row in enumerate(nb)])
neigh=[neighbors(e) for e in embeddings]
jaccards=[]
for a in range(len(neigh)):
 for b in range(a+1,len(neigh)):
    jaccards.append(np.mean([len(set(aa)&set(bb))/len(set(aa)|set(bb)) for aa,bb in zip(neigh[a],neigh[b])]))
write_csv('tSNE_sensitivity.csv',tsne_records)
summary={'source':SOURCE.name,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'seed':seed,'N':87,'items':84,'zero_ratings':int((X==0).sum()),'complete_7':n,'complete_19':int(complete_sub.sum()),'PCA_variance_percent':(pca.explained_variance_ratio_*100).tolist(),'PCA_PC1_CI_percent':(np.quantile(boot_var,[.025,.975])*100).tolist(),'PC1_overall_mean_Spearman':float(spearmanr(pc[:,0],overall).statistic),'parallel_observed_eigenvalues':pca.explained_variance_.tolist(),'parallel_95_eigenvalues':parallel95.tolist(),'correlation_range':[float(min(r['Spearman_rho'] for r in correlations)),float(max(r['Spearman_rho'] for r in correlations))],'correlation_pair_N_range':[min(r['N'] for r in correlations),max(r['N'] for r in correlations)],'correlation_BH_significant':sum(r['BH_q']<.05 for r in correlations),'relative_PCA_variance_percent':(relative_pca.explained_variance_ratio_*100).tolist(),'sensitivity':sens,'PCA_trustworthiness_k10':float(trustworthiness(z,pc[:,:2],n_neighbors=10)),'tSNE_trustworthiness_k10_range':[min(r['Trustworthiness_k10'] for r in tsne_records),max(r['Trustworthiness_k10'] for r in tsne_records)],'tSNE_neighbor_Jaccard_mean':float(np.mean(jaccards)),'tSNE_neighbor_Jaccard_range':[float(min(jaccards)),float(max(jaccards))],'software':{'Python':sys.version.split()[0],'NumPy':np.__version__,'SciPy':scipy.__version__,'scikit-learn':sklearn.__version__,'Matplotlib':matplotlib.__version__},'interpretation':'PCA is descriptive of observed importance profiles, not latent-trait validation. Zero-coded non-relevance is never imputed as importance. Complete-case selection defines the PCA target sample. No clusters or causal/demographic effects are inferred from embeddings.'}
(OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2))
summary['leave_one_out_PC1_percent_range']=[float(min(loo)),float(max(loo))]
(OUT/'analysis_summary.json').write_text(json.dumps(summary,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})

# Figure 11: Relevance and importance as distinct observed judgements.
fig,axes=plt.subplots(1,2,figsize=(12,5.5))
for ax,records,title in zip(axes,[main_summary,sub_summary],['A  Requirements','B  Subcategories']):
    for r in records:
        x,y=r['Relevant_percent'],r['Importance'];color=COLORS[r['Parent']]
        ax.scatter(x,y,color=color,s=48,edgecolor='white',linewidth=.6,zorder=3)
    # Place code labels on an expanded radial layout, linked to the observations.
    center=np.array([np.mean([r['Relevant_percent'] for r in records]),np.mean([r['Importance'] for r in records])])
    for i,r in enumerate(records):
        code='RFPR' if r['Code']=='PFPR' else r['Code']
        offsets={'HAA':(-26,12),'HO':(-25,-4),'RAS':(-30,14),'GS':(0,-18),'A':(-12,-7),'PFPR':(-34,12),'PR':(8,8),'DG':(7,7),'TRC':(0,18),'EXP':(7,-14),'COM':(8,8),'AUB':(8,8),'AUD':(8,8),'SP':(8,-5),'EWB':(-30,-8),'IWS':(8,-10),'ISLD':(8,8),'AU':(5,19),'RM':(6,-20)}
        off=offsets.get(r['Code'],(8,8)) if len(records)>7 else (8,8)
        ax.annotate(code,(r['Relevant_percent'],r['Importance']),xytext=off,textcoords='offset points',fontsize=9,color=COLORS[r['Parent']],fontweight='bold',arrowprops=dict(arrowstyle='-',color=COLORS[r['Parent']],lw=.65))
    ax.set_title(title,loc='left',fontweight='bold');ax.set_xlabel('Relevant item responses (%)');ax.set_ylabel('Conditional mean importance score');ax.grid(alpha=.12);ax.margins(x=.25,y=.2)
fig.tight_layout();savefig(fig,'CEAI_Fig11_Relevance_Importance')

# Figure 12: transparent primary profile analysis.
fig,axes=plt.subplots(2,2,figsize=(12,10),gridspec_kw={'height_ratios':[1.2,1]})
ax=axes[0,0];im=ax.imshow(R,vmin=-1,vmax=1,cmap='RdBu_r')
ax.set_xticks(range(7),main,rotation=45,ha='right');ax.set_yticks(range(7),main)
for i in range(7):
 for j in range(7):ax.text(j,i,f'{R[i,j]:.2f}',ha='center',va='center',fontsize=9,color='white' if abs(R[i,j])>.6 else '#20262E')
ax.set_title('A  Requirement associations',loc='left',fontweight='bold');fig.colorbar(im,ax=ax,shrink=.8,label='Spearman correlation')
ax=axes[0,1];im=ax.scatter(pc[:,0],pc[:,1],c=overall,cmap='viridis',s=38,edgecolor='white',linewidth=.5)
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)');ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)');ax.set_title(f'B  Participant profiles (n = {n})',loc='left',fontweight='bold');fig.colorbar(im,ax=ax,shrink=.8,label='Mean across seven requirements')
ax=axes[1,0];pos=np.arange(7)
ax.barh(pos-.16,loadings[:,0],height=.3,label='PC1',color='#0072B2');ax.barh(pos+.16,loadings[:,1],height=.3,label='PC2',color='#D55E00')
ax.set_yticks(pos,main);ax.invert_yaxis();ax.axvline(0,color='gray',lw=.7);ax.set_xlim(-1,1);ax.set_xlabel('Correlation loading');ax.legend(frameon=False,ncol=2);ax.set_title('C  Requirement contributions',loc='left',fontweight='bold')
ax=axes[1,1];ax.plot(range(1,8),pca.explained_variance_,'o-',label='Observed',color='#0072B2');ax.plot(range(1,8),parallel95,'s--',label='95th percentile: permuted data',color='#888888')
ax.set_xlabel('Component');ax.set_ylabel('Eigenvalue');ax.set_xticks(range(1,8));ax.legend(frameon=False,fontsize=9);ax.set_title('D  Parallel analysis (2,000 permutations)',loc='left',fontweight='bold')
fig.tight_layout(pad=2);savefig(fig,'CEAI_Fig12_Requirement_Profile_Structure')

# Supplement: predetermined central t-SNE specification, not a visually selected run.
embedding=embeddings[3] # perplexity=15, seed=11
fig,axes=plt.subplots(1,3,figsize=(14,4.2))
ax=axes[0];im=ax.scatter(embedding[:,0],embedding[:,1],c=overall,cmap='viridis',s=35);fig.colorbar(im,ax=ax,label='Overall importance',shrink=.8);ax.set_title('A  Overall importance')
for ax,key,title in [(axes[1],'Institution','B  Institutional affiliation'),(axes[2],'Relation','C  Relationship to EduGenZ')]:
    for k,level in enumerate(sorted(set(meta[key][complete]))):
        ok=meta[key][complete]==level
        ax.scatter(embedding[ok,0],embedding[ok,1],s=35,label=level,color=plt.get_cmap('tab10')(k))
    ax.set_title(title);ax.legend(frameon=False,fontsize=8,loc='best')
for ax in axes:ax.set_xlabel('t-SNE 1');ax.set_ylabel('t-SNE 2');ax.set_xticks([]);ax.set_yticks([])
fig.tight_layout();savefig(fig,'CEAI_Supplement_tSNE_Profiles')

fig,axes=plt.subplots(1,2,figsize=(11,4.3))
im=axes[0].scatter(relative_pc[:,0],relative_pc[:,1],c=overall,cmap='viridis',s=35);fig.colorbar(im,ax=axes[0],label='Overall importance')
axes[0].set_xlabel(f'PC1 ({relative_pca.explained_variance_ratio_[0]*100:.1f}%)');axes[0].set_ylabel(f'PC2 ({relative_pca.explained_variance_ratio_[1]*100:.1f}%)');axes[0].set_title('A  Within-participant centred profiles')
pos=np.arange(7);axes[1].barh(pos-.16,relative_pca.components_[0],height=.3,label='PC1',color='#0072B2');axes[1].barh(pos+.16,relative_pca.components_[1],height=.3,label='PC2',color='#D55E00');axes[1].set_yticks(pos,main);axes[1].invert_yaxis();axes[1].axvline(0,color='gray',lw=.7);axes[1].set_xlabel('Component coefficient');axes[1].legend(frameon=False);axes[1].set_title('B  Relative-priority contrasts')
fig.tight_layout();savefig(fig,'CEAI_Supplement_Relative_Priorities')
print(json.dumps(summary,indent=2))
