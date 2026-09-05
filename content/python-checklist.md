---
{
  "slug": "python-checklist",
  "title": "我的 Python 小项目检查清单",
  "category": "code",
  "date": "2026-08-25",
  "summary": "输入校验、错误提示、路径管理和一份能看懂的使用说明。",
  "tags": [
    "Python",
    "代码质量"
  ],
  "pinned": false,
  "featured": false,
  "draft": false
}
---

## 先检查输入

在处理之前确认路径是否存在、数据列是否齐全，以及单位和缺失值是否已经说明。

```python
from pathlib import Path

source = Path("data/input.csv")
if not source.is_file():
    raise FileNotFoundError(f"找不到输入文件：{source}")
```

## 让错误信息可以采取行动

除了说“发生错误”，还应说明失败位置、预期格式和接下来可以检查的内容。

## 分开配置和处理逻辑

将经常变化的参数集中保存。对新的实验条件修改配置，而不是在多个脚本中寻找相同数字。

## 用少量例子检查边界

除了正常输入，还应检查空文件、缺失列和重复记录。测试的目标是明确行为，而不是只证明理想情况能够运行。
