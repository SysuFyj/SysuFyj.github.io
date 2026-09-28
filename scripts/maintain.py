from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urljoin, urlsplit
import json,re,html,hashlib,subprocess,collections
from markdownify import markdownify
ROOT=Path(__file__).resolve().parents[1]
META={x['slug']:x for x in json.loads((ROOT/'scripts/catalog-data.json').read_text())}
def soupfile(p):return BeautifulSoup(p.read_text(),'html.parser')
def fragment(s):return BeautifulSoup(s,'html.parser')
def inner(el,s):
 el.clear()
 for node in list(fragment(s).contents):el.append(node)
def url(p):return '/'+quote(str(p.relative_to(ROOT).parent))+'/'
def save(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(str(s).replace('© \n','©\n').rstrip()+'\n')
# Repair the deployed HTML without moving any existing page.
for p in sorted(ROOT.rglob('*.html')):
 if any(x in p.parts for x in ['content','vendor']):continue
 s=soupfile(p)
 if not s.html:continue
 s.html['lang']='zh-CN'
 for el in s.select('[lang="en"]'):el['lang']='zh-CN'
 if s.body:s.body['class']=[x for x in s.body.get('class',[]) if x!='use-motion']
 for el in s.select('[href],[src],[content]'):
  for attr in ['href','src','content']:
   if attr not in el.attrs:continue
   v=el[attr].replace('http://example.com','https://sysufyj.github.io').replace('https://example.com','https://sysufyj.github.io')
   v=v.replace('/./../images/','/images/')
   if v.endswith('1059190%E3%80%91'):v=v.replace('%E3%80%91','')
   el[attr]=v
 for sc in s.select('script.next-config'):
  data=json.loads(sc.string)
  if isinstance(data,dict):
   if 'hostname' in data:
    data['hostname']='sysufyj.github.io';data['motion']['enable']=False
    data['i18n'].update(placeholder='搜索文章…',empty='没有找到相关内容：${query}',hits='找到 ${hits} 篇文章')
   if 'lang' in data:data['lang']='zh-CN'
   sc.string=json.dumps(data,ensure_ascii=False,separators=(',',':'))
 for el in s.select('script[src],link[href]'):
  attr='src' if el.name=='script' else 'href';v=el.get(attr,'')
  if 'cdnjs.cloudflare.com' in v:
   name=v.rsplit('/',1)[-1];el[attr]='/vendor/fontawesome/css/all.min.css' if name=='all.min.css' else '/vendor/'+name
 if not s.select_one('script[src="/js/blog-maintenance.js"]'):
  s.body.append(fragment('<script defer src="/js/blog-maintenance.js"></script>'))
 for tracking in s.select('script[src*="busuanzi.ibruce.info"]'):tracking.decompose()
 # No-JS reading and slow network should still show the article.
 if not s.select_one('link[href="/css/blog-maintenance.css"]'):
  s.head.append(fragment('<link rel="stylesheet" href="/css/blog-maintenance.css">'))
 labels={'Home':'首页','Archives':'时间归档','Categories':'分类','Tags':'标签','Search':'搜索'}
 for a in s.select('.menu-item a'):
  for node in list(a.find_all(string=True,recursive=False)):
   if node.strip() in labels:node.replace_with(labels[node.strip()])
 menu=s.select_one('.main-menu')
 if menu and not menu.select_one('a[href="/library/"]'):
  menu.append(fragment('<li class="menu-item"><a href="/library/">主题归档</a></li><li class="menu-item"><a href="/paper-notes/">论文笔记</a></li>'))
 for e in s.select('.site-state-item-name'):
  e.string={'posts':'文章','categories':'分类','tags':'标签'}.get(e.get_text(),e.get_text())
 tagstat=s.select_one('.site-state-tags')
 if tagstat and not tagstat.a:
  a=s.new_tag('a',href='/tags/');nodes=list(tagstat.contents)
  for n in nodes:a.append(n.extract())
  tagstat.append(a)
 for e in s.select('.search-input'):e['placeholder']='搜索文章…';e['aria-label']='搜索文章'
 for e in s.select('.popup-btn-close'):e['aria-label']='关闭搜索';e['tabindex']='0'
 for e in s.select('[role="button"]'):e['tabindex']='0'
 for e in s.select('.sidebar-nav-toc'):e.string='文章目录'
 for e in s.select('.sidebar-nav-overview'):e.string='站点概览'
 for e in s.select('.post-body p'):
  if e.get_text(strip=True)=='[TOC]':e.decompose()
 for e in s.select('.post-body img[src*="memory-hierarchy-in-gpus-1.png"]'):
  e.replace_with(fragment('<span class="missing-asset" role="note">原笔记配图缺失：GPU 内存层级图（memory-hierarchy-in-gpus-1.png）。待补回原图。</span>'))
 for e in s.select('meta[property="og:image"]'):
  if 'memory-hierarchy-in-gpus-1.png' in e.get('content',''):e.decompose()
 replacements={'W1,b1W_1, b_1W1,b1':'W₁, b₁','W2,b2W_2, b_2W2,b2':'W₂, b₂','dmodeld_{\\text{model}}dmodel':'d_model','WqW_qWq':'W_q','NhpN_{\\text{hp}}Nhp':'N_hp','rrr：':'r：'}
 for node in list(s.select_one('.main-inner').find_all(string=True)) if s.select_one('.main-inner') else []:
  if node.parent.name in ['script','code','pre']:continue
  v=str(node)
  for a,b in replacements.items():v=v.replace(a,b)
  if v!=str(node):node.replace_with(v)
 for e in s.select('.post-body p'):
  if e.get_text(strip=True) in ['代码：https: //github.com/SJTU-IPADS/reef','代码：https://github.com/SJTU-IPADS/reef']:
   inner(e,'代码：<a href="https://github.com/SJTU-IPADS/reef" target="_blank" rel="noopener">REEF 源码</a>')
  if e.get_text(strip=True)=='categories:' and e.find_next_sibling('ul'):
   ul=e.find_next_sibling('ul');ul.decompose()
   inner(e,'<pre><code class="language-yaml">categories:\n  - [论文, 大模型]\ntags:\n  - 调度系统\n  - 科研\n  - 大模型</code></pre>');e.unwrap()
 for e in s.select('.post-body a[href$="1059190"]'):e.string=e.get_text().rstrip('】')
 if p.parent.name in META and p.parts[-5].isdigit():
  m=META[p.parent.name]
  for e in s.select('meta[name="description"],meta[property="og:description"]'):e['content']=m['summary']
 save(p,s)
# Collect from actual post pages, not paginated excerpts.
posts=[]
for p in sorted(ROOT.glob('20*/*/*/*/index.html')):
 s=soupfile(p);m=dict(META[p.parent.name]);body=s.select_one('.post-body')
 m.update(title=s.select_one('.post-title').get_text(' ',strip=True),url=url(p),date=s.select_one('time[itemprop~="dateCreated"]')['datetime'][:10],path=str(p.relative_to(ROOT)),original_categories=[a.get_text(strip=True) for a in s.select('[itemprop="about"] a')],original_tags=[a.get_text(strip=True).removeprefix('#').strip() for a in s.select('.post-tags a')],headings=[h.get_text(' ',strip=True) for h in body.select('h1,h2,h3,h4,h5,h6')],image_count=len(body.select('img')))
 updated=s.select_one('time[itemprop="dateModified"]');m['updated']=updated['datetime'][:10] if updated else m['date']
 # Record original asset references (including missing ones) for recovery.
 try:
  original=subprocess.check_output(['git','show','origin/main:'+m['path']],cwd=ROOT,text=True)
 except subprocess.CalledProcessError:
  # New posts have no counterpart in the pre-publication origin/main snapshot.
  original=p.read_text()
 m['original_html_sha256']=hashlib.sha256(original.encode()).hexdigest()
 ob=fragment(original).select_one('.post-body')
 m['original_images']=[i['src'] for i in ob.select('img')] if ob else []
 cats=[a.get_text(strip=True) for a in s.select('.post-meta-item a[rel="index"]')]
 if not cats:
  cats=[e.get_text(strip=True) for e in s.select('[itemprop="about"] [itemprop="name"]')]
 m['original_categories']=cats
 posts.append(m)
posts.sort(key=lambda p:(p['date'],p['title']),reverse=True)
(ROOT/'content/catalog.json').write_text(json.dumps(posts,ensure_ascii=False,indent=2)+'\n')
# Short, authored homepage excerpts.
byurl={p['url']:p for p in posts}
for p in [ROOT/'index.html',ROOT/'page/2/index.html']:
 s=soupfile(p)
 for article in s.select('article'):
  a=article.select_one('.post-title a');b=article.select_one('.post-body')
  if a and b and a['href'] in byurl:
   m=byurl[a['href']];inner(b,'<p>'+html.escape(m['summary'])+'</p><div class="post-button"><a class="btn" href="'+m['url']+'">阅读全文 »</a></div>')
 save(p,s)
def card(m):
 return f'<li class="archive-entry"><div class="archive-date">{m["date"]} · {html.escape(m["topic"])}</div><h3><a href="{m["url"]}">{html.escape(m["title"])}</a></h3><p>{html.escape(m["summary"])}</p><p class="archive-keywords">{html.escape(" · ".join(m["keywords"]))}</p></li>'
def page(path,title,body):
 s=soupfile(ROOT/'categories/index.html');s.title.string=title+' | Ringo的博客'
 s.select_one('.post-title').string=title;inner(s.select_one('.post-body'),body)
 for el in s.select('meta[name="description"],meta[property="og:description"]'):el['content']=fragment(body).get_text(' ',strip=True)[:140]
 absolute='https://sysufyj.github.io/'+path+'/'
 s.select_one('link[rel="canonical"]')['href']=absolute
 for el in s.select('meta[property="og:url"]'):el['content']=absolute
 for el in s.select('meta[property="og:title"]'):el['content']=title
 for sc in s.select('script.next-config[data-name="page"]'):
  data=json.loads(sc.string);data.update(title=title,path=path+'/index.html',permalink=absolute,isHome=False,isPost=False);sc.string=json.dumps(data,ensure_ascii=False)
 save(ROOT/path/'index.html',s)
topics=list(dict.fromkeys(x['topic'] for x in META.values()))
years=collections.Counter(m['date'][:4] for m in posts)
year_text='、'.join(f'{year} 年 {count} 篇' for year,count in sorted(years.items()))
body=f'<p class="archive-intro">这里收录了 {year_text}，共 {len(posts)} 篇文章，按 {len(topics)} 个主题整理。也可以查看<a href="#by-time">完整时间线</a>。</p><nav class="topic-links" aria-label="主题导航">'
for i,t in enumerate(topics):body+=f'<a href="#topic-{i}">{t} · {sum(m["topic"]==t for m in posts)}</a>'
body+='</nav>'
for i,t in enumerate(topics):body+=f'<section id="topic-{i}"><h2>{t}</h2><ul class="archive-entries">'+''.join(card(m) for m in posts if m['topic']==t)+'</ul></section>'
body+='<section id="by-time"><h2>完整时间线</h2><ul class="archive-timeline">'+''.join(f'<li><time>{m["date"]}</time> <a href="{m["url"]}">{html.escape(m["title"])}</a></li>' for m in posts)+'</ul></section>'
page('library','主题归档',body)
papers=[p for p in posts if '论文' in p['original_categories']]
paper_topics=collections.Counter(p['topic'] for p in papers)
paper_summary='、'.join(f'{topic} {count} 篇' for topic,count in paper_topics.items())
page('paper-notes','论文笔记',f'<p>{len(papers)} 篇研究论文笔记：{paper_summary}。<a href="/library/">查看全部主题</a>。</p><ul class="archive-entries">'+''.join(card(p) for p in papers)+'</ul>')
tags=collections.Counter(t for p in posts for t in p['original_tags'])
page('tags','标签','<p>按原有标签浏览文章，共 '+str(len(tags))+' 个标签。</p><ul class="tag-directory">'+''.join(f'<li><a href="/tags/{quote(t)}/">{html.escape(t)}</a><span>{n} 篇</span></li>' for t,n in sorted(tags.items(),key=lambda x:(-x[1],x[0])))+'</ul><p>尚未设置标签的文章也都收录在<a href="/library/">主题归档</a>中。</p>')
# Independent Markdown recovery copies: rendered pages remain authoritative.
md=['# 博客归档总目','', f'归档日期：2026-09-28。共 {len(posts)} 篇：{year_text}。', '', '这些 Markdown 是由已发布 HTML 恢复的阅读副本，不是遗失的 Hexo 原稿。原始网页和全部 Git 历史另有备份。分类依据实际内容；原分类、标签、日期和链接均保留在 catalog.json。', '']
for topic in topics:
 md+=['## '+topic,'']
 for m in posts:
  if m['topic']!=topic:continue
  name=m['date']+'-'+m['slug']+'.md';mfile=ROOT/'content/posts'/name
  b=soupfile(ROOT/m['path']).select_one('.post-body')
  for f in b.select('figure.highlight'):
   code=f.select_one('td.code pre');pre=fragment('<pre><code></code></pre>');pre.code.string=code.get_text() if code else f.get_text();f.replace_with(pre)
  for a in b.select('a.headerlink'):a.decompose()
  for el in b.select('[src],[href]'):
   for at in ['src','href']:
    if at in el.attrs and el[at].startswith('/'):
     el[at]='../../'+unquote(el[at]).lstrip('/')
  recovered=markdownify(str(b),heading_style='ATX')
  mfile.write_text('# '+m['title']+'\n\n'+f'发布时间：{m["date"]}  \n最后更新：{m["updated"]}  \n归档主题：{m["topic"]}  \n原文：https://sysufyj.github.io{m["url"]}\n\n> 从网页恢复的阅读副本；非 Hexo 原始 Markdown。\n\n'+recovered+'\n')
  md += [f'### {m["date"]} · {m["title"]}','',m['summary'],'',f'- [原网页](https://sysufyj.github.io{m["url"]}) · [本地阅读副本](../content/posts/{quote(name)})',f'- 关键词：{"、".join(m["keywords"])}',f'- 原分类：{" / ".join(m["original_categories"]) or "未分类"}；原标签：{"、".join(m["original_tags"]) or "无"}',f'- 更新日期：{m["updated"]}；现存配图：{m["image_count"]} 张',f'- 归档备注：{m["note"]}','- 章节：'+' → '.join(m['headings']),'']
(ROOT/'docs/博客归档总目.md').write_text('\n'.join(md)+'\n')
# Refresh the search database so summaries and corrected text agree with pages.
import xml.etree.ElementTree as ET
search=ET.Element('search')
for m in posts:
 entry=ET.SubElement(search,'entry');ET.SubElement(entry,'title').text=m['title'];ET.SubElement(entry,'url').text=m['url'];ET.SubElement(entry,'content',{'type':'html'}).text=str(soupfile(ROOT/m['path']).select_one('.post-body'))
ET.ElementTree(search).write(ROOT/'search.xml',encoding='utf-8',xml_declaration=True)
print(f'Archived {len(posts)} posts, {len(tags)} tags, {len(papers)} papers.')
