# AI产业洞察 - 自动化AI行业周报生成器

基于微信公众号文章，自动生成《上海国投先导》风格的AI产业洞察周报。

## 功能
- 搜狗微信搜索，覆盖大模型/Agent/具身智能/算力/端侧AI/上海生态/投融资7大板块
- DeepSeek V3 生成"先导洞见"：事件摘要 + 战略洞察（各200-400字）
- 输出本地 Markdown 文件 + 可选飞书文档

## 使用方法

```bash
cd skills/ai-industry-report
python3 scripts/generate_report.py \
  --days 7 \
  --issue 69 \
  --name "AI产业洞察" \
  --model "deepseek-ai/deepseek-v3-0324" \
  --max-per-cat 3
```

### 环境变量
| 变量 | 说明 |
|------|------|
| `PROXY_API_KEY` | OpenAI-compatible API Key（默认已内置） |
| `PROXY_BASE_URL` | API Base URL（默认 `http://152.53.52.170:3003/v1`） |
| `JINA_API_KEY` | Jina Reader Key（用于抓取全文，可选） |

## 依赖
- Node.js（微信搜索）
- Python 3.8+
- `~/.openclaw/workspace/skills/wechat-article-search/scripts/search_wechat.js`

## 输出示例

```
AI产业洞察（第69期）
日期：2026.02.19 - 2026.02.26

01 本周AI概览
  1.1 模型/Agent应用
  1.2 具身智能
  1.3 算力
  1.4 端侧AI
02 上海AI生态
03 投融资动态
```

每条包含：事件摘要 + **先导洞见**（战略分析）+ 原文链接

## OpenClaw 技能集成

作为 OpenClaw Skill 安装后，对话中说：
> "生成本周AI行业周报"

即可自动触发报告生成（约5-8分钟）。
