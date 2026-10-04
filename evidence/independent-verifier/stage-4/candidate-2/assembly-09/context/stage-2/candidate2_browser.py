"""Own general browser protocol under adopted exact semantic numeric controls."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE/'browser.py').read_text()
old='await page.get_by_test_id("party-size-input").get_attribute("type")=="number"'
assert source.count(old)==1
source=source.replace(old,'await page.get_by_test_id("party-size-input").get_attribute("role")=="spinbutton" and await page.get_by_test_id("party-size-input").get_attribute("inputmode")=="numeric" and await page.get_by_test_id("party-size-input").is_visible()')
out=Path(sys.argv[sys.argv.index('--out')+1]);out.parent.mkdir(parents=True,exist_ok=True)
(out.parent/'general-executed-source.py').write_text(source)
(out.parent/'general-source-binding.json').write_text(json.dumps(dict(original_sha256=hashlib.sha256((HERE/'browser.py').read_bytes()).hexdigest(),executed_sha256=hashlib.sha256(source.encode()).hexdigest(),scope='Full original general flow protocol; only native HTML type assumption replaced with adopted semantic numeric-control expectation. Detailed exact/input/label/keyboard checks are separate real interactions.'),indent=2))
exec(compile(source,str(HERE/'browser.py'),'exec'),{'__name__':'__main__','__file__':str(HERE/'browser.py')})
