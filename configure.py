#!/usr/bin/env python3
"""Convenient command-line configuration; preserves unspecified fields."""
import argparse,json
from pathlib import Path
import build
p=argparse.ArgumentParser(description='修改站点信息并重新生成网站')
for field in ('name','author','domain','email','wechat','icp'):p.add_argument('--'+field)
p.add_argument('--production',action='store_true',help='关闭演示提示与 noindex；先替换示例文章')
a=p.parse_args();path=Path(__file__).with_name('site.json');old=path.read_text(encoding='utf-8');c=json.loads(old)
for key in ('name','author','domain','email','wechat','icp'):
 value=getattr(a,key)
 if value is not None:c[key]=value
if a.production:c['demo']=False
try:
 path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(build.build())
except Exception:
 path.write_text(old,encoding='utf-8');raise
