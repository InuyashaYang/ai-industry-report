---
name: ai-industry-report
description: >
  微信公众号AI产业洞察周报生成器。当用户要求基于过去一周公众号文章生成综合分析报告、产业洞察、周报、研究报告时使用。
  自动从搜狗微信搜索抓取指定公众号文章，AI分类筛选，生成含先导洞见的分析，输出Markdown+飞书文档。
  触发词：公众号周报、产业洞察、AI周报、生成报告、wechat周报、行业综合分析。
---

# AI产业洞察报告技能

## 功能

基于指定微信公众号，生成每周AI产业综合分析报告，格式参照《上海国投先导人工智能产业洞察》风格：
- 分类覆盖：模型/Agent应用、具身智能、算力、端侧AI、AI4S、上海AI生态、投融资动态
- 每条新闻包含：事件摘要 + 先导洞见（分析性观点）+ 原文链接
- 双输出：本地Markdown + 可选飞书文档

## 环境要求

- **Node.js** + **cheerio**（用于搜索，wechat-article-search技能已含）
- **Python 3.7+**（generate_report.py）
- **OPENROUTER_API_KEY**（已在openclaw.json env中配置）
- **JINA_API_KEY**（可选，用于获取文章全文，已配置）

## 触发时机

当用户说以下任意内容时激活此技能：
- "帮我生成本周公众号AI报告/周报"
- "基于过去一周的公众号，生成产业洞察"
- "生成先导洞见风格的分析报告"
- "整合公众号文章做一份综合分析"
- "做个AI行业周报"

## 使用流程

### 第一步：确认参数

向用户确认（如未指定）：
- **期数**：第几期？（如果不知道，用当前周数或留空）
- **报告名称**：默认"AI产业洞察"，用户可自定义
- **时间范围**：默认7天，可改为14天
- **是否写入飞书**：如需写飞书，询问文档token或新建
- **模型**：默认 `stepfun/step-3.5-flash:free`（免费），可选其他

### 第二步：运行生成脚本

```bash
cd ~/.openclaw/workspace/skills/ai-industry-report
python3 scripts/generate_report.py \
  --days 7 \
  --issue <期数> \
  --name "AI产业洞察" \
  --model "stepfun/step-3.5-flash:free" \
  [--feishu <飞书文档token>] \
  [--output output/report_YYYYMMDD.md]
```

带环境变量（确保API key可用）：
```bash
OPENROUTER_API_KEY=$(python3 -c "import json; d=json.load(open('/root/.openclaw/openclaw.json')); print(d['env']['OPENROUTER_API_KEY'])") \
JINA_API_KEY=$(python3 -c "import json; d=json.load(open('/root/.openclaw/openclaw.json')); print(d['env'].get('JINA_API_KEY',''))") \
python3 ~/.openclaw/workspace/skills/ai-industry-report/scripts/generate_report.py \
  --days 7 --issue <期数> --name "AI产业洞察"
```

**注意**：openclaw.json路径根据实际用户替换（`/root` 或 `/home/inuyasha`）。

### 第三步：等待完成（约3-8分钟）

脚本执行阶段：
1. 搜索各公众号文章（~1-2分钟，有延迟防封）
2. AI筛选分类（~30秒）
3. 逐篇获取全文 + 生成分析（每篇~20秒）
4. 格式化输出

### 第四步：读取输出

```bash
cat ~/.openclaw/workspace/skills/ai-industry-report/output/report_YYYYMMDD.md
```

### 第五步：写入飞书（如需）

1. 如果脚本已传入 `--feishu TOKEN`，脚本会输出 `[FEISHU_WRITE]` 标记
2. 使用 `feishu_doc` 工具的 `append` 操作将内容写入
3. 必须用 `feishu_perm` 将焦旸的openid `ou_1de7623156107c3158a3caf01d66663d` 加为 full_access 协作者

**飞书写入示例**（读取MD文件后用feishu_doc append）：
```python
# 读取生成的MD
with open('output/report_YYYYMMDD.md') as f:
    content = f.read()
# 用feishu_doc append写入
feishu_doc.append(doc_token=TOKEN, content=content)
```

## 自定义账号列表

编辑 `accounts.json` 中的 `accounts` 列表添加/删除公众号。
当前默认账号：机器之心、新智元、量子位、36氪、钛媒体、晚点LatePost、硅星人、智东西、InfoQ、极客公园等。

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--days` | 搜索最近几天 | 7 |
| `--issue` | 期数 | 当前周数 |
| `--name` | 报告名称 | AI产业洞察 |
| `--model` | OpenRouter模型 | stepfun/step-3.5-flash:free |
| `--output` | 输出路径 | output/report_YYYYMMDD.md |
| `--feishu` | 飞书文档token | (不输出到飞书) |
| `--no-content` | 跳过Jina全文抓取 | False |
| `--keywords-only` | 只用关键词搜索 | False |

## 推荐模型

- **免费方案**：`stepfun/step-3.5-flash:free`（已验证，分析质量不错）
- **高质量**：`anthropic/claude-3.5-sonnet` 或 `google/gemini-2.0-flash-exp:free`
- **平衡**：`deepseek/deepseek-chat` 或 `qwen/qwen-2.5-72b-instruct:free`

## 输出文件

- `output/report_YYYYMMDD.md` — 完整报告Markdown
- `output/report_YYYYMMDD_raw.json` — 原始数据（所有文章 + 筛选结果 + 分析内容）

## 常见问题

**搜索无结果**：搜狗微信可能IP限流，等待10分钟重试或使用VPN。

**分析质量差**：换用更强的模型（如 claude-3.5-sonnet）。

**飞书写入失败**：检查token有效性，飞书内容过长需分段append。

**报告内容为空但无报错**：`search_wechat.js` 可能需要重新安装cheerio：
```bash
cd ~/.openclaw/workspace/skills/wechat-article-search && npm install cheerio
```
