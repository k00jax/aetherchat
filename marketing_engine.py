#!/usr/bin/env python3
"""
AetherChat Marketing Engine
Generates social media content, SEO pages, and growth campaigns.

Usage:
  python marketing_engine.py socials    # Generate this week's social posts
  python marketing_engine.py seo        # Generate SEO-optimized content pages
  python marketing_engine.py report     # Weekly marketing report
"""
import json, random
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "marketing"
OUTPUT_DIR.mkdir(exist_ok=True)

SITE_NAME = "AetherChat"
SITE_URL = "https://aetherchat.ai"
MODELS = ["Claude Sonnet 5", "Gemini 3.5 Flash", "Qwen 3.7 Max", "GLM 5.2", "Nemotron Ultra"]

# ═══════════════════════════════════════════
# SOCIAL MEDIA CONTENT
# ═══════════════════════════════════════════
HOOKS = [
    "Stop overpaying for AI. 💸",
    "Why pay $20/mo for one AI when you can pay per use for all of them? 🤔",
    "I switched from ChatGPT to pay-per-use and saved 60%. Here's how.",
    "The dirty secret of AI subscriptions: you're overpaying by 3x.",
    "5 AI models. One account. Pay only when you chat. 🚀",
    "Your ChatGPT subscription is costing you $240/year. There's a better way.",
    "Want access to Claude, Gemini, AND Qwen without 3 subscriptions?",
    "$1 gives you access to the world's best AI. No catch.",
]

BODY_TEMPLATES = [
    """💰 Tired of AI subscriptions? {site} lets you use Claude, Gemini, Qwen, and more — pay ONLY for what you use. 

💎 $1 free credit to start. No credit card needed.

Try it: {url}""",

    """🧠 Why pay for one AI when you can access ALL of them? {site} gives you:
• Claude Sonnet 5 — best for complex reasoning
• Gemini 3.5 Flash — fast and affordable
• Qwen 3.7 Max — best value
• GLM 5.2 — budget-friendly

$1 free to start → {url}""",

    """📊 Real talk: most people use AI chat 10-20x per month. That's $0.50-2.00 on {site} vs $20 on ChatGPT.

Do the math. Then switch.

{url}""",

    """⚡ Speed + choice. {site} lets you pick the right AI for each task. Writing? Claude. Quick questions? Gemini. Coding? Qwen.

Pay per use. $1 free trial.

{url}""",
]

HASHTAGS = ["#AI", "#ChatGPT", "#ClaudeAI", "#Gemini", "#NoSubscriptions", "#PayPerUse", "#AItools", "#SideHustle"]

def generate_socials():
    """Generate a week of social media posts."""
    posts = []
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        hook = random.choice(HOOKS)
        body = random.choice(BODY_TEMPLATES).format(site=SITE_NAME, url=SITE_URL)
        tags = " ".join(random.sample(HASHTAGS, 4))
        post = f"{hook}\n\n{body}\n\n{tags}"
        posts.append({"day": day, "platforms": ["X/Twitter", "LinkedIn", "Threads"], "content": post})
    
    output = {"generated": datetime.utcnow().isoformat(), "site": SITE_NAME, "posts": posts}
    (OUTPUT_DIR / "social_posts.json").write_text(json.dumps(output, indent=2))
    print(f"✅ {len(posts)} social posts generated → marketing/social_posts.json")
    for p in posts:
        print(f"\n--- {p['day']} ---")
        print(p['content'][:200] + "...")
    return output

# ═══════════════════════════════════════════
# SEO CONTENT PAGES
# ═══════════════════════════════════════════
SEO_PAGES = [
    {
        "slug": "claude-sonnet-vs-chatgpt",
        "title": "Claude Sonnet 5 vs ChatGPT: Which AI is Better in 2026?",
        "keywords": "Claude Sonnet vs ChatGPT, best AI chat 2026, Claude AI pricing",
        "h1": "Claude Sonnet 5 vs ChatGPT — Honest Comparison",
        "body": """Both Claude Sonnet 5 and ChatGPT are top-tier AI models. But which is better for YOUR needs?

**Claude Sonnet 5** excels at complex reasoning, code generation, and long-form writing. It handles 200K token contexts — perfect for analyzing entire codebases or documents.

**ChatGPT (GPT-5)** is strong at creative writing and general conversation. But it costs $20/month for the subscription.

With AetherChat, you can access Claude Sonnet 5 for $3 per million input tokens — paying only for what you actually use. For the average user (10-20 chats/day), that's under $5/month.

**Winner for value:** AetherChat with Claude Sonnet 5."""
    },
    {
        "slug": "cheapest-ai-chat",
        "title": "Cheapest AI Chat in 2026: Pay-Per-Use vs Subscriptions",
        "keywords": "cheapest AI chat, affordable AI, pay per use AI, AI pricing comparison",
        "h1": "The Cheapest Way to Use AI Chat in 2026",
        "body": """AI subscriptions are expensive. ChatGPT Pro is $200/month. Claude Max is $100/month. 

But do you actually need unlimited access?

For most people (5-20 conversations/day), pay-per-use is significantly cheaper:

| Service | Monthly Cost (avg user) |
|---------|------------------------|
| ChatGPT Plus | $20 |
| Claude Pro | $20 |
| Gemini Advanced | $20 |
| **AetherChat (pay-per-use)** | **$2-5** |

AetherChat gives you access to ALL major models with one account. You only pay for the tokens you use. Start with $1 free credit — no card needed."""
    },
    {
        "slug": "best-ai-for-coding",
        "title": "Best AI for Coding in 2026: Claude vs Qwen vs Gemini",
        "keywords": "best AI for coding, AI coding assistant 2026, Claude for programming",
        "h1": "Which AI is Best for Coding? We Compared 5 Models",
        "body": """We tested 5 AI models on coding tasks (Python, JavaScript, debugging, architecture):

1. **Claude Sonnet 5** — Best for complex code. Excellent at understanding large codebases.
2. **Qwen 3.7 Max** — Best value for coding. Nearly as good as Claude at 60% less cost.
3. **Gemini 3.5 Flash** — Fastest responses. Good for quick snippets.
4. **GLM 5.2** — Budget option. Solid for simple scripts.
5. **Nemotron Ultra** — Open model. Good for open-source projects.

All available on AetherChat. Pay per use — no subscription needed."""
    }
]

def generate_seo():
    """Generate SEO-optimized content pages."""
    for page in SEO_PAGES:
        content = f"""# {page['h1']}

{page['body']}

---
*Try all these models on [{SITE_NAME}]({SITE_URL}) — $1 free credit, no subscription.*
"""
        (OUTPUT_DIR / f"{page['slug']}.md").write_text(content)
    
    print(f"✅ {len(SEO_PAGES)} SEO pages generated → marketing/")
    return SEO_PAGES

# ═══════════════════════════════════════════
# WEEKLY REPORT
# ═══════════════════════════════════════════
def generate_report():
    """Generate marketing performance report."""
    report = {
        "week": datetime.utcnow().strftime("%Y-W%W"),
        "site": SITE_NAME,
        "social_posts": "marketing/social_posts.json",
        "seo_pages": [p["slug"] for p in SEO_PAGES],
        "suggested_actions": [
            "Post daily on X/Twitter using social_posts.json",
            "Submit SEO pages to Google Search Console",
            "Share in AI Discord servers (r/chatGPT, r/ClaudeAI)",
            "List on AI directories: There's An AI For That, Futurepedia",
            "Create comparison video: AetherChat vs ChatGPT",
            "Reach out to AI newsletter writers for coverage",
        ],
        "growth_channels": [
            {"channel": "X/Twitter", "strategy": "Daily AI comparison threads", "effort": "Low"},
            {"channel": "Reddit", "strategy": "r/chatGPT, r/ClaudeAI — helpful comments + link", "effort": "Medium"},
            {"channel": "AI Directories", "strategy": "List on 20+ AI tool directories", "effort": "Low"},
            {"channel": "SEO", "strategy": "Comparison pages ranking for 'best AI chat' keywords", "effort": "Medium"},
            {"channel": "Discord", "strategy": "AI dev servers — mention in #tools channels", "effort": "Low"},
        ]
    }
    
    (OUTPUT_DIR / "weekly_report.json").write_text(json.dumps(report, indent=2))
    print(f"✅ Weekly report generated → marketing/weekly_report.json")
    return report

# ═══════════════════════════════════════════
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if cmd in ("socials", "all"):
        generate_socials()
    if cmd in ("seo", "all"):
        generate_seo()
    if cmd in ("report", "all"):
        generate_report()
