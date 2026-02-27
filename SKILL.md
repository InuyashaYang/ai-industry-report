---
name: ai-industry-report
description: >
  国智投洞见 · 微信公众号AI产业洞察周报生成器。当用户要求基于过去一周公众号文章生成综合分析报告、产业洞察、周报、研究报告时使用。
  由主控 AI 驱动：用 wechat-article-search 脚本抓取指定公众号文章列表，AI 分类、撰写先导洞见，结果落飞书文档，并附完整引用清单。
  触发词：国智投洞见、公众号周报、产业洞察、AI周报、生成报告、wechat周报、行业综合分析。
---

# 国智投洞见 · AI产业洞察报告技能

## 品牌名

**国智投洞见**（英文：GuoZhiTou Insights）

飞书文档标题格式：`国智投洞见 | 第N期（YYYY.MM.DD-MM.DD）`

---

## 设计原则

- **文章抓取**：调用 `wechat-article-search` 的 Node.js 脚本（纯爬虫工具）从搜狗微信拉取指定公众号近期文章
- **分析撰写**：全部由主控 AI 完成，禁止调用任何外部 LLM API
- **引用透明**：每条资讯标注原始公众号和日期，文档末尾附完整引用清单
- **输出**：落飞书文档，不保存本地文件

---

## 信源配置

读 `accounts.json` 获取：
- `wechat_accounts` — 要监控的公众号列表（含 weight）
- `search_topics` — 分类话题词
- `categories` — 关键词分类映射
- `filter_rules` — 过滤规则（max_days、skip_title_patterns 等）

如需增删公众号，直接编辑 `accounts.json` 的 `wechat_accounts`，无需改其他文件。

---

## 执行流程

### 第一步：确认参数

默认值（无需用户确认）：
- 时间范围：过去7天
- 期数：查 MEMORY.md 取上期期数 + 1
- 报告品牌：国智投洞见

### 第二步：抓取公众号文章

读取 `accounts.json` 的 `wechat_accounts` 和 `search_topics`，对高权重账号（weight ≥ 2）× 每个 topic 搜索：

```bash
cd ~/.openclaw/workspace/skills/wechat-article-search
node scripts/search_wechat.js "量子位 大模型 Agent 2026年2月" -n 6
node scripts/search_wechat.js "机器之心 具身智能 融资 2026年2月" -n 6
node scripts/search_wechat.js "新智元 AI芯片 算力 2026年2月" -n 6
# 以此类推，公号 × topic 组合
```

查询格式：`"{公号名} {topic} {year}年{month}月"`

记录每条结果的 `source`（公众号名）、`datetime`（发布时间）、`title`、`summary`，供后续引用。

**搜狗限流处理**：每次搜索间隔 2-3 秒，连续失败时切换 fallback：
```
web_fetch("https://www.qbitai.com/feed")   # 量子位 RSS
web_fetch("https://36kr.com/feed")          # 36kr RSS
```

对摘要中感兴趣的文章，可用 Jina Reader 抓全文：
```
web_fetch("https://r.jina.ai/https://mp.weixin.qq.com/s/XXXXX")
```

### 第三步：过滤与分类

1. 过滤掉超过 `filter_rules.max_days`（默认7天）的文章
2. 过滤掉 `skip_title_patterns` 中的标题（简报/课程/培训等）
3. 按 `categories` 关键词将文章归类到各分类
4. 同一事件多家媒体重复报道时合并为1条（保留最详细来源）

### 第四步：撰写报告

报告结构（国智投洞见风格）：

```
# 国智投洞见 | 第N期（YYYY.MM.DD-MM.DD）

出品：国智投 · OpenClaw AI 研究助手
覆盖分类：模型/Agent · 具身智能 · 算力 · ...

---

## 信息源说明
（说明采集渠道、工具、时间）

## 先导洞见
（3条结构性信号，结论先行，每条2-3句）

## 一、模型/Agent应用
**【标题】**
事件摘要（2-3句，含数据）
引用来源：公众号名（YYYY-MM-DD）
先导洞见：分析性观点（2-3句，指向产业意义）

## 二、具身智能 ... （同上格式）

## 本期信源全引用清单
（按公众号分组，列出每篇引用文章标题和日期）

---
本期「国智投洞见」由 OpenClaw AI 研究助手自动采集生成。
内容仅供参考，不构成投资建议。
```

**引用规范**：
- 每条资讯末尾写 `引用来源：公众号名（YYYY-MM-DD）`
- 文档末尾统一附「本期信源全引用清单」，按公众号分组列出

**Feishu 写入规范（避免400）**：
- 禁用嵌套列表（`- 父\n  - 子` 会触发400）
- 禁用 blockquote（`>` 开头）
- 每次 append < 1500 汉字

### 第五步：写入飞书

```
1. feishu_doc create  →  标题：国智投洞见 | 第N期（YYYY.MM.DD-MM.DD）
2. feishu_perm add    →  openid ou_1de7623156107c3158a3caf01d66663d, full_access
3. feishu_doc append  →  分段写入（每段验证 block_ids > 0）
4. 在今日日记 append 报告链接
5. 更新 MEMORY.md 记录最新期数和 token
```

---

## 历史期数（从 MEMORY.md 读取）

- 第70期（2026.02.21-02.27）飞书 token: QbVBd6fbZogCtRxXqWpculxEnwG（旧品牌名 AI产业洞察）
- 国智投洞见第1期（2026.02.21-02.27）飞书 token: IM5jdVFtvo63t3x0CHrci8jAnVe（含完整引用清单）
