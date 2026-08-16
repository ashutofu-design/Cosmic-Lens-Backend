"""Narrow tools — this logged-in customer only, customer-visible fields only."""
from __future__ import annotations

import re
from typing import Any


def parse_account_card(account_card: str) -> dict[str, Any]:
    """Read the customer-safe card already built for this user. No extra DB."""
    purchases: list[dict[str, Any]] = []
    cosmo = ""
    for line in (account_card or "").splitlines():
        s = line.strip()
        if s.lower().startswith("user id:"):
            cosmo = s.split(":", 1)[-1].strip()
        if s.startswith("- "):
            body = s[2:].strip()
            amount = 0
            m = re.search(r"₹\s*(\d+)", body)
            if m:
                amount = int(m.group(1))
            title = re.split(r"₹", body, 1)[0].strip() or body
            purchases.append({"title": title[:80], "amount": amount})
    return {"cosmo": cosmo, "purchases": purchases, "card": account_card or ""}


def customer_facts(
    user: Any = None,
    account_card: str = "",
    cosmo_user_id: str = "",
) -> dict[str, Any]:
    facts = lookup_this_account(user) if user is not None else {
        "cosmo": "",
        "name": "",
        "plan": "Free",
        "ask_left": 0,
        "purchases": [],
        "card": "",
    }
    parsed = parse_account_card(account_card)
    if not facts.get("purchases") and parsed.get("purchases"):
        facts["purchases"] = parsed["purchases"]
    if account_card and not facts.get("card"):
        facts["card"] = account_card
    cid = str(facts.get("cosmo") or cosmo_user_id or parsed.get("cosmo") or "").strip()
    if cid:
        facts["cosmo"] = cid
    return facts


def lookup_this_account(user: Any) -> dict[str, Any]:
    """Paid orders + plan this user can already see in the app."""
    try:
        from support_account import build_customer_facts

        return build_customer_facts(user)
    except Exception:
        return {
            "cosmo": "",
            "name": "",
            "plan": "Free",
            "ask_left": 0,
            "purchases": [],
            "card": "",
        }


def format_transactions(facts: dict[str, Any], lang: str) -> str:
    rows = facts.get("purchases") if isinstance(facts.get("purchases"), list) else []
    if lang == "en":
        if not rows:
            return (
                "There is no wallet in Cosmic Lens. I checked this account and do not see "
                "a paid order on Help → Transactions yet. If money was deducted, a team "
                "member will join this chat shortly — please wait here."
            )
        listed = "; ".join(
            f"{p.get('title')} ₹{p.get('amount')}" for p in rows[:5] if isinstance(p, dict)
        )
        return (
            "There is no wallet in Cosmic Lens. I checked this account — Help → Transactions "
            f"currently shows: {listed}. If the payment you made is not in that list, "
            "a team member will join this chat shortly — please wait here."
        )
    if not rows:
        return (
            "App mein wallet nahi hota. Is account pe Help → Transactions mein abhi koi "
            "paid order nahi dikha. Agar paise kat gaye hon to team yahin join karegi — wait kariye."
        )
    listed = "; ".join(
        f"{p.get('title')} ₹{p.get('amount')}" for p in rows[:5] if isinstance(p, dict)
    )
    return (
        "App mein wallet nahi hota. Is account pe Help → Transactions mein abhi yeh dikh raha hai: "
        f"{listed}. Agar aapka payment is list mein nahi hai to team yahin join karegi — wait kariye."
    )
