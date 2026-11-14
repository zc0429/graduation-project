"""Use review derivatives; never change retained diagrams or historical evidence."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/thesis/final-master-20261114/figures'
def derivative(target,image,run):
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    if target in manifest:
        return Image.open(BASE/manifest[target]['file']).convert('RGB')
    return image
