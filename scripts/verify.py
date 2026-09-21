"""Check complete coverage, local links/assets, anchors and original code blocks."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit,urljoin,unquote
from collections import Counter
import json,hashlib,base64,subprocess,xml.etree.ElementTree as ET,re
root=Path(__file__).resolve().parents[1]
files={p:BeautifulSoup(p.read_text(),'html.parser') for p in root.rglob('*.html') if 'content' not in p.relative_to(root).parts}
errors=[];links=0
for p,s in files.items():
 ids=Counter(e['id'] for e in s.select('[id]'))
 if any(n>1 for n in ids.values()):errors.append((str(p),'duplicate ids'))
 for e in s.select('[href],[src]'):
  value=e.get('src',e.get('href'));v=urlsplit(urljoin('https://sysufyj.github.io/'+str(p.relative_to(root)),value))
  if v.netloc!='sysufyj.github.io':continue
  target=root/unquote(v.path).lstrip('/')
  if target.is_dir():target=target/'index.html'
  links+=1
  if not target.exists():errors.append((str(p.relative_to(root)),value,'missing'))
  elif v.fragment and target in files and not files[target].find(id=unquote(v.fragment)):
   errors.append((str(p.relative_to(root)),value,'missing anchor'))
  if e.get('integrity') and target.is_file():
   alg,want=e['integrity'].split('-',1)
   actual=base64.b64encode(hashlib.new(alg,target.read_bytes()).digest()).decode()
   if actual!=want:errors.append((value,'SRI mismatch'))
 if s.html.get('lang')!='zh-CN':errors.append((str(p),'language'))
 if 'use-motion' in s.body.get('class',[]):errors.append((str(p),'hidden before JS'))
 if s.select_one('.post-body') and '[TOC]' in s.select_one('.post-body').get_text():errors.append((str(p),'TOC placeholder'))
for p in root.glob('vendor/**/*.css'):
 for u in re.findall(r'url\(([^)]+)\)',p.read_text()):
  if not (p.parent/u.strip('"\'')).resolve().exists():errors.append((str(p),u))
catalog=json.loads((root/'content/catalog.json').read_text())
assert len(catalog)==11 and len({m['url'] for m in catalog})==11
assert len(list((root/'content/posts').glob('*.md')))==11
assert len(files[root/'library/index.html'].select('.archive-entry'))==11
assert len(files[root/'paper-notes/index.html'].select('.archive-entry'))==6
assert len(files[root/'tags/index.html'].select('.tag-directory li'))==9
assert len(ET.parse(root/'search.xml').getroot().findall('entry'))==11
for m in catalog:
 original=subprocess.check_output(['git','show','origin/main:'+m['path']],cwd=root,text=True)
 assert hashlib.sha256(original.encode()).hexdigest()==m['original_html_sha256']
 old=BeautifulSoup(original,'html.parser');new=files[root/m['path']]
 before=[x.get_text() for x in old.select('figure.highlight td.code pre')]
 after=[x.get_text() for x in new.select('figure.highlight td.code pre')]
 if before!=after:errors.append((m['path'],'code changed'))
 if [x['id'] for x in old.select('.post-body [id]')]!=[x['id'] for x in new.select('.post-body [id]')]:errors.append((m['path'],'article anchors changed'))
 if len(old.select('.post-body img'))-len(new.select('.post-body img'))!=(1 if m['slug']=='cuda基础操作' else 0):errors.append((m['path'],'image count changed'))
result={'html_pages':len(files),'local_references_checked':links,'posts':len(catalog),'recovered_markdown':11,'papers':6,'tags':9,'errors':errors}
print(json.dumps(result,ensure_ascii=False,indent=2))
(root/'docs/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
raise SystemExit(bool(errors))
