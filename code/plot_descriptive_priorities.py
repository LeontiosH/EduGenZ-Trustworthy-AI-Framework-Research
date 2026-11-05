from pathlib import Path
import json, textwrap, zipfile, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/descriptive'
OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((ROOT/'results/descriptive/results.json').read_text())
colors=dict(zip(['HAO','TRS','PDG','TPR','DnDF','SEW','ACC'],['#0072B2','#E69F00','#009E73','#CC79A7','#56B4E9','#D55E00','#6B6B6B']))
parent={}
for group,codes in {'HAO':['HAA','HO'],'TRS':['RAS','GS','A','PFPR'],'PDG':['PR','DG'],'TPR':['TRC','EXP','COM'],'DnDF':['AUB','AUD','SP'],'SEW':['EWB','IWS','ISLD'],'ACC':['AU','RM']}.items():
    parent.update({code:group for code in codes})
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
for key,stem,height in [('Requirements','CEAI_Requirement_Priorities_Corrected',6),('Subcategories','CEAI_Subcategory_Priorities_Corrected',11)]:
    records=sorted(data[key],key=lambda r:r['Mean'],reverse=True)
    fig,ax=plt.subplots(figsize=(12,height))
    fig.subplots_adjust(left=.405,right=.965,top=.98,bottom=.19 if key=='Requirements' else .115)
    y=np.arange(len(records));means=np.array([r['Mean'] for r in records])
    lo=np.array([r['CI_lower'] for r in records]);hi=np.array([r['CI_upper'] for r in records])
    c=[colors[r['Code'] if key=='Requirements' else parent[r['Code']]] for r in records]
    ax.barh(y,means,color=c,height=.60,edgecolor='white',linewidth=.4,zorder=2)
    ax.errorbar(means,y,xerr=np.vstack([means-lo,hi-means]),fmt='none',ecolor='#20262E',elinewidth=1.3,capsize=3,capthick=1.2,zorder=3)
    labels=[]
    for r in records:
        code='RFPR' if r['Code']=='PFPR' else r['Code']
        labels.append(textwrap.fill(f"{r['Name']} ({code})",width=43))
    ax.set_yticks(y,labels,fontsize=11)
    ax.tick_params(axis='y',length=0,pad=10)
    ax.invert_yaxis();ax.set_xlim(0,10);ax.set_xticks(range(0,11,1))
    ax.set_xlabel('Mean importance score',labelpad=8)
    ax.grid(axis='x',color='#DDE2E7',linewidth=.6,zorder=0)
    ax.set_axisbelow(True);ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#9AA3AD')
    for i,r in enumerate(records):
        ax.text(r['CI_upper']+.13,i,f"{r['Mean']:.2f}",ha='left',va='center',fontsize=11,fontweight='semibold')
    legend=[Patch(facecolor=colors[g],label=g) for g in colors]
    fig.legend(handles=legend,loc='lower center',ncol=7,frameon=False,bbox_to_anchor=(.61,.025 if key=='Requirements' else .018),fontsize=10,handlelength=1.2,columnspacing=1.15)
    for ext in ['png','pdf','svg']:
        fig.savefig(OUT/(stem+'.'+ext),dpi=300,facecolor='white')
    plt.close(fig)
captions=r'''% Requires \usepackage{graphicx}. Place each figure in its corresponding results subsection.
\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{CEAI_Requirement_Priorities_Corrected.pdf}
\caption{Mean perceived importance of the seven trustworthiness requirements, ordered by mean score. Error bars show 95\% percentile confidence intervals from 50,000 participant-level bootstrap resamples. Zero-coded non-relevance judgements were excluded, and means were multiplied by $10/3$ (possible range: approximately 3.33--10). HAO: human agency and oversight; TRS: technical robustness and safety; PDG: privacy and data governance; TPR: transparency; DnDF: diversity, non-discrimination and fairness; SEW: societal and environmental well-being; ACC: accountability.}
\label{fig:requirement-priorities}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\linewidth]{CEAI_Subcategory_Priorities_Corrected.pdf}
\caption{Mean perceived importance of the nineteen trustworthiness subcategories, ordered by mean score. Colours identify the parent requirements using the same scheme as Figure~\ref{fig:requirement-priorities}. Error bars show 95\% percentile confidence intervals from 50,000 participant-level bootstrap resamples. Zero-coded non-relevance judgements were excluded, and means were multiplied by $10/3$ (possible range: approximately 3.33--10).}
\label{fig:subcategory-priorities}
\end{figure}

% Example references in the manuscript:
% Figure~\ref{fig:requirement-priorities} presents the requirement-level priorities.
% Figure~\ref{fig:subcategory-priorities} presents the subcategory-level priorities.
'''
(OUT/'figure_insertions.tex').write_text(captions)
