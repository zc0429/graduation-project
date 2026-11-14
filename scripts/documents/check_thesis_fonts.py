"""Check actual font identities; an installed fallback is never an original.

Default: fail if any required original is absent. --preview explicitly permits
an accurately labelled preview while retaining the missing-font report.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
from fontTools.ttLib import TTFont

REQUIRED={'SimSun':{'SimSun','宋体'},'SimHei':{'SimHei','黑体'},
          'Times New Roman':{'Times New Roman'}}

def inspect():
    result=[]
    for family,accepted in REQUIRED.items():
        match=subprocess.check_output(['fc-match','-f','%{file}\n%{index}\n%{family}\n',family],text=True).splitlines()
        path=Path(match[0]);index=int(match[1] or 0)
        font=TTFont(path,fontNumber=index)
        names={r.toUnicode() for r in font['name'].names if r.nameID in {1,16}}
        result.append({'requested':family,'actual_family_names':sorted(names),
                       'fontconfig_family':match[2],'file':str(path),'font_index':index,
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'version':font['name'].getDebugName(5),
                       'embedding_fsType':font['OS/2'].fsType if 'OS/2' in font else None,
                       'original_available':bool(names & accepted)})
        font.close()
    return {'fonts':result,'all_originals_available':all(r['original_available'] for r in result),
            'microsoft_word_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True)
    p.add_argument('--pdf',type=Path,help='Also verify actual PDF fonts from the selected renderer')
    p.add_argument('--preview',action='store_true');args=p.parse_args()
    report=inspect();report['mode']='font-limited-preview' if args.preview else 'original-required'
    report['missing_originals']=[r['requested'] for r in report['fonts'] if not r['original_available']]
    if args.pdf:
        import fitz
        with fitz.open(args.pdf) as pdf:
            names=sorted({font[3] for page in pdf for font in page.get_fonts()})
        missing=[family for family,key in [('SimSun','SimSun'),('SimHei','SimHei'),
                  ('Times New Roman','TimesNewRoman')] if not any(key in name for name in names)]
        report.update({'actual_pdf_fonts':names,'pdf_missing_originals':missing,
                       'pdf_originals_verified':not missing})
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    missing=sorted(set(report['missing_originals']+report.get('pdf_missing_originals',[])))
    if missing and not args.preview:
        print('Original fonts missing: '+', '.join(missing)+'. No formal PDF was exported. Use --preview only for a labelled preview.',file=sys.stderr)
        raise SystemExit(2)

if __name__=='__main__':main()
