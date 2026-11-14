"""Embed only legally installed open-source font subsets in new SVG exports."""
import base64,io,os
from fontTools import subset
from fontTools.ttLib import TTFont

def embed(svg,scene):
 chars=''.join(o.get('text','') for o in scene['ops']);styles=[]
 for family,var in [('DeliveryLatin','THESIS_LATIN_FONT'),('DeliverySong','THESIS_SONG_FONT')]:
  f=TTFont(os.environ[var],fontNumber=0);opt=subset.Options();sub=subset.Subsetter(options=opt);sub.populate(text=chars);sub.subset(f);f.flavor='woff';buf=io.BytesIO();f.save(buf)
  styles.append("@font-face{font-family:'"+family+"';src:url(data:font/woff;base64,"+base64.b64encode(buf.getvalue()).decode()+") format('woff');}")
 svg=svg.replace('Times New Roman, SimSun, serif','DeliveryLatin, DeliverySong, serif')
 return svg.replace('>','><defs><style>'+''.join(styles)+'</style></defs>',1)
