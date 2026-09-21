"""Run all DOCX package checks with pinned, offline Dublin Core dependencies."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from functools import lru_cache
from zipfile import ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = Path(__file__).parent / 'schemas/dublincore'


def install_offline_schemas():
    """Patch this process's loader, never the installed skill or source DOCX."""
    from validators import base
    sources = json.loads((SCHEMAS / 'sources.json').read_text(encoding='utf-8'))
    mapping = {}
    for source in sources:
        path = SCHEMAS / source['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Schema checksum mismatch: {path}')
        for host in ('www.dublincore.org', 'dublincore.org'):
            for protocol in ('http', 'https'):
                mapping[f'{protocol}://{host}/schemas/xmls/qdc/2003/04/02/{path.name}'] = path
        for protocol in ('http', 'https'):
            if path.name == 'xml.xsd':
                mapping[f'{protocol}://www.w3.org/2001/03/xml.xsd'] = path

    class LocalResolver(etree.Resolver):
        def resolve(self, url, public_id, context):
            if url in mapping:
                return self.resolve_filename(str(mapping[url]), context)
            if url.startswith(('http:', 'https:')):
                raise ValueError(f'Unmapped external schema: {url}')
            return None

    @lru_cache(maxsize=None)
    def load(schema_path):
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalResolver())
        return etree.XMLSchema(etree.parse(schema_path, parser))

    base._load_schema = load
    return sources


def make_validator(directory, verbose=True):
    from validators import DOCXSchemaValidator
    class PortableValidator(DOCXSchemaValidator):
        def _clean_ignorable_namespaces(self, tree):
            if etree.QName(tree.getroot()).localname == 'chartSpace':
                # CT_Extension accepts foreign payload via xs:any. Removing
                # WPS chartProps would create an invalid empty c:ext.
                mc = {'mc': self.MC_NAMESPACE}
                for alternate in tree.xpath('//mc:AlternateContent', namespaces=mc):
                    fallback = alternate.find('mc:Fallback', mc)
                    if fallback is None:
                        raise ValueError('Chart AlternateContent has no fallback')
                    parent = alternate.getparent()
                    position = parent.index(alternate)
                    for child in list(fallback):
                        parent.insert(position, child)
                        position += 1
                    parent.remove(alternate)
                return tree
            return super()._clean_ignorable_namespaces(tree)

        def _get_schema_path(self, file):
            # Bundled chart/theme matching uses '/' and misses Windows paths.
            if file.parent.name == 'charts' and file.name.startswith('chart'):
                return self.schemas_dir / self.SCHEMA_MAPPINGS['chart']
            if file.parent.name == 'theme' and file.name.startswith('theme'):
                return self.schemas_dir / self.SCHEMA_MAPPINGS['theme']
            if file.parent.name == 'customXml' and file.name.startswith('itemProps'):
                return self.schemas_dir / 'ISO-IEC29500-4_2016/shared-customXmlDataProperties.xsd'
            return super()._get_schema_path(file)
    validator = PortableValidator(Path(directory), None, verbose=verbose)
    validator.IGNORED_VALIDATION_ERRORS = []
    return validator


def main():
    validator_dir = Path(os.environ.get('DOCX_VALIDATOR_DIR') or Path.home() / '.agents/skills/docx/scripts/office')
    sys.path.insert(0, str(validator_dir.resolve()))
    sources = install_offline_schemas()
    docx = ROOT / 'output/docx/论文审阅版.docx'
    report_dir = ROOT / 'docs/notes/thesis-run-20260920'
    before = hashlib.sha256(docx.read_bytes()).hexdigest()
    log = io.StringIO()
    with tempfile.TemporaryDirectory() as temp:
        with ZipFile(docx) as z:
            z.extractall(temp)
        validator = make_validator(temp)
        with contextlib.redirect_stdout(log):
            package_ok = validator.validate()
        parts = []
        for file in validator.xml_files:
            valid, errors = validator._validate_single_file_xsd(file, Path(temp))
            parts.append({'part': file.relative_to(temp).as_posix(),
                          'xsd_valid': valid, 'errors': sorted(errors or [])})
    assert hashlib.sha256(docx.read_bytes()).hexdigest() == before
    report = {'date': '2026-09-21', 'docx_sha256': before, 'package_valid': package_ok,
              'schema_sources': sources, 'parts': parts,
              'xsd_passed': sum(p['xsd_valid'] is True for p in parts),
              'xsd_unmapped': [p['part'] for p in parts if p['xsd_valid'] is None],
              'xsd_failed': [p for p in parts if p['xsd_valid'] is False],
              'scope': 'All package parts retained; no baseline or error allowlist. Bundled MC preprocessing with chart Fallback and extension-payload preservation. Unmapped WPS private data receives package checks only.'}
    (report_dir / 'DOCX-OFFLINE-XSD.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (report_dir / 'DOCX-OFFLINE-XSD.txt').write_text(log.getvalue(), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('package_valid', 'xsd_passed', 'xsd_unmapped', 'xsd_failed')}, ensure_ascii=False))
    return 0 if package_ok and not report['xsd_failed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
