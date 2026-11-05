"""Run the repository's Python analyses without writing to reference_results."""
from pathlib import Path
import argparse,subprocess,sys,os
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--quick',action='store_true',help='Descriptive estimates and corrected non-parametric comparisons only')
a=p.parse_args()
if not (ROOT/'data/responses.csv').is_file():
    p.exit(2, 'Participant-level data are under embargo and are not included in this public release.\n'
           'See docs/DATA_ACCESS.md. Full reanalysis requires an authorised dataset.\n')

env=os.environ.copy()
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[k]='1'
steps=[('descriptive_analysis.py','descriptive'),('nonparametric_analysis.py','nonparametric')]
if not a.quick:steps += [('extended_analysis.py','extended'),('robustness_analysis.py','robustness'),('student_analysis.py','students')]
for script,out in steps:
    print('Running',script,flush=True)
    subprocess.run([sys.executable,str(ROOT/'code'/script),str(ROOT/'data/responses.csv'),str(ROOT/'results'/out)],check=True,env=env)
subprocess.run([sys.executable,str(ROOT/'code/plot_descriptive_priorities.py')],check=True,env=env)
print('Complete. Outputs are in results/. MATLAB mixed-effects models are a separate step.')
