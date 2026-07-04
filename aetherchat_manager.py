#!/usr/bin/env python3
"""
AetherChat Agent Manager
Hermes-compatible script to manage the API arbitrage business autonomously.

Usage:
  python aetherchat_manager.py stats     # Get business stats
  python aetherchat_manager.py onboard   # Create a new user account
  python aetherchat_manager.py topup USER_ID AMOUNT  # Add credits
"""
import json, sys, requests
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:5050"
SCRIPT_DIR = Path(__file__).parent

def cmd_stats():
    """Get business stats for cron reporting."""
    resp = requests.get(f"{BASE}/api/admin/stats", timeout=10)
    data = resp.json()
    
    # Calculate profit margins
    revenue = data["total_revenue"]
    # Rough cost estimate: revenue / 1.5 (50% markup)
    cost = revenue / 1.5 if revenue > 0 else 0
    profit = revenue - cost
    
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "users": data["total_users"],
        "tokens": data["total_tokens"],
        "revenue": round(revenue, 2),
        "estimated_cost": round(cost, 2),
        "estimated_profit": round(profit, 2),
        "margin_pct": round((profit / revenue * 100) if revenue > 0 else 0, 1),
        "model_usage": data.get("model_usage", {})
    }
    
    print(json.dumps(output, indent=2))
    return output

def cmd_onboard():
    """Create a new user (e.g., from a marketing campaign)."""
    resp = requests.post(f"{BASE}/api/admin/create-user", timeout=10)
    data = resp.json()
    print(f"✅ New user: {data['user_id']} (${data['credits']} free credit)")
    return data

def cmd_topup(user_id, amount):
    """Add credits to a user."""
    resp = requests.post(f"{BASE}/api/admin/add-credits", 
                        json={"user_id": user_id, "amount": float(amount)}, timeout=10)
    data = resp.json()
    if data.get("success"):
        print(f"✅ {user_id}: +${amount} → ${data['new_balance']}")
    else:
        print(f"❌ Failed: {data.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python aetherchat_manager.py <stats|onboard|topup> [args]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "stats":
        cmd_stats()
    elif cmd == "onboard":
        cmd_onboard()
    elif cmd == "topup" and len(sys.argv) >= 4:
        cmd_topup(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
