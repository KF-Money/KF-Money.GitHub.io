import json
import re
import tempfile
import unittest
import shutil
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
ROOT=Path(__file__).resolve().parents[1]

class Collector(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set();self.h1=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='h1':self.h1+=1
        if 'id' in attrs:self.ids.add(attrs['id'])
        if tag in ('a','link','script','img','use'):
            value=attrs.get('href') or attrs.get('src')
            if value:self.links.append(value)

class SiteTests(unittest.TestCase):
    def test_all_pages_have_one_heading_and_no_broken_internal_links(self):
        site=ROOT/'site';pages=list(site.rglob('*.html'));self.assertEqual(len(pages),json.loads((site/'build-info.json').read_text())['pages'])
        for page in pages:
            parser=Collector();parser.feed(page.read_text(encoding='utf-8'));self.assertEqual(parser.h1,1,str(page))
            for link in parser.links:
                parsed=urlsplit(link)
                if parsed.scheme or parsed.netloc:continue
                if not parsed.path:
                    if parsed.fragment:self.assertIn(unquote(parsed.fragment),parser.ids,(page,link))
                    continue
                target=(site/parsed.path.lstrip('/')) if parsed.path.startswith('/') else page.parent/unquote(parsed.path)
                if target.is_dir():target=target/'index.html'
                self.assertTrue(target.exists(),(page,link,target))
    def test_raw_html_is_not_executable(self):
        text,_=build.markdown('## Hello\n\n<script>alert(1)</script>\n\n[x](javascript:alert)\n\n`<img onerror=x>`')
        self.assertNotIn('<script>',text);self.assertNotIn('href="javascript:',text);self.assertIn('&lt;script&gt;',text)
    def test_unicode_and_code_preserved(self):
        text,toc=build.markdown('## 中文标题\n\n```python\nprint("你好")\n```\n\n**重要**')
        self.assertIn('print(&quot;你好&quot;)',text);self.assertEqual(toc,[('section-1','中文标题')]);self.assertIn('<strong>重要</strong>',text)
    def test_demo_robots(self):
        demo=json.loads((ROOT/'site.json').read_text())['demo']
        self.assertIn('Disallow: /' if demo else 'Allow: /',(ROOT/'site/robots.txt').read_text());self.assertIn('noindex' if demo else 'index,follow',(ROOT/'site/index.html').read_text())
    def test_search_has_full_article_text(self):
        text=(ROOT/'site/assets/search-index.js').read_text()
        data=json.loads(text.split('=',1)[1].strip().removesuffix(';').replace('\\/','/'))
        expected={p['slug']:p['body'] for p in map(build.parse_post,(ROOT/'content').glob('*.md')) if not p.get('draft',False)}
        self.assertEqual({p['slug']:p['text'] for p in data},expected)
    def test_output_contains_no_editor_or_private_key(self):
        self.assertFalse((ROOT/'site/editor.py').exists());self.assertFalse((ROOT/'site/site.json').exists());self.assertFalse(list((ROOT/'site').rglob('*.key')))
    def test_drafts_are_not_published(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);shutil.copy(ROOT/'site.json',base/'site.json');shutil.copytree(ROOT/'assets',base/'assets');(base/'content').mkdir()
            meta={'slug':'draft-test','title':'私有草稿','category':json.loads((ROOT/'site.json').read_text())['categories'][0]['id'],'date':'2026-09-05','summary':'草稿摘要','tags':[],'draft':True}
            (base/'content/draft-test.md').write_text('---\n'+json.dumps(meta,ensure_ascii=False)+'\n---\n\n不得公开的草稿',encoding='utf-8')
            with patch.object(build,'BASE',base):build.build()
            self.assertFalse((base/'site/posts/draft-test/index.html').exists());self.assertNotIn('不得公开',(base/'site/assets/search-index.js').read_text())
    def test_invalid_build_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);shutil.copy(ROOT/'site.json',base/'site.json');shutil.copytree(ROOT/'assets',base/'assets');shutil.copytree(ROOT/'content',base/'content')
            with patch.object(build,'BASE',base):
                build.build();before=(base/'site/index.html').read_bytes();(base/'content/broken.md').write_text('not front matter')
                with self.assertRaises(ValueError):build.build()
                self.assertEqual((base/'site/index.html').read_bytes(),before)

if __name__=='__main__':unittest.main()
