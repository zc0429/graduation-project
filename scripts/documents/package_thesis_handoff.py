"""Package reviewed local artifacts; never pushes, merges, or copies credentials."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import subprocess,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/handoff'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    status={'generated_at':datetime.datetime.now().astimezone().isoformat(),'worktree':str(ROOT),'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'origin_dev':git('rev-parse','origin/dev'),'origin_main':git('rev-parse','origin/main'),'ahead_behind_dev':git('rev-list','--left-right','--count','origin/dev...HEAD'),'main_dev':git('rev-list','--left-right','--count','origin/main...origin/dev'),'tracked_uncommitted':git('status','--porcelain'),'availability':'local committed, not pushed; archive and incremental bundle local only'}
    assert status['branch']=='codex/thesis-finalization-20260920'
    assert not status['tracked_uncommitted'],status['tracked_uncommitted']
    assert status['origin_dev']=='3b7fc4768e4a2588583f109133d378a050da8733'
    bundle=OUT/'thesis-20260920.bundle'
    subprocess.run(['git','bundle','create',str(bundle),'origin/dev..HEAD'],cwd=ROOT,check=True)
    verified=subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
    status['bundle_verify']=verified.stdout+verified.stderr
    (OUT/'LOCAL-STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    paths=[ROOT/'AGENTS.md',ROOT/'README.md',ROOT/'docs/notes/HANDOFF.md',ROOT/'docs/notes/进度记录.md',ROOT/'docs/thesis/毕业论文.md',ROOT/'docs/thesis/答辩逐页讲稿.md',ROOT/'docs/thesis/答辩追问要点.md',ROOT/'output/docx/论文审阅版.docx',ROOT/'output/pdf/论文审阅版.pdf',ROOT/'output/pptx/答辩审阅版.pptx',OUT/'LOCAL-STATUS.json',bundle]
    paths+=[ROOT/'.gitattributes']
    paths+=list((ROOT/'docs/notes/thesis-run-20260920').glob('*'))
    paths+=[p for p in (ROOT/'docs/notes/thesis-run-20260920/mock-demo-20260921').rglob('*') if p.is_file()]
    paths+=[ROOT/'scripts/documents/verify_docx_offline.py']
    paths+=[p for p in (ROOT/'scripts/documents/schemas/dublincore').rglob('*') if p.is_file()]
    paths+=[p for p in (ROOT/'docs/thesis/figures').rglob('*') if p.is_file()]
    paths+=[ROOT/'scripts/documents'/name for name in ['build_thesis_review.py','build_defense.mjs','verify_thesis_review.py','align_thesis_review.py','inspect_thesis_materials.py','record_thesis_audit.py','package_thesis_handoff.py']]
    paths=sorted(set(p for p in paths if p.is_file()))
    assert not any('.env' in p.parts or 'node_modules' in p.parts or 'materials' in p.parts for p in paths)
    # Extracted school source texts are provenance records, not raw school documents.
    manifest=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
    mp=OUT/'PACKAGE-MANIFEST.json';mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=OUT/'毕设审阅与交接包-20260921.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED) as z:
        for p in paths+[mp]:z.write(p,p.relative_to(ROOT).as_posix())
    with ZipFile(archive) as z:
        assert z.testzip() is None
        for item in manifest:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    (OUT/'ARCHIVE-SHA256.txt').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'files':len(manifest)+1,'head':status['head'],'status':status['tracked_uncommitted']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
