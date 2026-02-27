---
name: ai-industry-report
description: >
  微信公众号AI产业洞察周报生成器。当用户要求基于过去一周公众号文章生成综合分析报告、产业洞察、周报、研究报告时使用。
  由主控 AI 驱动：用 wechat-article-search 脚本抓取指定公众号文章列表，AI 分类、撰写先导洞见，结果落飞书文档。
  触发词：公众号周报、产业洞察、AI周报、生成报告、wechat周报、行业综合分析。
---

# AI产业洞察报告技能

## 设计原则

- **文章抓取**：调用 `wechat-article-search` 的 Node.js 脚本（纯爬虫工具）从搜狗微信拉取指定公众号近期文章
- **分析撰写**：全部由主控 AI 完成，禁止调用任何外部 LLM API
- **输出**：落飞书文档，不保存本地文件

---

## 信源配置

读 `accounts.json` 获取：
- `wechat_accounts` — 要监控的公众号列表（含 weight）
- `search_topics` — 7个分类话题词
- `categories` — 关键词分类映射
- `filter_rules` — 过滤规则（max_days、skip_title_patterns 等）

如需增删公众号，直接编辑 `accounts.json` 的 `wechat_accounts`，无需改其他文件。

---

## 执行流程

### 第一步：确认参数

默认值（无需用户确认）：
- 时间范围：过去7天
- 期数：查 MEMORY.md 取上期期数 + 1
- 报告名称：AI产业洞察

### 第二步：抓取公众号文章

读取 `accounts.json` 的 `wechat_accounts` 和 `search_topics`，对高权重账号（weight ≥ 2）× 每个 topic 搜索：

```bash
cd ~/.openclaw/workspace/skills/wechat-article-search
node scripts/search_wechat.js "量子位 大模型 Agent 2026年2月" -n 5
node scripts/search_wechat.js "机器之心 具身智能 机器人 2026年2月" -n 5
node scripts/search_wechat.js "新智元 AI芯片 算力 2026年2月" -n 5
# ...以此类推，公号 × topic 组合
```

查询格式：`"{公号名} {topic} {year}年{month}月"`

**搜狗限流处理**：每次搜索间隔 2-3 秒，超过3次连续失败时切换 fallback：
```bash
# fallback：直接抓 RSS
web_fetch("https://www.qbitai.com/feed")
web_fetch("https://36kr.com/feed")
```

对摘要中感兴趣的文章，可用 Jina Reader 抓全文：
```
web_fetch("https://r.jina.ai/https://mp.weixin.qq.com/s/XXXXX")
```

### 第三步：过滤与分类

1. 过滤掉 `filter_rules.max_days`（默认7天）以前的文章
2. 过滤掉 `skip_title_patterns` 中的标题（简报/课程/培训等）
3. 按 `categories` 关键词将文章归类到7个分类
4. 同一事件多家媒体重复报道时合并为1条（保留最详细来源）

### 第四步：撰写报告

格式（参照《上海国投先导人工智能产业洞察》风格）：

```
# AI产业洞察周报 | 第N期（YYYY.MM.DD-MM.DD）

## 先导洞见
（3条结构性信号，每条2-3句，结论先行）

## 一、模型/Agent应用
**【标题】**
事件摘要（2-3句，含数据）
先导洞见：分析性观点（2-3句，指向产业意义）

## 二、具身智能
## 三、算力
## 四、端侧AI（含自动驾驶）
## 五、AI4Science
## 六、上海AI生态（无则省略）
## 七、投融资动态

## 本周数据与综述
- 核心数字（列表，不嵌套）
- 4个层面观察
---
本报告由 OpenClaw 主控 AI 直接生成。生成时间：YYYY年MM月DD日 HH:MM GMT+8
```

**写作规范（Feishu 400 限制）**：
- 禁用任何嵌套列表（`- 父\n  - 子` 会触发400）
- 禁用 blockquote（`>` 开头）
- 每段 append < 1500 汉字

### 第五步：写入飞书

```
1. feishu_doc create  →  标题：AI产业洞察周报 第N期（YYYY.MM.DD-MM.DD）
2. feishu_perm add    →  openid ou_1de7623156107c3158a3caf01d66663d, full_access
3. feishu_doc append  →  分段写入（每段验证 block_ids > 0）
4. 在今日日记 append 报告链接
5. 更新 MEMORY.md 记录最新期数和 token
```

---

## 历史期数（从 MEMORY.md 读取）

最新完成：第70期（2026.02.21-02.27），飞书 token: QbVBd6fbZogCtRxXqWpculxEnwG
