#!/usr/bin/env python3
"""
AetherChat — AI API Arbitrage Platform
Production-ready with Stripe billing, SEO landing page, and marketing engine.

Quick start:
  1. Set env: STRIPE_SECRET_KEY, OPENROUTER_API_KEY, SECRET_KEY
  2. pip install flask requests stripe gunicorn
  3. python app.py  (dev)  OR  gunicorn app:app -w 2 -b 0.0.0.0:5050  (prod)
  4. Stripe webhook: stripe listen --forward-to localhost:5050/stripe/webhook
"""
import os, json, uuid, hashlib
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SITE_NAME = "AetherChat"
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "http://localhost:5050")
SITE_DESC = "Affordable AI chat. Pay only for what you use. No subscriptions."

# Stripe setup (lazy init to not crash without key)
stripe = None
if STRIPE_KEY:
    import stripe as _stripe
    _stripe.api_key = STRIPE_KEY
    stripe = _stripe

# ═══════════════════════════════════════════
# MODELS & PRICING (50% markup over OpenRouter wholesale)
# ═══════════════════════════════════════════
MODELS = {
    "claude-sonnet": {
        "id": "anthropic/claude-sonnet-5", "name": "Claude Sonnet 5",
        "cost_per_m_in": 2.00, "cost_per_m_out": 10.00,
        "price_per_m_in": 3.00, "price_per_m_out": 15.00,
        "description": "Best for complex reasoning and coding"
    },
    "gemini-flash": {
        "id": "google/gemini-3.5-flash", "name": "Gemini 3.5 Flash",
        "cost_per_m_in": 1.50, "cost_per_m_out": 9.00,
        "price_per_m_in": 2.25, "price_per_m_out": 13.50,
        "description": "Fast, affordable, great for everyday tasks"
    },
    "qwen-max": {
        "id": "qwen/qwen3.7-max", "name": "Qwen 3.7 Max",
        "cost_per_m_in": 1.25, "cost_per_m_out": 3.75,
        "price_per_m_in": 2.00, "price_per_m_out": 6.00,
        "description": "Best value — powerful and cheap"
    },
    "glm": {
        "id": "z-ai/glm-5.2", "name": "GLM 5.2",
        "cost_per_m_in": 0.91, "cost_per_m_out": 2.86,
        "price_per_m_in": 1.50, "price_per_m_out": 4.50,
        "description": "Budget-friendly, solid performance"
    },
    "nemotron": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "Nemotron Ultra",
        "cost_per_m_in": 0.50, "cost_per_m_out": 2.20,
        "price_per_m_in": 0.80, "price_per_m_out": 3.50,
        "description": "NVIDIA's open model — fast & cheap"
    }
}

# Stripe price IDs (create in Stripe dashboard, paste here)
STRIPE_PRICES = {
    "starter": os.environ.get("STRIPE_PRICE_STARTER", "price_starter"),
    "pro": os.environ.get("STRIPE_PRICE_PRO", "price_pro"),
    "power": os.environ.get("STRIPE_PRICE_POWER", "price_power"),
}

CREDIT_PACKS = {
    "starter": {"credits": 5.00, "price": 5.00, "stripe_price": STRIPE_PRICES["starter"], "name": "Starter"},
    "pro": {"credits": 20.00, "price": 18.00, "stripe_price": STRIPE_PRICES["pro"], "name": "Pro"},
    "power": {"credits": 100.00, "price": 80.00, "stripe_price": STRIPE_PRICES["power"], "name": "Power"},
}

# ═══════════════════════════════════════════
# DATA LAYER
# ═══════════════════════════════════════════
def load_db(name):
    path = DATA_DIR / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}

def save_db(name, data):
    (DATA_DIR / f"{name}.json").write_text(json.dumps(data, indent=2))

def get_user(user_id=None):
    user_id = user_id or session.get("user_id")
    return load_db("users").get(user_id) if user_id else None

def create_user(email=None):
    user_id = uuid.uuid4().hex[:12]
    users = load_db("users")
    users[user_id] = {
        "id": user_id, "credits": 1.00, "total_spent": 0, "total_tokens": 0,
        "created": datetime.now(timezone.utc).isoformat(), "model_usage": {},
        "email": email, "stripe_customer_id": None
    }
    save_db("users", users)
    return users[user_id]

def deduct_credits(user_id, model_key, tokens_in, tokens_out):
    users = load_db("users")
    user = users.get(user_id)
    if not user: return False
    model = MODELS[model_key]
    cost = (tokens_in / 1_000_000) * model["price_per_m_in"] + (tokens_out / 1_000_000) * model["price_per_m_out"]
    if user["credits"] < cost: return False
    user["credits"] -= cost
    user["total_spent"] += cost
    user["total_tokens"] += tokens_in + tokens_out
    user.setdefault("model_usage", {}).setdefault(model_key, {"tokens": 0, "spent": 0})
    user["model_usage"][model_key]["tokens"] += tokens_in + tokens_out
    user["model_usage"][model_key]["spent"] += cost
    # Log transaction
    txn = {"user_id": user_id, "type": "usage", "model": model_key, "tokens_in": tokens_in,
           "tokens_out": tokens_out, "cost": round(cost, 6), "time": datetime.now(timezone.utc).isoformat()}
    txns = load_db("transactions")
    txns[str(len(txns))] = txn
    save_db("transactions", txns)
    save_db("users", users)
    return True

def add_credits(user_id, amount, source="manual"):
    users = load_db("users")
    if user_id in users:
        users[user_id]["credits"] += amount
        save_db("users", users)
        txns = load_db("transactions")
        txns[str(len(txns))] = {"user_id": user_id, "type": "credit_add", "amount": amount,
                                 "source": source, "time": datetime.now(timezone.utc).isoformat()}
        save_db("transactions", txns)
        return True
    return False

# ═══════════════════════════════════════════
# ROUTES — PUBLIC
# ═══════════════════════════════════════════
@app.route("/")
def landing():
    """SEO-optimized landing page for new visitors. Existing users go to chat."""
    if session.get("user_id") and get_user():
        return redirect(url_for("chat"))
    return render_template("landing.html", site=SITE_NAME, desc=SITE_DESC,
                          models=MODELS, packs=CREDIT_PACKS, domain=SITE_DOMAIN)

@app.route("/chat")
def chat():
    if not session.get("user_id"):
        user = create_user()
        session["user_id"] = user["id"]
    return render_template("index.html", models=MODELS, site=SITE_NAME, packs=CREDIT_PACKS)

@app.route("/pricing")
def pricing():
    return render_template("pricing.html", models=MODELS, packs=CREDIT_PACKS, site=SITE_NAME)

# ═══════════════════════════════════════════
# API — CHAT
# ═══════════════════════════════════════════
@app.route("/api/chat", methods=["POST"])
def api_chat():
    user = get_user()
    if not user: return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json
    model_key = data.get("model", "qwen-max")
    messages = data.get("messages", [])
    
    if model_key not in MODELS: return jsonify({"error": f"Unknown model: {model_key}"}), 400
    if not messages: return jsonify({"error": "No messages"}), 400
    
    model = MODELS[model_key]
    try:
        resp = requests.post(f"{OPENROUTER_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json",
                     "HTTP-Referer": SITE_DOMAIN, "X-Title": SITE_NAME},
            json={"model": model["id"], "messages": messages, "max_tokens": 2000}, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)}"}), 500
    
    usage = result.get("usage", {})
    tokens_in, tokens_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    
    if not deduct_credits(user["id"], model_key, tokens_in, tokens_out):
        return jsonify({"error": "Insufficient credits. Please top up.", "code": "LOW_CREDITS"}), 402
    
    choice = result["choices"][0]
    user = get_user()
    return jsonify({"content": choice["message"]["content"], "model": model["name"],
                    "tokens": {"in": tokens_in, "out": tokens_out},
                    "credits_remaining": round(user["credits"], 2)})

@app.route("/api/credits")
def api_credits():
    user = get_user()
    return jsonify({"credits": round(user["credits"], 2)}) if user else (jsonify({"error": "Auth required"}), 401)

@app.route("/api/models")
def api_models():
    return jsonify({k: {"name": m["name"], "price_in": m["price_per_m_in"],
                        "price_out": m["price_per_m_out"], "description": m["description"]} for k, m in MODELS.items()})

# ═══════════════════════════════════════════
# STRIPE — CHECKOUT & WEBHOOK
# ═══════════════════════════════════════════
@app.route("/api/create-checkout", methods=["POST"])
def create_checkout():
    if not stripe: return jsonify({"error": "Stripe not configured"}), 500
    user = get_user()
    if not user: return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json
    pack_key = data.get("pack", "starter")
    pack = CREDIT_PACKS.get(pack_key)
    if not pack: return jsonify({"error": "Invalid pack"}), 400
    
    try:
        checkout = stripe.checkout.Session.create(
            customer_email=user.get("email"),
            client_reference_id=user["id"],
            line_items=[{"price": pack["stripe_price"], "quantity": 1}],
            mode="payment",
            success_url=f"{SITE_DOMAIN}/chat?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{SITE_DOMAIN}/pricing",
            metadata={"user_id": user["id"], "pack": pack_key, "credits": str(pack["credits"])}
        )
        return jsonify({"url": checkout.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if not stripe: return jsonify({"error": "Stripe not configured"}), 500
    payload = request.get_data(as_text=True)
    sig = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        user_id = sess.get("client_reference_id") or sess["metadata"].get("user_id")
        credits = float(sess["metadata"].get("credits", 5))
        if user_id:
            add_credits(user_id, credits, source=f"stripe_{sess['id'][:12]}")
            # Update Stripe customer ID
            users = load_db("users")
            if user_id in users and sess.get("customer"):
                users[user_id]["stripe_customer_id"] = sess["customer"]
                save_db("users", users)
    
    return jsonify({"status": "ok"})

# ═══════════════════════════════════════════
# ADMIN — Agent-managed
# ═══════════════════════════════════════════
@app.route("/admin")
def admin_dashboard():
    return render_template("dashboard.html", **(admin_stats_data()))

@app.route("/api/admin/stats")
def admin_stats():
    return jsonify(admin_stats_data())

@app.route("/api/admin/create-user", methods=["POST"])
def admin_create_user():
    user = create_user()
    return jsonify({"user_id": user["id"], "credits": user["credits"]})

@app.route("/api/admin/add-credits", methods=["POST"])
def admin_add_credits():
    data = request.json
    if add_credits(data.get("user_id"), float(data.get("amount", 0)), source="admin"):
        user = get_user(data["user_id"])
        return jsonify({"success": True, "new_balance": round(user["credits"], 2)})
    return jsonify({"error": "User not found"}), 404

def admin_stats_data():
    users = load_db("users")
    model_usage = {}
    for u in users.values():
        for mk, mu in u.get("model_usage", {}).items():
            model_usage.setdefault(mk, {"tokens": 0, "spent": 0, "name": MODELS.get(mk, {}).get("name", mk)})
            model_usage[mk]["tokens"] += mu["tokens"]
            model_usage[mk]["spent"] += mu["spent"]
    total_users = len(users)
    total_revenue = sum(u.get("total_spent", 0) for u in users.values())
    total_tokens = sum(u.get("total_tokens", 0) for u in users.values())
    return {"total_users": total_users, "total_revenue": round(total_revenue, 2),
            "total_tokens": total_tokens, "model_usage": model_usage,
            "timestamp": datetime.now(timezone.utc).isoformat()}

# ═══════════════════════════════════════════
# SITEMAP & SEO
# ═══════════════════════════════════════════
@app.route("/sitemap.xml")
def sitemap():
    pages = ["", "/chat", "/pricing"]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f"  <url><loc>{SITE_DOMAIN}{p}</loc><changefreq>weekly</changefreq></url>\n"
    xml += "</urlset>"
    return xml, 200, {'Content-Type': 'application/xml'}

@app.route("/robots.txt")
def robots():
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_DOMAIN}/sitemap.xml", 200, {'Content-Type': 'text/plain'}

# ═══════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 {SITE_NAME} running on http://localhost:{port}")
    print(f"   Models: {len(MODELS)}  |  Stripe: {'✅' if stripe else '⚠️ demo mode'}")
    app.run(host="0.0.0.0", port=port, debug=not STRIPE_KEY)
