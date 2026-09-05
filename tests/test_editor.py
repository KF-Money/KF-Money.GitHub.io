import json,shutil,socket,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=Path(__file__).resolve().parents[1]

class LocalEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.app=Path(cls.temp.name)/'app'
        shutil.copytree(ROOT,cls.app,ignore=shutil.ignore_patterns('tests','__pycache__','.git'))
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.origin=f'http://127.0.0.1:{cls.port}'
        cls.process=subprocess.Popen([sys.executable,str(cls.app/'editor.py'),'--no-browser','--port',str(cls.port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                with urlopen(cls.origin+'/session.js',timeout=1) as response:script=response.read().decode()
                cls.token=json.loads(script.split('=',1)[1].strip().removesuffix(';'));break
            except URLError:time.sleep(.05)
        else:raise RuntimeError('本地工作台未启动')
    @classmethod
    def tearDownClass(cls):
        cls.process.terminate();cls.process.wait(timeout=5);cls.temp.cleanup()
    def request(self,path,data=None,token=True,origin=None,headers=None):
        h={'Origin':origin or self.origin}
        if data is not None:h['Content-Type']='application/json'
        if token:h['X-Editor-Token']=self.token
        h.update(headers or {})
        req=Request(self.origin+path,data=None if data is None else json.dumps(data).encode(),headers=h)
        try:
            with urlopen(req,timeout=8) as r:return r.status,r.read().decode()
        except HTTPError as e:return e.code,e.read().decode()
    def test_state_and_preview(self):
        code,body=self.request('/api/state');self.assertEqual(code,200);self.assertEqual(len(json.loads(body)['posts']),len(list((self.app/'content').glob('*.md'))))
        code,body=self.request('/preview/index.html');self.assertEqual(code,200);self.assertIn(json.loads((self.app/'site.json').read_text())['name'],body)
    def test_csrf_and_origin_are_checked(self):
        self.assertEqual(self.request('/api/build',{},token=False)[0],403)
        self.assertEqual(self.request('/api/build',{},origin='https://not-allowed.example')[0],403)
    def test_rebinding_host_and_traversal_are_rejected(self):
        self.assertEqual(self.request('/api/state',headers={'Host':'not-allowed.example'})[0],403)
        self.assertEqual(self.request('/preview/../../site.json')[0],403)
        self.assertEqual(self.request('/api/post',{'slug':'../../escape'})[0],400)
    def test_invalid_config_is_rolled_back(self):
        before=(self.app/'site.json').read_bytes();code,_=self.request('/api/config',{'domain':'javascript:bad'})
        self.assertEqual(code,400);self.assertEqual((self.app/'site.json').read_bytes(),before)
    def test_article_save_draft_publish_and_delete(self):
        post={'slug':'editor-unit-test','originalSlug':'','title':'Editor unit test','category':json.loads((self.app/'site.json').read_text())['categories'][0]['id'],'date':'2026-09-05','summary':'Unique editor test summary','tags':['test'],'pinned':False,'featured':False,'draft':True,'body':'## Test\n\nUNIQUE_DRAFT_CONTENT\n\n<script>alert(1)</script>'}
        code,_=self.request('/api/post',post);self.assertEqual(code,200)
        self.assertNotIn('UNIQUE_DRAFT_CONTENT',(self.app/'site/assets/search-index.js').read_text())
        post.update(originalSlug=post['slug'],draft=False)
        code,_=self.request('/api/post',post);self.assertEqual(code,200)
        page=(self.app/'site/posts/editor-unit-test/index.html').read_text();self.assertIn('&lt;script&gt;',page);self.assertNotIn('<script>alert(1)</script>',page)
        code,_=self.request('/api/delete',{'slug':post['slug']});self.assertEqual(code,200);self.assertFalse((self.app/'content/editor-unit-test.md').exists())
    def test_duplicate_slug_is_not_overwritten(self):
        article=next((self.app/'content').glob('*.md'),None)
        if article is None:self.skipTest('No existing article to test duplicate path')
        before=article.read_bytes()
        code,_=self.request('/api/post',{'slug':article.stem,'originalSlug':''});self.assertEqual(code,400)
        self.assertTrue(article.is_file())
        self.assertEqual(article.read_bytes(),before)

if __name__=='__main__':unittest.main()
