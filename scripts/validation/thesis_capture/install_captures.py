"""Install reviewed DPR2 captures, keeping original real-GLM evidence untouched."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'docs/validation/thesis-screenshots-20261117'
BASE=ROOT/'docs/thesis/final-master-20261114/figures'
records=json.loads((RUN/'capture-records.json').read_text())
history=json.loads((RUN/'business-history.json').read_text())
manifest=json.loads((BASE/'manifest.json').read_text());entries=[]
for e in records['entries']:
 n=int(e['number'].split('.')[1]);source=ROOT/e['candidate_path'];sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha==e['sha256'] and e['deviceScaleFactor']==2
 if n<=3:
  name={1:'current-create',2:'current-knowledge',3:'current-practice'}[n]
  target=f'align-reference1-20261113/screenshots/{name}.png';dest=ROOT/'docs/thesis'/target
 else:
  target=f'structure-20261112/figures/png/7-{n-2}.png';dest=BASE/f'7-{n}.png'
 shutil.copyfile(source,dest)
 width,height=Image.open(dest).size
 record={k:v for k,v in e.items() if k not in ['candidate_path','text']}
 record.update(file=str(dest.relative_to(ROOT/'docs')),target=target,pixel_width=width,pixel_height=height,model='Archived real GLM outputs, local replay',source_provenance='docs/validation/thesis-screenshots-20261117/business-history.json',original_ai_sources=history['sources'],sha256=sha)
 entries.append(record)
 if n>=4:manifest[target]={'file':dest.name,'number':e['number'],'source':'docs/validation/thesis-screenshots-20261117/capture-records.json','source_sha256':hashlib.sha256((RUN/'capture-records.json').read_bytes()).hexdigest(),'png_sha256':sha,'capture':record,'retained_original_evidence_unchanged':True}
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(ROOT/'docs/thesis/align-reference1-20261113/screenshots/provenance.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print('Installed 8 reviewed DPR2 captures; original historical source PNGs unchanged')
