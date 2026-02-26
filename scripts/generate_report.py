#!/usr/bin/env python3
"""
AI Industry Report Generator
生成上海国投先导风格的公众号周报
Usage: python3 generate_report.py [--days 7] [--accounts accounts.json] [--output report.md] [--feishu TOKEN]
"""
import os
import sys
import json
import time
import subprocess
import argparse
import datetime
import urllib.request
import urllib.error
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
OUTPUT_DIR = SKILL_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

WECHAT_SEARCH_JS = Path(__file__).parent.parent.parent / "wechat-article-search" / "scripts" / "search_wechat.js"
JINA_BASE = "https://r.jina.ai"

# Default: self-hosted proxy (no rate limits, 653 models)
DEFAULT_BASE = "http://152.53.52.170:3003/v1"
DEFAULT_MODEL = "deepseek-ai/deepseek-v3-0324"
DEFAULT_KEY_ENV = "PROXY_API_KEY"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def get_env():
    """Load API keys from environment or openclaw config."""
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    jina_key = os.environ.get("JINA_API_KEY", "")
    proxy_key = os.environ.get("PROXY_API_KEY", "sk-5Ds6eFbTEE1zu5fQ14F4FfB5892b419dB1BfC7292147B9Ef")
    proxy_base = os.environ.get("PROXY_BASE_URL", DEFAULT_BASE)
    if not openrouter_key or not jina_key:
        try:
            with open(Path.home() / ".openclaw" / "openclaw.json") as f:
                cfg = json.load(f)
            env = cfg.get("env", {})
            openrouter_key = openrouter_key or env.get("OPENROUTER_API_KEY", "")
            jina_key = jina_key or env.get("JINA_API_KEY", "")
        except Exception:
            pass
    return openrouter_key, jina_key, proxy_key, proxy_base


def search_articles(query: str, days: int = 7, limit: int = 15) -> list[dict]:
    """Search WeChat articles via Sogou using search_wechat.js."""
    if not WECHAT_SEARCH_JS.exists():
        print(f"  [WARN] search_wechat.js not found at {WECHAT_SEARCH_JS}", file=sys.stderr)
        return []
    try:
        result = subprocess.run(
            ["node", str(WECHAT_SEARCH_JS), query, "-n", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return []
        raw = json.loads(result.stdout)
        # search_wechat.js returns {"query":..., "total":..., "articles":[...]}
        if isinstance(raw, dict):
            articles = raw.get("articles", [])
        elif isinstance(raw, list):
            articles = raw
        else:
            return []

        # Filter by date: keep articles from last `days` days
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        filtered = []
        for a in articles:
            # Field names: "datetime" (e.g. "2026-02-22 10:01:09"), "date_text", "pubTime", "pub_time"
            pub_time = a.get("datetime", a.get("pubTime", a.get("pub_time", a.get("date_text", ""))))
            if pub_time:
                try:
                    dt = datetime.datetime.strptime(pub_time[:10], "%Y-%m-%d")
                    if dt >= cutoff:
                        filtered.append(a)
                except ValueError:
                    filtered.append(a)  # Keep if can't parse date
            else:
                filtered.append(a)
        return filtered
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  [WARN] Search failed for '{query}': {e}", file=sys.stderr)
        return []


def fetch_article_content(url: str, jina_key: str, timeout: int = 15) -> str:
    """Fetch article content via Jina Reader API."""
    try:
        jina_url = f"{JINA_BASE}/{url}"
        headers = {
            "Accept": "text/plain",
            "User-Agent": "Mozilla/5.0",
        }
        if jina_key:
            headers["Authorization"] = f"Bearer {jina_key}"
        req = urllib.request.Request(jina_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            # Truncate to 3000 chars to save tokens
            return content[:3000]
    except Exception as e:
        return ""


def call_openrouter(messages: list, model: str, api_key: str, temperature: float = 0.7, max_tokens: int = 4000, search_both_fields: bool = False, base_url: str = None) -> str:
    """Call OpenAI-compatible chat completions API."""
    endpoint_base = base_url or OPENROUTER_BASE
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if "openrouter" in endpoint_base:
        headers["HTTP-Referer"] = "https://openclaw.ai"
        headers["X-Title"] = "AI Industry Report"
    payload = json.dumps({
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens,
    }).encode("utf-8")

    def _do_request():
        req = urllib.request.Request(
            f"{endpoint_base}/chat/completions",
            data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if not choices:
                return ""
            msg = choices[0].get("message", {})
            content = msg.get("content", "")
            reasoning = msg.get("reasoning", "")
            if search_both_fields:
                return (content or "") + "\n" + (reasoning or "")
            if content and len(content) >= len(reasoning):
                return content
            return content or reasoning

    for attempt in range(2):
        try:
            return _do_request()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429 and attempt == 0:
                print(f"\n  [限流429] 等待15s...", end=" ", file=sys.stderr, flush=True)
                time.sleep(15)
                continue
            print(f"  [ERROR] HTTP {e.code}: {body[:150]}", file=sys.stderr)
            return ""
        except Exception as e:
            print(f"  [ERROR] {e}", file=sys.stderr)
            return ""
    return ""


def extract_json_from_text(text: str) -> str:
    """Extract the last valid JSON object from text (handles reasoning model output and code fences)."""
    if not text:
        return ""
    # Strip common code fence wrappers like ```json ... ```
    import re
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = list(fenced)

    # Also search raw JSON objects (outermost braces)
    best = None
    start = 0
    while True:
        idx = text.find("{", start)
        if idx < 0:
            break
        depth = 0
        for i in range(idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[idx:i+1])
                    break
        start = idx + 1

    # Return the last candidate that is valid JSON
    for candidate in reversed(candidates):
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    return ""


def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """Remove duplicate articles by title similarity."""
    seen_titles = set()
    result = []
    for a in articles:
        title = a.get("title", "").strip()
        # Normalize: remove punctuation, lowercase
        norm = "".join(c for c in title if c.isalnum()).lower()
        if norm and norm not in seen_titles:
            seen_titles.add(norm)
            result.append(a)
    return result


def select_and_categorize(articles: list[dict], categories: dict, api_key: str, model: str) -> dict:
    """Use AI to select top articles and categorize them."""
    articles_text = ""
    for i, a in enumerate(articles):
        articles_text += f"[{i}] 标题: {a.get('title','')}\n"
        articles_text += f"    来源: {a.get('source', a.get('account_name', a.get('accountName','')))}\n"
        articles_text += f"    摘要: {a.get('abstract', a.get('summary',''))[:200]}\n"
        articles_text += f"    链接: {a.get('url','')}\n\n"

    category_list = "\n".join(f"- {cat}" for cat in categories.keys())

    prompt = f"""你是一位AI产业分析师，负责筛选和分类本周最重要的AI行业新闻。

以下是本周收集到的微信公众号文章列表：
{articles_text}

请从中筛选出最具行业价值的文章（通常每类2-5篇，总计不超过20篇），按以下分类归类：
{category_list}

输出格式（严格JSON）：
{{
  "selected": [
    {{
      "index": <原始文章索引号>,
      "category": "<分类名>",
      "importance": "high/medium",
      "reason": "<一句话说明选择理由>"
    }}
  ]
}}

选择标准：
1. 优先选择有实质技术突破、具体数据或重大事件的文章
2. 排除重复报道同一事件的文章（只选最详尽的一篇）
3. 排除广告、活动通知、榜单评选等低信息密度内容
4. 投融资优先选择金额较大或战略意义强的
"""
    response = call_openrouter(
        [{"role": "user", "content": prompt}],
        model=model,
        api_key=api_key,
        temperature=0.3,
        max_tokens=8000,
        search_both_fields=True,
    )
    json_str = extract_json_from_text(response)
    if json_str:
        try:
            data = json.loads(json_str)
            return data.get("selected", [])
        except Exception as e:
            print(f"  [WARN] Failed to parse selection JSON: {e}", file=sys.stderr)
    else:
        print(f"  [WARN] No JSON found in selection response", file=sys.stderr)
        print(f"  Response tail (last 300): {response[-300:]}", file=sys.stderr)
    return []


def generate_item_analysis(article: dict, content: str, category: str, api_key: str, model: str, issue_style: str, base_url: str = None) -> dict:
    """Generate 先导洞见-style analysis for a single article."""
    title = article.get("title", "")
    summary = article.get("abstract", article.get("summary", ""))
    url = article.get("url", "")
    account = article.get('source', article.get('account_name', article.get('accountName', '')))
    full_content = content if content else summary

    prompt = f"""你是一位顶级AI产业分析师，正在为《AI产业洞察》周报撰写分析。

分类：{category}
文章标题：{title}
来源公众号：{account}
文章内容：{full_content[:2000]}

请生成以下两部分内容：

1. **事件摘要**（200-350字）：
   - 概括核心事实：发布了什么、具体数据/指标、主要功能/突破
   - 客观陈述，不加评价，信息密度高
   - 包含时间、主体、关键数字

2. **先导洞见**（250-400字）：
   - 分析本质突破是什么（不是表象，是why it matters）
   - 对行业的短期和长期影响
   - 有明确观点，不做平庸总结
   - 风格参考：用"本质是..."、"这意味着..."、"短期看..."、"长期看..."等分析句式
   - 落地到具体场景或产业逻辑

输出格式（严格JSON）：
{{
  "summary": "<事件摘要>",
  "insight": "<先导洞见>",
  "url": "{url}"
}}
"""
    response = call_openrouter(
        [{"role": "user", "content": prompt}],
        model=model,
        api_key=api_key,
        temperature=0.7,
        max_tokens=2000,
        base_url=base_url,
    )
    json_str = extract_json_from_text(response)
    if json_str:
        try:
            data = json.loads(json_str)
            data["title"] = title
            data["category"] = category
            data["url"] = data.get("url") or url
            return data
        except Exception as e:
            print(f"  [WARN] Failed to parse item JSON: {e}", file=sys.stderr)
    else:
        # Fallback: return a basic item with the response as insight
        print(f"  [WARN] No JSON, using raw response as insight", file=sys.stderr)
    return {"title": title, "summary": summary, "insight": response[:500] if response else "", "url": url, "category": category}


def format_report(items_by_category: dict, issue_num: str, date_range: str, report_name: str) -> str:
    """Format the final report in the 上海国投先导 style."""
    lines = []
    lines.append(f"# {report_name}（第{issue_num}期）")
    lines.append("")
    lines.append(f"**产业洞察 INDUSTRY INSIGHTS**")
    lines.append(f"**日期：{date_range}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    section_num = 0

    # Group categories into sections
    section_map = {
        "01 本周AI概览": ["模型/Agent应用", "具身智能", "算力", "端侧AI", "AI4S"],
        "02 上海AI生态": ["上海AI生态"],
        "03 投融资动态": ["投融资动态"],
    }

    for section_title, cats in section_map.items():
        section_items = []
        subsection_num = 1
        for cat in cats:
            cat_items = items_by_category.get(cat, [])
            if cat_items:
                section_items.append((cat, cat_items))

        if not section_items:
            continue

        lines.append(f"## {section_title}")
        lines.append("")

        # Get section number (01, 02, 03)
        sec_idx = section_title[:2]

        for cat, items in section_items:
            lines.append(f"### {sec_idx.lstrip('0') or '0'}.{subsection_num} {cat}")
            lines.append("")
            subsection_num += 1

            for item_idx, item in enumerate(items, 1):
                lines.append(f"**（{item_idx}）{item.get('title', '')}**")
                lines.append("")
                lines.append(item.get("summary", ""))
                lines.append("")
                lines.append("> **-先导洞见-**")
                lines.append(">")
                insight = item.get("insight", "")
                for line in insight.split("\n"):
                    lines.append(f"> {line}")
                lines.append("")
                lines.append(f"原文链接：{item.get('url', '')}")
                lines.append("")
                lines.append("---")
                lines.append("")

    lines.append("")
    lines.append("> **重要说明**")
    lines.append("> 本文所有观点仅供学习交流使用，不具有任何盈利目的、不构成任何投资推荐或操作建议。")
    lines.append("")
    lines.append(f"*报告生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append(f"*数据来源：微信公众号 | AI分析：OpenRouter*")

    return "\n".join(lines)


def write_to_feishu(content: str, title: str, feishu_token: str) -> None:
    """Write report to Feishu document via feishu_doc skill."""
    # This calls the feishu API via the OpenClaw built-in feishu_doc tool
    # Since we're in a Python script, we output a special marker for the agent to pick up
    print(f"\n[FEISHU_WRITE] token={feishu_token} title={title}", flush=True)
    print("[FEISHU_CONTENT_START]")
    print(content)
    print("[FEISHU_CONTENT_END]")


def main():
    parser = argparse.ArgumentParser(description="AI Industry Report Generator")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--accounts", default=str(SKILL_DIR / "accounts.json"), help="Accounts config JSON")
    parser.add_argument("--output", help="Output markdown file path")
    parser.add_argument("--feishu", help="Feishu document token to write to")
    parser.add_argument("--issue", default="", help="Issue number (e.g. 69)")
    parser.add_argument("--name", default="AI产业洞察", help="Report name")
    parser.add_argument("--model", default="stepfun/step-3.5-flash:free", help="OpenRouter model")
    parser.add_argument("--no-content", action="store_true", help="Skip fetching full article content via Jina")
    parser.add_argument("--max-per-cat", type=int, default=3, dest="max_per_cat", help="Max articles per category (default: 3)")
    args = parser.parse_args()

    openrouter_key, jina_key, proxy_key, proxy_base = get_env()
    # Use proxy for AI generation (no rate limits); fallback to OpenRouter
    ai_key = proxy_key
    ai_base = proxy_base
    if not proxy_key:
        print("[ERROR] No API key found. Set PROXY_API_KEY or OPENROUTER_API_KEY.", file=sys.stderr)
        sys.exit(1)

    with open(args.accounts) as f:
        config = json.load(f)

    # Use search_queries if present, else fall back to keywords
    search_queries = config.get("search_queries", config.get("keywords", []))
    categories = config.get("categories", {})

    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=args.days)
    date_range = f"{start_date.strftime('%Y.%m.%d')} - {end_date.strftime('%Y.%m.%d')}"
    issue_num = args.issue or str(end_date.isocalendar()[1])

    print(f"=== AI产业洞察报告生成器 ===")
    print(f"日期范围: {date_range}  |  期数: 第{issue_num}期")
    print(f"搜索词: {len(search_queries)} 条  |  模型: {args.model}")
    print()

    # Step 1: 搜索文章
    all_articles = []
    for query in search_queries:
        print(f"  搜索: {query[:30]}...", end=" ", flush=True)
        articles = search_articles(query, days=args.days, limit=10)
        print(f"{len(articles)} 篇")
        all_articles.extend(articles)
        time.sleep(1.2)

    all_articles = deduplicate_articles(all_articles)
    print(f"\n✓ 去重后共 {len(all_articles)} 篇文章\n")

    if not all_articles:
        print("[WARN] 未找到文章，请检查 search_wechat.js 是否正常。", file=sys.stderr)

    # Step 2: 关键词分类（快速可靠，无需AI）
    print("正在关键词分类...")
    items_by_category = {cat: [] for cat in categories.keys()}
    categorized_urls = set()

    def keyword_score(article: dict, kws: list) -> int:
        title = article.get("title", "")
        summary = article.get("summary", article.get("abstract", ""))
        text = title + " " + summary
        return sum(1 for kw in kws if kw in text)

    # 质量过滤：排除日报、课程广告、汇总类低信息文章
    LOW_QUALITY_PATTERNS = [
        "每日动态", "每日简报", "每日资讯", "每周汇总", "每周时政",
        "课程", "培训", "报名", "学习", "补贴申请", "工资", "就业指导",
        "概念股梳理", "资料整理全了", "投资建议", "选股",
    ]
    def is_low_quality(article: dict) -> bool:
        title = article.get("title", "")
        return any(p in title for p in LOW_QUALITY_PATTERNS)

    # Sort by recency, categorize greedily
    for article in sorted(all_articles,
                          key=lambda a: a.get("datetime", a.get("date_text", "")),
                          reverse=True):
        url = article.get("url", "")
        if url in categorized_urls:
            continue
        best_cat, best_score = "", 0
        for cat, kws in categories.items():
            s = keyword_score(article, kws)
            if s > best_score:
                best_cat, best_score = cat, s
        if best_cat and best_score >= 2 and not is_low_quality(article) and len(items_by_category[best_cat]) < args.max_per_cat:
            items_by_category[best_cat].append(article)
            categorized_urls.add(url)

    total = sum(len(v) for v in items_by_category.values())
    print(f"✓ 共选出 {total} 篇文章：")
    for cat, arts in items_by_category.items():
        if arts:
            print(f"    {cat}: {len(arts)} 篇 — " + " / ".join(a.get("title","")[:20] for a in arts))

    # Step 3: 抓全文 + AI生成分析
    print(f"\n正在生成分析（模型: {args.model}）...")
    articles_to_analyze = {cat: list(arts) for cat, arts in items_by_category.items()}
    items_by_category = {cat: [] for cat in categories.keys()}

    for cat, art_list in articles_to_analyze.items():
        for article in art_list:
            title_short = article.get("title", "")[:35]
            print(f"  [{cat[:5]}] {title_short}...", end=" ", flush=True)

            content = ""
            if not args.no_content and jina_key:
                content = fetch_article_content(article.get("url", ""), jina_key)

            # Retry once on failure
            for attempt in range(2):
                item = generate_item_analysis(article, content, cat, ai_key, args.model, issue_num, base_url=ai_base)
                if item.get("summary") and item.get("insight"):
                    break
                if attempt == 0:
                    print("(重试)", end=" ", flush=True)
                    time.sleep(3)

            items_by_category[cat].append(item)
            print("✓")
            time.sleep(3)  # Rate limit buffer for free models

    # Step 4: 格式化
    print("\n正在格式化报告...")
    report_md = format_report(items_by_category, issue_num, date_range, args.name)

    # Step 5: 输出
    output_path = args.output or str(OUTPUT_DIR / f"report_{end_date.strftime('%Y%m%d')}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n✅ 报告已保存: {output_path}")

    raw_path = output_path.replace(".md", "_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"articles": all_articles, "items": items_by_category}, f, ensure_ascii=False, indent=2)

    lines = report_md.split("\n")
    print("\n" + "="*60)
    print("\n".join(lines[:80]))
    if len(lines) > 80:
        print(f"\n... 共{len(lines)}行，完整内容见 {output_path}")

    if args.feishu:
        write_to_feishu(report_md, f"{args.name}（第{issue_num}期）", args.feishu)

    return output_path, report_md


if __name__ == "__main__":
    main()
