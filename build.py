#!/usr/bin/env python3
"""Build the entire static site. Python >= 3.10; standard library only."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import html
import json
import math
import posixpath
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET
from email.utils import format_datetime

BASE = Path(__file__).resolve().parent
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ICONS = {
 'arrow':'<path d="M5 12h14m-6-6 6 6-6 6"/>',
 'up':'<path d="M12 19V5m-6 6 6-6 6 6"/>',
 'chevron':'<path d="m9 5 7 7-7 7"/>',
 'external':'<path d="M14 4h6v6m-1-5-9 9M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5"/>',
 'search':'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
 'moon':'<path d="M20.5 13A8.5 8.5 0 0 1 11 3.5 8.5 8.5 0 1 0 20.5 13Z"/>',
 'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M19 5l-1.5 1.5m-11 11L5 19"/>',
 'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
 'close':'<path d="m6 6 12 12M6 18 18 6"/>',
 'sparkles':'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Zm7-2v4m-2-2h4"/>',
 'flask':'<path d="M9 3h6m-5 0v7L5 19a1.3 1.3 0 0 0 1 2h12a1.3 1.3 0 0 0 1-2l-5-9V3M8 14h8"/><path d="M10 17h.01M14 18h.01"/>',
 'code':'<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
 'pen':'<path d="m15 4 5 5M4 20l5-1L21 7a2.1 2.1 0 0 0-4-4L5 15l-1 5Z"/>',
 'book':'<path d="M12 5C8 2 3 3 3 3v16s5-1 9 2c4-3 9-2 9-2V3s-5-1-9 2Zm0 0v16"/>',
 'layers':'<path d="m12 3 10 5-10 5L2 8l10-5ZM2 12l10 5 10-5M2 16l10 5 10-5"/>',
 'grid':'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 'pin':'<path d="m16 3 5 5-3 2-3 5-2-1-6 6m1-11-1-2 5-3 2-3M7 9l8 8"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>',
 'rss':'<path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>',
 'mail':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
 'shield':'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
 'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.01"/>',
 'image':'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 6"/>',
 'text':'<path d="M3 5h18M8 5v14M5 19h6m4-9h6m-3 0v9m-3 0h6"/>',
 'link':'<path d="m10 14 4-4m-6 7-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m4 0 1-1a4 4 0 1 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 -1) scale(.9)"/>',
 'braces':'<path d="M8 3H6a2 2 0 0 0-2 2v4l-2 3 2 3v4a2 2 0 0 0 2 2h2m8-18h2a2 2 0 0 1 2 2v4l2 3-2 3v4a2 2 0 0 1-2 2h-2"/>',
 'check':'<path d="m4 12 5 5L20 6"/>',
}
TOOLS = [
 {'id':'json','title':'JSON 格式化','description':'格式化、压缩与语法检查，让结构化数据更易阅读。','icon':'braces','color':'blue'},
 {'id':'timestamp','title':'时间戳转换','description':'秒、毫秒与带时区日期互转，明确区分 UTC 和本地时间。','icon':'clock','color':'purple'},
 {'id':'words','title':'字数统计','description':'统计汉字、英文单词与字符数量，边写边看。','icon':'text','color':'green'},
 {'id':'url','title':'URL 编码解码','description':'对单个 URL 参数进行百分号编码，或还原编码内容。','icon':'link','color':'orange'},
 {'id':'base64','title':'Base64 编码解码','description':'支持中文的 UTF-8 文本与 Base64 编码转换。','icon':'code','color':'purple'},
 {'id':'image','title':'图片压缩与转换','description':'本地调整尺寸、质量与格式，支持 JPG、PNG、WebP。','icon':'image','color':'blue'},
]

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)

def icon(name: str, extra: str = '') -> str:
    return f'<svg class="icon {esc(extra)}" aria-hidden="true"><use href="#i-{esc(name if name in ICONS else "book")}"></use></svg>'

def safe_url(value: str) -> str:
    value=html.unescape(value).strip()
    p=urlsplit(value)
    if p.scheme and p.scheme.lower() not in ('https','http','mailto'):
        return '#'
    if value.startswith('//') or any(ord(c)<32 for c in value):
        return '#'
    return value

def inline(text: str) -> str:
    """A deliberately small, safe Markdown subset. Raw HTML is escaped."""
    tokens: list[str] = []
    def protect(match: re.Match) -> str:
        tokens.append('<code>'+esc(match.group(1))+'</code>')
        return f'\x00CODE{len(tokens)-1}\x00'
    text=re.sub(r'`([^`\n]+)`',protect,text)
    text=esc(text)
    text=re.sub(r'\[([^\]\n]+)\]\(([^\s)]+)\)',lambda m:f'<a href="{esc(safe_url(m.group(2)))}">{m.group(1)}</a>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)',r'<em>\1</em>',text)
    for i,value in enumerate(tokens):text=text.replace(f'\x00CODE{i}\x00',value)
    return text

def markdown(text: str) -> tuple[str,list[tuple[str,str]]]:
    lines=text.replace('\r\n','\n').splitlines(); result=[]; toc=[]; i=0; number=0
    def structural(s: str)->bool:
        return bool(re.match(r'^(#{1,6}\s|```|>\s?|[-*]\s|\d+\.\s)',s))
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('```'):
            lang=line[3:].strip() or 'text';i+=1;code=[]
            while i<len(lines) and not lines[i].strip().startswith('```'):code.append(lines[i]);i+=1
            i+=1
            code_text=esc('\n'.join(code))
            result.append(f'<div class="code-wrap"><div class="code-header"><span>{esc(lang)}</span><button type="button" class="copy-code" aria-label="复制代码">复制代码</button></div><pre><code>{code_text}</code></pre></div>');continue
        h=re.match(r'^(#{1,6})\s+(.+)$',line)
        if h:
            level=max(2,len(h.group(1)));number+=1;anchor=f'section-{number}'
            result.append(f'<h{level} id="{anchor}">{inline(h.group(2))}</h{level}>')
            if level==2:toc.append((anchor,h.group(2)))
            i+=1;continue
        if i+1<len(lines) and '|' in line and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):
            heads=line.strip('|').split('|');i+=2;rows=[]
            while i<len(lines) and '|' in lines[i] and lines[i].strip():
                rows.append(lines[i].strip().strip('|').split('|'));i+=1
            result.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(h.strip())+'</th>' for h in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v.strip())+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>');continue
        if line.startswith('>'):
            q=[]
            while i<len(lines) and lines[i].strip().startswith('>'):q.append(lines[i].strip()[1:].lstrip());i+=1
            result.append('<blockquote><p>'+inline(' '.join(q))+'</p></blockquote>');continue
        if re.match(r'^([-*]|\d+\.)\s+',line):
            ordered=bool(re.match(r'^\d+\.',line));tag='ol' if ordered else 'ul';items=[]
            pattern=r'^\d+\.\s+' if ordered else r'^[-*]\s+'
            while i<len(lines) and re.match(pattern,lines[i].strip()):items.append(re.sub(pattern,'',lines[i].strip()));i+=1
            result.append(f'<{tag}>'+''.join('<li>'+inline(x)+'</li>' for x in items)+f'</{tag}>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not structural(lines[i].strip()):
            if i+1<len(lines) and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):break
            para.append(lines[i].strip());i+=1
        result.append('<p>'+inline(' '.join(para))+'</p>')
    return '\n'.join(result),toc

def parse_post(path: Path)->dict:
    raw=path.read_text(encoding='utf-8-sig')
    match=re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)\Z',raw,re.S)
    if not match:raise ValueError(f'{path.name}: 缺少 JSON front matter（--- 分隔）')
    try:p=json.loads(match.group(1))
    except json.JSONDecodeError as e:raise ValueError(f'{path.name}: 文章元数据 JSON 错误：{e}') from e
    if not isinstance(p,dict):raise ValueError(f'{path.name}: 文章元数据必须是 JSON 对象')
    for key in ('slug','title','category','date','summary'):
        if not isinstance(p.get(key),str) or not p[key].strip():raise ValueError(f'{path.name}: {key} 必须为非空字符串')
    if not SLUG.fullmatch(p['slug']):raise ValueError(f'{path.name}: slug 仅允许小写英文字母、数字和短横线')
    if p['slug']!=path.stem:raise ValueError(f'{path.name}: 文件名必须与 slug 一致')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',p['date']):raise ValueError(f'{path.name}: 日期必须使用 YYYY-MM-DD 格式')
    dt.date.fromisoformat(p['date'])
    for key in ('draft','featured','pinned'):
        if key in p and not isinstance(p[key],bool):raise ValueError(f'{path.name}: {key} 应使用 true 或 false')
    if not isinstance(p.get('tags',[]),list) or any(not isinstance(x,str) for x in p.get('tags',[])):raise ValueError(f'{path.name}: tags 必须是字符串数组')
    p.setdefault('tags',[]);p['body']=match.group(2);p['path']=f'posts/{p["slug"]}/index.html'
    p['html'],p['toc']=markdown(p['body']);p['minutes']=max(1,math.ceil(len(p['body'])/450))
    return p

def read_config()->dict:
    c=json.loads((BASE/'site.json').read_text(encoding='utf-8'))
    if not isinstance(c,dict):raise ValueError('site.json 必须是 JSON 对象')
    for k in ('name','tagline','author','domain','hero_title','hero_accent','description','about'):
        if not isinstance(c.get(k),str):raise ValueError(f'site.json: {k} 必须为字符串')
    p=urlsplit(c['domain'])
    if p.scheme not in ('https','http') or not p.netloc or p.path not in ('','/') or p.query or p.fragment or p.username:raise ValueError('domain 应为完整网站根地址，例如 https://example.com，不要带路径')
    c['domain']=c['domain'].rstrip('/')
    for k in ('email','wechat','github','icp','police_record','police_url'):
        c.setdefault(k,'')
        if not isinstance(c[k],str):raise ValueError(f'{k} 必须是字符串')
    if not isinstance(c.get('demo'),bool):raise ValueError('demo 必须是 true 或 false')
    if not isinstance(c.get('categories'),list) or not c['categories']:raise ValueError('至少配置一个分类')
    ids=set()
    for cat in c['categories']:
        if not isinstance(cat,dict) or not isinstance(cat.get('id'),str):raise ValueError('分类必须是包含字符串 id 的对象')
        if not SLUG.fullmatch(cat.get('id','')) or cat['id'] in ids:raise ValueError('分类 id 需唯一，并且仅含小写字母、数字和短横线')
        ids.add(cat['id'])
        for key in ('name','description','icon','color'):
            if not isinstance(cat.get(key),str):raise ValueError(f'分类 {cat["id"]} 的 {key} 必须是字符串')
        if cat['color'] not in ('blue','green','purple','orange'):raise ValueError('分类 color 应为 blue / green / purple / orange')
    return c

class Site:
    def __init__(self,out:Path):
        self.out=out;self.c=read_config();self.categories=self.c['categories'];self.cats={x['id']:x for x in self.categories}
        all_posts=[parse_post(p) for p in sorted((BASE/'content').glob('*.md'))]
        slugs=[p['slug'] for p in all_posts]
        if len(slugs)!=len(set(slugs)):raise ValueError('文章 slug 重复，停止构建以避免覆盖')
        for p in all_posts:
            if p['category'] not in self.cats:raise ValueError(f'文章 {p["slug"]} 使用了未知分类')
        self.posts=sorted((p for p in all_posts if not p.get('draft',False)),key=lambda p:p['date'],reverse=True)
        self.counts={k:sum(p['category']==k for p in self.posts) for k in self.cats}
        self.pages=[];self.path='index.html';self.hashes={}
    def url(self,path:str)->str:
        return posixpath.relpath(path,posixpath.dirname(self.path) or '.')
    def a(self,path:str,label:str,cls:str='')->str:
        return f'<a class="{cls}" href="{esc(self.url(path))}">{label}</a>'
    def asset(self,name:str)->str:
        return esc(self.url('assets/'+name))+'?v='+self.hashes.get(name,'1')
    def pill(self,p:dict)->str:
        c=self.cats[p['category']]
        return f'<span class="category-pill {c["color"]}">{esc(c["name"])}</span>'
    def brand(self,footer:bool=False)->str:
        c=self.c
        return f'<a class="brand" href="{self.url("index.html")}" aria-label="{esc(c["name"])}首页"><span class="brand-mark" aria-hidden="true">{esc(c["name"][:1])}</span><span class="brand-copy"><span class="brand-name">{esc(c["name"])}</span><span class="brand-description">{esc(c["tagline"])}</span></span></a>'
    def section_head(self,title:str,label:str,link:str,text:str)->str:
        return f'<div class="section-heading"><div><p class="section-kicker">{label}</p><h2 class="section-title">{title}</h2></div>{self.a(link,esc(text)+icon("arrow"),"text-link")}</div>'
    def card(self,p:dict)->str:
        c=self.cats[p['category']];search=' '.join([p['title'],p['summary'],*p['tags']])
        return f'''<article class="article-card" data-article data-slug="{esc(p['slug'])}" data-date="{p['date']}" data-article-category="{c['id']}" data-search="{esc(search)}">
<div class="card-top">{self.pill(p)}{icon(c['icon'])}</div><h3>{self.a(p['path'],esc(p['title']))}</h3><p>{esc(p['summary'])}</p><div class="card-bottom"><time datetime="{p['date']}">{p['date'].replace('-','.')}</time><span>·</span><span>{p['minutes']} 分钟阅读</span>{icon('arrow')}</div></article>'''
    def topic(self,c:dict)->str:
        path=f'subject/{c["id"]}/index.html'
        return f'''<a href="{self.url(path)}" class="topic-card"><div class="topic-top"><span class="icon-wrap {c['color']}">{icon(c['icon'])}</span><span class="topic-count">{self.counts[c['id']]:02d} 篇文章</span></div><h3>{esc(c['name'])}</h3><p>{esc(c['description'])}</p><span class="text-link">进入专题 {icon('arrow')}</span></a>'''
    def tabs(self,all_label:str='全部文章')->str:
        return '<div class="tabs" aria-label="按主题筛选"><button class="tab active" type="button" data-category="all" aria-pressed="true">'+esc(all_label)+'</button>'+''.join(f'<button class="tab" type="button" data-category="{c["id"]}" aria-pressed="false">{esc(c["name"])}<small>{self.counts[c["id"]]}</small></button>' for c in self.categories)+'</div>'
    def footer(self)->str:
        c=self.c
        record=''
        if c['icp']:record+=f' · <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">{esc(c["icp"])}</a>'
        if c['police_record'] and c['police_url']:record+=f' · <a href="{esc(safe_url(c["police_url"]))}" target="_blank" rel="noopener noreferrer">{esc(c["police_record"])}</a>'
        demo='演示站点 · 请替换为你的内容' if c['demo'] else '记录 · 实践 · 分享'
        nav=''.join(self.a(path,label) for path,label in [('index.html','首页'),('articles/index.html','文章'),('subject/index.html','专题'),('tools/index.html','工具'),('about/index.html','关于')])
        return f'''<footer class="site-footer"><div class="container"><div class="footer-top">{self.brand(True)}<nav class="footer-links" aria-label="页脚导航">{nav}<button type="button" data-open-contact>联系</button>{self.a('feed.xml','RSS')}</nav></div><div class="footer-bottom"><span>© {dt.date.today().year} {esc(c['author'])} · {esc(c['name'])}{record}</span><span>{demo}</span></div></div></footer>'''
    def dialogs(self)->str:
        c=self.c;channels=''
        for label,key in [('电子邮箱','email'),('微信','wechat')]:
            if c[key]:channels+=f'<div class="contact-channel"><div><b>{label}</b><span>{esc(c[key])}</span></div><button class="button small" type="button" data-copy="{esc(c[key])}">复制</button></div>'
        if c['github']:channels+=f'<div class="contact-channel"><div><b>公开主页</b><span>GitHub</span></div><a class="button small" href="{esc(safe_url(c["github"]))}" target="_blank" rel="noopener noreferrer">访问 {icon("external")}</a></div>'
        if not channels:channels='<div class="demo-notice">联系方式尚未配置。站长可在本地管理界面或 site.json 中填写邮箱与微信。</div>'
        return f'''<dialog id="search-modal" class="modal" aria-labelledby="search-title"><div class="modal-head"><h2 id="search-title">搜索知识与记录</h2><button class="icon-button" type="button" data-close-modal aria-label="关闭搜索">{icon('close')}</button></div><div class="search-box">{icon('search')}<input id="global-search" type="search" placeholder="搜索文章、主题或关键词…" aria-label="搜索文章" autocomplete="off"></div><div id="search-results" class="search-results" aria-live="polite"></div><div class="modal-foot">搜索在本地完成 · 支持正文检索 · Ctrl / ⌘ K 打开 · Esc 关闭</div></dialog>
<dialog id="contact-modal" class="modal" aria-labelledby="contact-title"><div class="modal-head"><h2 id="contact-title">聊聊想法，交换经验</h2><button class="icon-button" type="button" data-close-modal aria-label="关闭联系方式">{icon('close')}</button></div><div class="contact-body"><p>关于文章、研究与技术实践，欢迎交流。</p>{channels}</div><div class="modal-foot">本网站没有留言提交表单，不会在这里收集你的联系信息。</div></dialog><div id="toast" class="toast" role="status" hidden></div><button id="back-top" class="back-top" type="button" aria-label="回到顶部" hidden>{icon('up')}</button>'''
    def write(self,path:str,title:str,description:str,body:str,active:str='home')->None:
        assert self.path==path, 'Set self.path before constructing relative links'
        c=self.c;page_title=title+' | '+c['name'];canonical=c['domain']+'/'+path.removesuffix('index.html')
        sprite='<svg class="sprite" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs>'+''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k,v in ICONS.items())+'</defs></svg>'
        navpaths=[('home','index.html','首页'),('articles','articles/index.html','文章'),('topics','subject/index.html','专题'),('tools','tools/index.html','工具'),('about','about/index.html','关于')]
        nav=''.join(f'<a href="{self.url(p)}" class="{"active" if key==active else ""}"'+(' aria-current="page"' if key==active else '')+'>'+label+'</a>' for key,p,label in navpaths)
        noindex='<meta name="robots" content="noindex,nofollow">' if c['demo'] or path=='404.html' else '<meta name="robots" content="index,follow">'
        base_tag='<base href="/">' if path=='404.html' else ''
        doc=f'''<!doctype html>
<html lang="zh-CN" data-theme="light"><head>{base_tag}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#2864e9"><title>{esc(page_title)}</title><meta name="description" content="{esc(description)}">{noindex}<link rel="canonical" href="{esc(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(page_title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}"><link rel="icon" href="{self.asset('favicon.svg')}" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="{esc(c['name'])} RSS" href="{self.url('feed.xml')}"><script src="{self.asset('theme.js')}"></script><link rel="stylesheet" href="{self.asset('styles.css')}"><script src="{self.asset('search-index.js')}" defer></script><script src="{self.asset('app.js')}" defer></script></head>
<body>{sprite}<a class="skip-link" href="#main">跳到正文</a><header class="site-header"><div class="container header-inner">{self.brand()}<nav class="desktop-nav" aria-label="主导航">{nav}</nav><div class="header-actions"><button class="search-trigger" type="button" data-open-search aria-label="搜索文章">{icon('search')}<span>搜索</span><kbd>⌘ K</kbd></button><button class="icon-button" type="button" data-theme-toggle aria-label="切换深浅色模式">{icon('moon','theme-moon')}{icon('sun','theme-sun')}</button><button class="icon-button mobile-toggle" type="button" data-menu-toggle aria-label="打开导航菜单" aria-controls="mobile-menu" aria-expanded="false">{icon('menu')}</button></div></div><nav id="mobile-menu" class="mobile-nav" aria-label="手机导航" hidden>{nav}</nav></header>
<main id="main">{body}</main>{self.footer()}{self.dialogs()}<noscript><div class="container demo-notice">文章和导航无需 JavaScript 即可阅读。搜索、筛选、深浅色切换和在线工具需要启用 JavaScript。</div></noscript></body></html>'''
        dest=self.out/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(doc,encoding='utf-8');self.pages.append(path)
    def home(self)->None:
        self.path='index.html';c=self.c
        hero=f'''<section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="status-dot"></span> 持续探索，认真记录</p><h1>{esc(c['hero_title'])}<br><em>{esc(c['hero_accent'])}</em></h1><p class="hero-description">{esc(c['description'])}</p><div class="button-row">{self.a('articles/index.html','开始阅读 '+icon('arrow'),'button primary')}{self.a('subject/index.html',icon('layers')+' 探索专题','button')}</div><div class="hero-micro"><span>{icon('book')}{len(self.posts)} 篇{'示例' if c['demo'] else ''}文章</span><span>{icon('grid')}{len(self.categories)} 个主题方向</span><span>{icon('pen')}在实践中积累</span></div></div><div class="hero-art" aria-hidden="true"><div class="art-grid"></div><span class="spark">✦</span><div class="note-window"><div class="window-bar"><i class="window-dot"></i><i class="window-dot"></i><i class="window-dot"></i><span>我的知识笔记 / 01</span></div><div class="note-content"><div class="note-kicker">从一个好问题开始</div><h2>思考，动手，<br>然后把它写下来。</h2><div class="note-line"></div><div class="note-line short"></div><div class="note-flow"><span>提出问题</span><b>→</b><span>实践验证</span><b>→</b><span>分享</span></div></div></div><div class="floating-note right"><span class="icon-wrap">{icon('sparkles')}</span><div><strong>与 AI 一起探索</strong><small>保持思考，认真核验</small></div></div><div class="floating-note left"><span class="icon-wrap green">{icon('code')}</span><div><strong>让经验可以复用</strong><small>从一次实践，到一份方法</small></div></div></div></section>'''
        strip='<div class="feature-strip"><span class="strip-label">'+icon('layers')+'这里都在记录什么</span><div class="strip-topics">'+''.join(self.a(f'subject/{x["id"]}/index.html',icon(x['icon'])+esc(x['name']),'strip-topic') for x in self.categories[:4])+'</div>'+self.a('about/index.html','认识站长 '+icon('arrow'),'strip-right')+'</div>'
        featured=''
        if self.posts:
            p=next((p for p in self.posts if p.get('featured')),self.posts[0]);others=[x for x in self.posts if x!=p];picks=sorted(others,key=lambda x:(not x.get('pinned',False),-dt.date.fromisoformat(x['date']).toordinal()))[:4]
            featured='<section class="section">'+self.section_head('值得先读的几篇','01 / EDITOR’S PICKS','articles/index.html','全部文章')+'<div class="featured-grid">'
            featured+=f'''<article class="featured-card"><a class="featured-cover" href="{self.url(p['path'])}" aria-label="阅读：{esc(p['title'])}"><div><div class="cover-kicker">AI × RESEARCH × PRACTICE</div><div class="cover-title">工具之外，<br>更是工作方式。</div><div class="cover-bottom">从灵感到实践 · 把经验变成方法</div></div><div class="cover-visual" aria-hidden="true"><div class="cover-square">{icon('book')}</div><div class="cover-square second">{icon('sparkles')}</div></div><span class="pin-label">{icon('pin')}置顶精选</span></a><div class="featured-copy">{self.pill(p)}<h3>{self.a(p['path'],esc(p['title']))}</h3><p>{esc(p['summary'])}</p><div class="card-bottom"><time datetime="{p['date']}">{p['date'].replace('-','.')}</time><span>· {p['minutes']} 分钟阅读</span>{self.a(p['path'],'继续阅读 '+icon('arrow'),'read-link')}</div></div></article><div class="picks"><div class="picks-heading"><strong>更多精选</strong><small>READ & EXPLORE</small></div>'''
            for i,x in enumerate(picks,1):featured+=f'<a class="pick-item" href="{self.url(x["path"])}"><span class="pick-number">{i:02d}</span><div class="pick-content">{self.pill(x)}<h3>{esc(x["title"])}</h3><p>{x["date"].replace("-",".")} · {esc(x["tags"][0] if x["tags"] else self.cats[x["category"]]["name"])}</p></div>{icon("external")}</a>'
            featured+='</div></div></section>'
        latest='<section class="section" data-catalog data-page-size="6">'+self.section_head('最近的探索与记录','02 / LATEST NOTES','articles/index.html','查看全部')+self.tabs('最新文章')+'<div class="article-grid">'+''.join(self.card(p) for p in self.posts)+'<p class="empty-state" data-empty hidden>这个分类暂时没有文章。</p></div><div class="more-button">'+self.a('articles/index.html','浏览全部文章 '+icon('arrow'),'button')+'</div></section>'
        topics='<section class="section">'+self.section_head('沿着主题，深入一点','03 / THEMATIC HUBS','subject/index.html','所有专题')+'<div class="topic-grid">'+''.join(self.topic(x) for x in self.categories)+'</div></section>'
        tags=[]
        for p in self.posts:
            for t in p['tags']:
                if t not in tags:tags.append(t)
        chips=''.join(f'<a class="category-chip" href="{self.url("articles/index.html")}?category={x["id"]}">{esc(x["name"])}<span>{self.counts[x["id"]]} 篇</span></a>' for x in self.categories)
        chips+=''.join(f'<a class="category-chip" href="{self.url("articles/index.html")}?q={quote(t)}"># {esc(t)}</a>' for t in tags[:2])
        explore='<section class="section">'+self.section_head('找到你感兴趣的内容','04 / EXPLORE BY TOPIC','articles/index.html','分类浏览')+'<div class="category-cloud">'+chips+'</div></section>'
        closing=f'<section class="closing-note"><div><h2>好的经验，值得被留下。</h2><p>从一个问题开始，在一次次记录中，找到属于自己的方法。</p></div>{icon("pen")}{self.a("about/index.html","关于这个小站 "+icon("arrow"),"button")}</section>'
        self.write(self.path,'AI 工具、科研实践与技术记录',c['description'],'<div class="container">'+hero+strip+featured+latest+topics+explore+closing+'</div>')
    def catalog(self)->None:
        self.path='articles/index.html'
        hero=f'<header class="page-hero"><p class="eyebrow">ARTICLE LIBRARY / 内容索引</p><h1>文章与实践</h1><p>每一个具体问题，都值得一次认真记录。按主题浏览，或从关键词开始。</p><div class="page-meta"><span>{len(self.posts)} 篇已发布文章</span><span>{len(self.categories)} 个主题方向</span><span>按时间持续整理</span></div></header>'
        sidebar=f'<aside class="archive-sidebar"><section class="sidebar-card"><h2>内容概览</h2><div class="sidebar-stat"><span>文章总数</span><b>{len(self.posts):02d}</b></div><div class="sidebar-stat"><span>主题方向</span><b>{len(self.categories):02d}</b></div><div class="sidebar-stat"><span>本地工具</span><b>{len(TOOLS):02d}</b></div></section><section class="sidebar-card"><h2>专题入口</h2>'+''.join(self.a(f'subject/{c["id"]}/index.html',esc(c['name'])+f'<span>{self.counts[c["id"]]} →</span>','sidebar-link') for c in self.categories)+'</section><section class="sidebar-card"><h2>慢慢记录，持续积累</h2><p>好的笔记不一定很长，但应当把问题、过程和边界讲清楚。</p></section></aside>'
        controls=self.tabs()+'<label class="catalog-search">'+icon('search')+'<input type="search" data-catalog-search aria-label="在文章中搜索" placeholder="搜索标题、标签与正文…"></label><div class="catalog-info"><span data-result-count></span><label>排序 <select data-sort aria-label="文章排序"><option value="newest">最新在前</option><option value="oldest">最早在前</option></select></label></div>'
        cards='<div class="article-grid">'+''.join(self.card(p) for p in self.posts)+'<div class="empty-state" data-empty hidden>没有找到匹配的文章，试试其他关键词。</div></div>'
        pager='<div class="pagination" data-pager><button type="button" class="button small" data-prev>上一页</button><span data-page-label></span><button type="button" class="button small" data-next>下一页</button></div>'
        body='<div class="container">'+hero+'<div class="archive-layout page-content"><section data-catalog data-page-size="8">'+controls+cards+pager+'</section>'+sidebar+'</div></div>'
        self.write(self.path,'文章与实践','按分类、时间与关键词浏览文章，支持本地全文搜索。',body,'articles')
    def topics(self)->None:
        self.path='subject/index.html'
        body='<div class="container"><header class="page-hero"><p class="eyebrow">THEMATIC HUBS / 专题导航</p><h1>从一个主题，慢慢深入</h1><p>将零散经验串起来，把一次次探索整理成可以反复回看的内容。</p></header><div class="page-content topic-grid topic-library">'+''.join(self.topic(c) for c in self.categories)+'</div></div>'
        self.write(self.path,'专题导航','AI 工具、科研实践、代码开发与写作思考的主题内容。',body,'topics')
        for c in self.categories:
            self.path=f'subject/{c["id"]}/index.html';ps=[p for p in self.posts if p['category']==c['id']]
            body=f'<div class="container"><header class="page-hero"><div class="breadcrumbs">{self.a("subject/index.html","全部专题")}{icon("chevron")}<span>{esc(c["name"])}</span></div><span class="icon-wrap {c["color"]}">{icon(c["icon"])}</span><h1>{esc(c["name"])}</h1><p>{esc(c["description"])}</p><div class="page-meta"><span>共 {len(ps)} 篇文章</span><span>按发布时间排序</span></div></header><div class="page-content article-grid">'+(''.join(self.card(p) for p in ps) or '<p class="empty-state">这个专题的第一篇文章正在等你写下。</p>')+'</div></div>'
            self.write(self.path,c['name']+'专题',c['description'],body,'topics')
    def post_pages(self)->None:
        for p in self.posts:
            self.path=p['path'];c=self.cats[p['category']]
            head=f'''<header class="article-head"><div class="breadcrumbs">{self.a('index.html','首页')}{icon('chevron')}{self.a('articles/index.html','文章')}{icon('chevron')}<span>{esc(c['name'])}</span></div>{self.pill(p)}<h1>{esc(p['title'])}</h1><p class="article-subtitle">{esc(p['summary'])}</p><div class="article-meta"><span class="author-circle">{esc(self.c['name'][:1])}</span><span>{esc(self.c['author'])}</span><time datetime="{p['date']}">{p['date'].replace('-','.')}</time><span>{p['minutes']} 分钟阅读</span><span>{len(p['body'])} 字符</span></div></header>'''
            notice='<div class="demo-notice">'+icon('info')+'<span>这是一篇原创演示文章，用于展示网站的排版与交互。请替换为你的实际内容，不代表站长已经完成的研究或成果。</span></div>' if self.c['demo'] else ''
            end='<div class="article-end"><div class="tag-cloud">'+''.join(f'<a class="tag" href="{self.url("articles/index.html")}?q={quote(t)}"># {esc(t)}</a>' for t in p['tags'])+'</div><button class="button small" type="button" data-share>复制文章链接 '+icon('link')+'</button></div>'
            toc='<aside class="sidebar-card toc"><h2>本篇目录</h2>'+''.join(f'<a href="#{anchor}">{esc(text)}</a>' for anchor,text in p['toc'])+'</aside>'
            related=sorted((x for x in self.posts if x['slug']!=p['slug']),key=lambda x:x['category']!=p['category'])[:3]
            body='<progress id="reading-progress" class="reading-progress" max="100" value="0" aria-label="阅读进度"></progress><div class="container">'+head+'<div class="article-layout"><article class="article-body">'+notice+'<div class="prose">'+p['html']+'</div>'+end+'</article>'+toc+'</div><section class="section"><h2 class="related-heading">继续探索</h2><div class="article-grid">'+''.join(self.card(x) for x in related)+'</div></section></div>'
            self.write(self.path,p['title'],p['summary'],body,'articles')
    def about(self)->None:
        self.path='about/index.html';c=self.c
        body=f'''<div class="container"><header class="page-hero"><p class="eyebrow">ABOUT / 关于小站</p><h1>你好，很高兴在这里遇见你。</h1><p>记录技术，也记录实践中的问题、转折和新的理解。</p></header><div class="page-content"><section class="about-card"><div class="profile-block"><div class="profile-avatar" aria-hidden="true">{esc(c['name'][:1])}</div><h2>{esc(c['author'])}</h2><p>{esc(c['name'])} · 站长</p><span class="profile-label"><span class="status-dot"></span>学习 · 实践 · 记录</span><button class="button small" type="button" data-open-contact>联系我 {icon('mail')}</button></div><div class="about-copy"><h2>把走过的路，写成可以回看的笔记。</h2><p>{esc(c['about'])}</p><div class="about-values"><div class="about-value">{icon('flask')}<h3>从实践出发</h3><p>记录具体问题，而不只收集抽象结论。</p></div><div class="about-value">{icon('shield')}<h3>说清楚边界</h3><p>把已经验证和仍待确认的部分分开。</p></div><div class="about-value">{icon('pen')}<h3>允许持续修正</h3><p>在新的理解中，更新旧的记录。</p></div></div></div></section></div></div>'''
        self.write(self.path,'关于我',c['about'],body,'about')
    def tools(self)->None:
        self.path='tools/index.html'
        cards=''
        for t in TOOLS:cards+=f'<a class="tool-card" href="{self.url("tools/"+t["id"]+"/index.html")}"><span class="icon-wrap {t["color"]}">{icon(t["icon"])}</span><h2>{t["title"]}</h2><p>{t["description"]}</p><span class="text-link">打开工具 {icon("arrow")}</span></a>'
        body='<div class="container"><header class="page-hero"><p class="eyebrow">TOOLS / 轻量工具箱</p><h1>小工具，解决眼前的小问题。</h1><p>无需注册，不依赖外部接口。输入内容仅在当前浏览器中处理，不会上传。</p><span class="local-badge">'+icon('shield')+'本地处理 · 不保存输入内容</span></header><div class="page-content tool-grid">'+cards+'</div></div>'
        self.write(self.path,'本地工具箱','JSON 格式化、时间戳转换、字数统计、URL 编解码、Base64 与图片处理工具。',body,'tools')
        for t in TOOLS:
            self.path=f'tools/{t["id"]}/index.html';kind=t['id']
            example={'json':'{"title":"我的笔记","tags":["AI","科研"],"published":true}','timestamp':'2026-09-05T12:00:00+08:00','words':'把探索写成记录，让知识持续生长。\nLearn, build, and share.','url':'科研笔记 & AI','base64':'你好，知行手记。'}.get(kind,'')
            if kind=='image':
                work='<div class="file-drop"><label class="field">选择图片（不超过 20 MB、4000 万像素）<input id="image-file" type="file" accept="image/jpeg,image/png,image/webp"></label></div><div class="field-row"><label class="field">输出宽度（像素，保持比例）<input id="image-width" type="number" min="1" max="8192" value="1600"></label><label class="field">输出格式<select id="image-format"><option value="image/webp">WebP</option><option value="image/jpeg">JPG（透明区域变白）</option><option value="image/png">PNG（保留透明）</option></select></label><label class="field">质量（PNG 不使用此参数）<input id="image-quality" type="number" min="0.1" max="1" step="0.05" value="0.8"></label></div><img id="image-preview" class="image-preview" alt="待处理图片预览" hidden><div class="tool-controls"><button id="image-convert" class="button primary" type="button">生成图片</button><a id="image-download" class="button" download hidden>保存处理后的图片</a></div><p class="tool-note">仅处理静态 JPG、PNG、WebP；不保留动画、EXIF 或色彩配置。转换不保证文件一定变小。图片不会上传到服务器。</p>'
            else:
                input_field=f'<label class="field">输入内容<textarea id="tool-input" spellcheck="false">{esc(example)}</textarea></label>'
                output_field='<label class="field">处理结果<textarea id="tool-output" readonly spellcheck="false" placeholder="结果会显示在这里"></textarea></label>'
                work='<div class="tool-inputs">'+input_field+(output_field if kind!='words' else '<div><p class="tool-note">汉字按 Unicode Han 文字统计；英文单词按字母与常见连接符划分；字符数按 Unicode 码点统计（组合表情可能包含多个码点），不是排版字形数。</p><div class="stats-row"><div class="stat-tile"><b id="count-chinese">0</b><span>汉字</span></div><div class="stat-tile"><b id="count-english">0</b><span>英文单词</span></div><div class="stat-tile"><b id="count-total">0</b><span>全部字符</span></div><div class="stat-tile"><b id="count-no-space">0</b><span>非空白字符</span></div></div></div>')+'</div>'
                if kind=='timestamp':work+='<label class="field">纯数字输入的单位<select id="timestamp-unit"><option value="s">秒</option><option value="ms">毫秒</option></select></label>'
                actions={'json':[('format','格式化 JSON'),('compact','压缩 JSON')],'timestamp':[('convert','转换时间'),('now','使用当前时间')],'url':[('encode','编码'),('decode','解码')],'base64':[('encode','编码'),('decode','解码')],'words':[]}[kind]
                work+='<div class="tool-controls">'+''.join(f'<button class="button {"primary" if i==0 else ""}" data-tool-action="{a}" type="button">{label}</button>' for i,(a,label) in enumerate(actions))+'<button class="button" data-tool-action="copy" type="button">复制'+('文本' if kind=='words' else '结果')+'</button><button class="button" data-tool-action="clear" type="button">清空</button></div>'
                notes={'json':'使用浏览器的 JSON.parse。超出 JavaScript 安全整数范围的数字可能丢失精度；重要大整数请使用字符串保存。重复键名将按解析器规则保留最后一个值。','timestamp':'日期字符串需包含时区，例如 +08:00 或 Z。纯数字输入请明确选择秒或毫秒，不做隐式猜测。','url':'按 encodeURIComponent / decodeURIComponent 的规则处理单个参数，不是整个 URL 的格式化工具。加号不会自动当作空格。','base64':'仅支持 UTF-8 文本。Base64 是编码，不是加密；不要用它隐藏密码或密钥。','words':'输入实时统计；刷新或关闭页面后不保留内容。'}
                work+='<p class="tool-note">'+notes[kind]+'</p>'
            work+='<p id="tool-status" class="tool-status" role="status" aria-live="polite"></p>'
            body=f'<div class="container"><header class="page-hero"><div class="breadcrumbs">{self.a("tools/index.html","全部工具")}{icon("chevron")}<span>{t["title"]}</span></div><h1>{t["title"]}</h1><p>{t["description"]}</p><span class="local-badge">{icon("shield")}本地处理 · 不上传输入内容</span></header><section class="page-content"><div class="tool-workspace" data-tool="{kind}">{work}</div></section></div>'
            self.write(self.path,t['title'],t['description'],body,'tools')
    def misc(self)->None:
        self.path='404.html'
        body='<div class="container error-page"><p class="error-code">404</p><h1>这一页，似乎还没有写下。</h1><p>链接可能已经变更，试着回到首页，或搜索你感兴趣的内容。</p><div class="button-row">'+self.a('index.html','返回首页 '+icon('arrow'),'button primary')+'<button class="button" type="button" data-open-search>搜索文章</button></div></div>'
        self.write(self.path,'页面未找到','页面未找到，请返回首页或搜索文章。',body)
        rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
        for tag,text in [('title',self.c['name']),('link',self.c['domain']+'/'),('description',self.c['description']),('language','zh-CN')]:ET.SubElement(channel,tag).text=text
        for p in self.posts:
            node=ET.SubElement(channel,'item');u=self.c['domain']+'/'+p['path'].removesuffix('index.html')
            for tag,text in [('title',p['title']),('link',u),('guid',u),('description',p['summary']),('pubDate',format_datetime(dt.datetime.combine(dt.date.fromisoformat(p['date']),dt.time(),tzinfo=dt.timezone(dt.timedelta(hours=8)))))]:ET.SubElement(node,tag).text=text
        ET.ElementTree(rss).write(self.out/'feed.xml',encoding='utf-8',xml_declaration=True)
        ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns);root=ET.Element('{'+ns+'}urlset')
        for path in self.pages:
            if path=='404.html':continue
            node=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=self.c['domain']+'/'+path.removesuffix('index.html')
        ET.ElementTree(root).write(self.out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
        robots='User-agent: *\n'+('Disallow: /\n' if self.c['demo'] else 'Allow: /\n')+'Sitemap: '+self.c['domain']+'/sitemap.xml\n'
        (self.out/'robots.txt').write_text(robots,encoding='utf-8')
    def run(self)->dict:
        self.out.mkdir(parents=True,exist_ok=True)
        shutil.copytree(BASE/'assets',self.out/'assets',dirs_exist_ok=True)
        data=[dict(slug=p['slug'],title=p['title'],summary=p['summary'],tags=p['tags'],category=self.cats[p['category']]['name'],date=p['date'],path=p['path'],text=p['body']) for p in self.posts]
        (self.out/'assets/search-index.js').write_text('window.BLOG_INDEX = '+json.dumps(data,ensure_ascii=False).replace('</','<\\/')+';\n',encoding='utf-8')
        self.hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()[:12] for p in (self.out/'assets').iterdir() if p.is_file()}
        self.home();self.catalog();self.topics();self.post_pages();self.about();self.tools();self.misc()
        manifest={'pages':len(self.pages),'articles':len(self.posts),'topics':len(self.categories),'tools':len(TOOLS),'demo':self.c['demo'],'domain':self.c['domain']}
        (self.out/'build-info.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return manifest

def build()->dict:
    """Build to staging first. Invalid content leaves the last working site intact."""
    staging=BASE/'.site-building';old=BASE/'.site-previous';destination=BASE/'site'
    if staging.exists():shutil.rmtree(staging)
    try:
        result=Site(staging).run()
        if old.exists():shutil.rmtree(old)
        if destination.exists():destination.rename(old)
        try:staging.rename(destination)
        except Exception:
            if old.exists() and not destination.exists():old.rename(destination)
            raise
        if old.exists():shutil.rmtree(old)
        return result
    except Exception:
        if staging.exists():shutil.rmtree(staging)
        raise

if __name__=='__main__':
    try:
        result=build();print('构建成功：'+json.dumps(result,ensure_ascii=False));print('打开 site/index.html，或运行 python -m http.server 8000 --directory site --bind 127.0.0.1')
        if result['demo']:print('提示：当前为演示模式，已禁止搜索引擎索引。正式发布前请替换内容、设置域名并关闭 demo。')
    except (ValueError,OSError,json.JSONDecodeError) as error:
        print('构建失败：'+str(error),file=sys.stderr);sys.exit(1)
