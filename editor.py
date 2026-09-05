#!/usr/bin/env python3
"""Private local writing desk. Deliberately binds only to 127.0.0.1."""
from __future__ import annotations
import argparse
import json
import mimetypes
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import build as builder

BASE=Path(__file__).resolve().parent
LOCK=threading.Lock()
TOKEN=secrets.token_urlsafe(32)
MAX_BODY=2*1024*1024

class Handler(BaseHTTPRequestHandler):
    server_version='ZhiNoteLocal/1.0'
    def log_message(self,fmt,*args):
        print('[本地工作台] '+fmt%args)
    def allowed_host(self):
        port=self.server.server_port
        return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
    def send(self,status,body,ctype='application/json; charset=utf-8'):
        if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        elif isinstance(body,str):body=body.encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if not self.allowed_host():return self.send(403,{'error':'不允许的 Host。请通过 127.0.0.1 或 localhost 访问。'})
        path=unquote(urlsplit(self.path).path)
        if path=='/session.js':return self.send(200,'window.EDITOR_TOKEN='+json.dumps(TOKEN)+';','application/javascript; charset=utf-8')
        if path=='/api/state':
            with LOCK:
                posts=[builder.parse_post(p) for p in sorted((BASE/'content').glob('*.md'))]
                clean=[{k:v for k,v in p.items() if k not in ('html','toc')} for p in posts]
                return self.send(200,{'config':builder.read_config(),'posts':sorted(clean,key=lambda x:x['date'],reverse=True)})
        if path in ('/','/index.html'):target=BASE/'editor/index.html'
        elif path.startswith('/editor/'):target=(BASE/path.lstrip('/')).resolve()
        elif path in ('/assets/styles.css','/assets/theme.js','/assets/favicon.svg'):target=BASE/path.lstrip('/')
        elif path.startswith('/preview/'):
            target=(BASE/'site'/path.removeprefix('/preview/')).resolve()
            if not target.is_relative_to(BASE/'site'):return self.send(403,{'error':'禁止访问此路径'})
            if target.is_dir():target=target/'index.html'
        else:return self.send(404,{'error':'页面不存在'})
        if not target.resolve().is_relative_to(BASE):return self.send(403,{'error':'禁止访问此路径'})
        if path.startswith('/editor/') and not target.is_relative_to(BASE/'editor'):return self.send(403,{'error':'禁止访问此路径'})
        if not target.is_file():return self.send(404,{'error':'文件不存在，请先生成网站'})
        ctype=mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype in ('application/javascript','application/json'):ctype+='; charset=utf-8'
        self.send(200,target.read_bytes(),ctype)
    def do_POST(self):
        if not self.allowed_host():return self.send(403,{'error':'不允许的 Host'})
        port=self.server.server_port
        if self.headers.get('Origin') not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):return self.send(403,{'error':'不允许的请求来源'})
        if not secrets.compare_digest(self.headers.get('X-Editor-Token',''),TOKEN):return self.send(403,{'error':'会话验证失败，请刷新本地管理页面'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'只接受 JSON 请求'})
        try:size=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.send(400,{'error':'请求长度错误'})
        if not 0<size<=MAX_BODY:return self.send(413,{'error':'请求为空或超过 2 MB'})
        try:data=json.loads(self.rfile.read(size).decode('utf-8'))
        except (ValueError,UnicodeDecodeError):return self.send(400,{'error':'JSON 格式错误'})
        if not isinstance(data,dict):return self.send(400,{'error':'请求必须是 JSON 对象'})
        with LOCK:
            target=None;before=None;changed=False
            try:
                if self.path=='/api/post':
                    slug=data.get('slug','')
                    if not isinstance(slug,str) or not builder.SLUG.fullmatch(slug):raise ValueError('文章路径只能包含小写英文字母、数字和短横线')
                    target=BASE/'content'/(slug+'.md')
                    original=data.get('originalSlug','')
                    if target.exists() and original!=slug:raise ValueError('此文章路径已存在，请使用另一个路径')
                    if original and original!=slug:raise ValueError('现有文章路径不可直接改名；请新建文章并迁移内容')
                    meta={k:data.get(k) for k in ('slug','title','category','date','summary','tags','pinned','featured','draft')}
                    body=data.get('body','')
                    if not isinstance(body,str):raise ValueError('正文必须是文本')
                    payload='---\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n---\n\n'+body.strip()+'\n'
                    before=target.read_bytes() if target.exists() else None
                    changed=True
                    target.write_text(payload,encoding='utf-8')
                    builder.parse_post(target)
                elif self.path=='/api/config':
                    target=BASE/'site.json';before=target.read_bytes();config=builder.read_config()
                    for key in ('name','tagline','author','domain','hero_title','hero_accent','description','about','email','wechat','github','icp','police_record','police_url','demo'):
                        if key in data:config[key]=data[key]
                    changed=True
                    target.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');builder.read_config()
                elif self.path=='/api/delete':
                    slug=data.get('slug','')
                    if not isinstance(slug,str) or not builder.SLUG.fullmatch(slug):raise ValueError('无效文章路径')
                    target=BASE/'content'/(slug+'.md')
                    if not target.is_file():raise ValueError('文章不存在')
                    before=target.read_bytes();changed=True;target.unlink()
                elif self.path!='/api/build':return self.send(404,{'error':'接口不存在'})
                result=builder.build()
                self.send(200,{'ok':True,'build':result})
            except (ValueError,OSError,KeyError,TypeError) as error:
                if target is not None and changed:
                    if before is None:target.unlink(missing_ok=True)
                    else:target.write_bytes(before)
                self.send(400,{'error':str(error)})

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='本地内容工作台，不要映射到公网。');parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('端口范围应为 1024～65535')
    if not (BASE/'site/index.html').exists():builder.build()
    try:server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as error:raise SystemExit(f'无法启动：{error}。可使用 --port 8767 指定其他端口。')
    address=f'http://127.0.0.1:{args.port}/'
    print(f'本地工作台：{address}\n只在本机监听；不要开放管理端口。按 Ctrl+C 退出。')
    if not args.no_browser:webbrowser.open(address)
    try:server.serve_forever()
    except KeyboardInterrupt:print('\n已关闭本地工作台。')
    finally:server.server_close()
