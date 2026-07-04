# AetherChat Deployment Guide

## Quick Deploy (Railway/Render/Fly.io)

### 1. Push to GitHub
```bash
cd revenue-pipelines/api-arbitrage
git init && git add . && git commit -m "AetherChat v1"
gh repo create aetherchat --public --push
```

### 2. Deploy on Railway
1. Go to railway.app → New Project → Deploy from GitHub
2. Select `aetherchat` repo
3. Add env vars (see .env.example)
4. Deploy — gets a free `*.up.railway.app` domain

### 3. Or Deploy on Render
1. render.com → New Web Service
2. Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app -w 2 -b 0.0.0.0:$PORT`
5. Add env vars → Deploy

### 4. Custom Domain
1. Buy domain (Namecheap, Porkbun ~$10/year)
2. Add CNAME record to Railway/Render URL
3. Set SITE_DOMAIN in env vars
4. HTTPS is automatic on both platforms

## Stripe Setup

1. Create Stripe account at stripe.com
2. Create Products (one-time payment):
   - Starter: $5 for $5 credits
   - Pro: $18 for $20 credits  
   - Power: $80 for $100 credits
3. Copy Price IDs → STRIPE_PRICE_* env vars
4. Get webhook secret:
   ```bash
   stripe listen --forward-to https://yourdomain.com/stripe/webhook
   ```
5. Set STRIPE_WEBHOOK_SECRET

## Local Dev
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in keys
python app.py
# → http://localhost:5050
```
