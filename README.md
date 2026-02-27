# AI产业洞察周报 · OpenClaw Skill

> 两层检索 + OpenClaw 主控 AI 分析 · 飞书文档输出 · 零外部 LLM 依赖

参照《上海国投先导人工智能产业洞察》风格，自动从指定微信公众号抓取近期文章，由 OpenClaw Agent 直接分类、撰写先导洞见，结果落飞书文档。

---

## 架构

```
第一层（文章检索）
  └─ scripts/search_wechat.js   搜狗微信爬虫，按公众号名 × 话题词搜索近期文章
  └─ RSS fallback               搜狗限速时直接抓量子位/36kr RSS

第二层（分析生成）
  └─ OpenClaw 主控 AI           读取文章摘要 → 分类 → 撰写先导洞见
  └─ 禁止调用任何外部 LLM API

输出
  └─ 飞书文档（feishu_doc append，分段写入）
  └─ 自动授权指定用户 full_access
```

## 信源配置

编辑 `accounts.json`：

- **`wechat_accounts`** — 监控的公众号列表（含 weight 排序权重）
- **`search_topics`** — 话题词，与公号名组合生成搜索查询
- **`categories`** — 7个分类及关键词映射（模型/Agent · 具身智能 · 算力 · 端侧AI · AI4S · 上海AI生态 · 投融资）
- **`filter_rules`** — 过滤规则（时间窗口、低质量标题模式）

默认监控公众号：量子位、机器之心、新智元、AI科技评论、智东西、硅星人、36氪、钛媒体、极客公园、晚点LatePost、AIGC开放社区、InfoQ

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 在 OpenClaw 中激活

将本目录放入 OpenClaw 的 `skills/` 目录，重启 gateway 后自动加载。

触发词：公众号周报、产业洞察、AI周报、生成报告

### 3. 手动测试搜索

```bash
# 搜索指定公号的近期文章
node scripts/search_wechat.js "量子位 大模型 2026年2月" -n 10

# 输出到 JSON 文件
node scripts/search_wechat.js "机器之心 具身智能 2026年2月" -n 10 -o result.json
```

## 输出示例

飞书文档结构：

```
# AI产业洞察周报 | 第N期（YYYY.MM.DD-MM.DD）

## 先导洞见（3条结构性信号）

## 一、模型/Agent应用
【标题】事件摘要 + 先导洞见

## 二、具身智能
...

## 本周数据与综述
```

## 版本历史

| 版本 | 说明 |
|------|------|
| v2.0.0 | 移除 Python 脚本层和外部 LLM 调用，改为纯 OpenClaw Agent 分析 |
| v1.x   | 基于 DeepSeek V3 + Python generate_report.py（已废弃） |

## 注意事项

- 搜狗微信搜索有频率限制，脚本内置随机延迟（2-3s）自动处理
- 微信公众号原文需通过 Jina Reader（`r.jina.ai`）代理访问，需配置 `JINA_API_KEY`
- 本工具仅用于学术研究，请遵守相关平台使用条款

## License

MIT
