"""CSV adapter preserving the original four-header-row analysis interface."""
from pathlib import Path
import csv

def load_legacy_rows(path):
    path=Path(path)
    with path.open(newline='',encoding='utf-8') as f:
        records=list(csv.DictReader(f))
    with (path.parent/'item_dictionary.csv').open(newline='',encoding='utf-8') as f:
        items=list(csv.DictReader(f))
    rows=[[None]*4+[i['requirement_code'] for i in items],
          [None]*4+[i['subcategory_source_code'] for i in items],
          ['participant_id','institution','project_role','gender']+[i['statement'] for i in items],
          ['participant_id','institution','project_role','gender']+list(range(1,85))]
    for r in records:
        rows.append([r['participant_id'],r['institution'],r['project_role'],r['gender']]+[int(r[i['item_id']]) for i in items])
    return rows
