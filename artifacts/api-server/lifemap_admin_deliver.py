"""Admin LifeMap — enrich order payloads + deliver founder text → My Reports PDF."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


_MIN_BODY = 40


def person_brief(person: dict[str, Any] | None, fallback_name: str = "—") -> dict[str, Any]:
    if not isinstance(person, dict):
        person = {}
    name = str(person.get("name") or fallback_name or "—").strip()
    dob = ""
    try:
        y, m, d = int(person.get("year", 0)), int(person.get("month", 0)), int(person.get("day", 0))
        if y and m and d:
            dob = f"{d:02d}/{m:02d}/{y}"
    except (TypeError, ValueError):
        pass
    if not dob and person.get("dob"):
        dob = str(person.get("dob")).strip()

    tob = ""
    try:
        h, mn = int(person.get("hour", 0)), int(person.get("minute", 0))
        ampm = str(person.get("ampm") or "").upper().strip()
        if h or mn or ampm:
            tob = f"{h:02d}:{mn:02d}" + (f" {ampm}" if ampm else "")
    except (TypeError, ValueError):
        pass
    if not tob and person.get("tob"):
        tob = str(person.get("tob")).strip()

    out: dict[str, Any] = {
        "name": name,
        "dob": dob,
        "tob": tob.strip(),
        "place": str(person.get("place") or person.get("pob") or "").strip(),
        "gender": str(person.get("gender") or "").strip(),
        "mobile": str(person.get("mobile") or "").strip(),
    }
    lat, lon, tz = person.get("lat"), person.get("lon"), person.get("tz")
    if lat not in (None, ""):
        out["lat"] = lat
    if lon not in (None, ""):
        out["lon"] = lon
    if tz not in (None, ""):
        out["tz"] = str(tz).strip()
    return out


def _account_for(user_id: int) -> dict[str, str]:
    empty = {"user_name": "", "user_email": "", "user_phone": "", "cosmo_user_id": ""}
    if not user_id:
        return empty
    try:
        from models import User

        u = User.query.get(int(user_id))
        if not u:
            return empty
        return {
            "user_name": str(getattr(u, "name", None) or "").strip(),
            "user_email": str(getattr(u, "email", None) or "").strip(),
            "user_phone": str(getattr(u, "phone", None) or "").strip(),
            "cosmo_user_id": str(getattr(u, "cosmo_user_id", None) or "").strip(),
        }
    except Exception:
        return empty


def _primary_birth_brief(user_id: int) -> dict[str, Any]:
    """Account kundli birth details — shown on every PDF request card."""
    if not user_id:
        return person_brief({})
    try:
        from admin_dashboard import _parse_birth_data
        from models import Profile

        prim = Profile.query.filter_by(
            user_id=int(user_id), deleted_at=None, is_primary=True
        ).first()
        if not prim:
            prim = (
                Profile.query.filter_by(user_id=int(user_id), deleted_at=None)
                .order_by(Profile.created_at.asc())
                .first()
            )
        if not prim:
            return person_brief({})
        parsed = _parse_birth_data(prim.birth_data)
        merged = {
            "name": prim.name or "",
            "gender": prim.gender or parsed.get("gender") or "",
            "dob": parsed.get("dob") or "",
            "tob": parsed.get("tob") or "",
            "place": parsed.get("place") or "",
            "lat": parsed.get("lat"),
            "lon": parsed.get("lon"),
            "tz": parsed.get("tz"),
        }
        return person_brief(merged, str(prim.name or "—"))
    except Exception:
        return person_brief({})


def _notify_pdf_ready(
    user_id: int, title: str, body: str, kind: str, report_id: str
) -> dict[str, Any]:
    try:
        from notification_helper import send_to_user

        return (
            send_to_user(
                user_id,
                title,
                body,
                data={"screen": "/my-reports", "kind": kind, "report_id": report_id},
            )
            or {}
        )
    except Exception:
        return {"sent": 0, "error": "notify_failed"}


def _base_row(
    *,
    kind: str,
    label: str,
    order_id: str,
    created_at: Any,
    status: str,
    lang: str,
    urgent: bool,
    user_id: int,
    cosmo_user_id: str,
    subject: str,
    detail: str = "",
    contact_method: str = "my_reports",
    contact_value: str = "",
    admin_accepted_at: Any = None,
) -> dict[str, Any]:
    uid = int(user_id or 0)
    acct = _account_for(uid)
    cosmo = (cosmo_user_id or "").strip() or acct.get("cosmo_user_id") or ""
    return {
        "kind": kind,
        "label": label,
        "order_id": order_id,
        "created_at": created_at,
        "status": status or "pending",
        "lang": lang or "en",
        "urgent": bool(urgent),
        "contact_method": contact_method,
        "contact_value": contact_value,
        "user_id": uid,
        "cosmo_user_id": cosmo,
        "user_name": acct.get("user_name") or "",
        "user_email": acct.get("user_email") or "",
        "birth": _primary_birth_brief(uid),
        "subject": subject,
        "detail": detail,
        "admin_accepted_at": admin_accepted_at or None,
        "admin_accepted": bool(admin_accepted_at),
    }


def enrich_love_row(row: dict[str, Any]) -> dict[str, Any]:
    p1 = row.get("p1") if isinstance(row.get("p1"), dict) else {}
    p2 = row.get("p2") if isinstance(row.get("p2"), dict) else {}
    snap = row.get("engine_snapshot") if isinstance(row.get("engine_snapshot"), dict) else {}
    p1b = person_brief(p1, str(row.get("p1_name") or snap.get("p1_name") or "Person 1"))
    p2b = person_brief(p2, str(row.get("p2_name") or snap.get("p2_name") or "Person 2"))
    out = _base_row(
        kind="love_reality_pro",
        label="Love Reality Pro",
        order_id=str(row.get("order_id") or ""),
        created_at=row.get("created_at"),
        status=str(row.get("status") or "pending"),
        lang=str(row.get("lang") or "en"),
        urgent=bool(row.get("urgent")),
        user_id=int(row.get("user_id") or 0),
        cosmo_user_id=str(row.get("cosmo_user_id") or ""),
        subject=f"{p1b['name']} & {p2b['name']}",
        contact_method=str(row.get("contact_method") or "my_reports"),
        contact_value=str(row.get("contact_value") or ""),
        admin_accepted_at=row.get("admin_accepted_at"),
    )
    out["p1"] = p1b
    out["p2"] = p2b
    out["engine_snapshot"] = {
        "p1_name": snap.get("p1_name") or p1b["name"],
        "p2_name": snap.get("p2_name") or p2b["name"],
        "red_flag_count": snap.get("red_flag_count"),
    }
    out["deliverable"] = str(row.get("deliverable") or "report")
    out["amount_inr"] = row.get("amount_inr")
    out["priority_fee_inr"] = row.get("priority_fee_inr")
    out["eta_hours"] = row.get("eta_hours") if row.get("eta_hours") is not None else (12 if row.get("urgent") else 144)
    out["eta_label"] = row.get("eta_label") or (
        "⚡ Priority — deliver within 12 hours"
        if row.get("urgent")
        else "📦 Standard — 4–6 business days"
    )
    return out


def enrich_milan_row(row: dict[str, Any]) -> dict[str, Any]:
    p1 = row.get("p1") if isinstance(row.get("p1"), dict) else {}
    p2 = row.get("p2") if isinstance(row.get("p2"), dict) else {}
    snap = row.get("engine_snapshot") if isinstance(row.get("engine_snapshot"), dict) else {}
    p1b = person_brief(p1, str(row.get("p1_name") or snap.get("p1_name") or "Partner A"))
    p2b = person_brief(p2, str(row.get("p2_name") or snap.get("p2_name") or "Partner B"))
    score = row.get("couple_score")
    if score is None:
        score = snap.get("couple_score")
    band = row.get("couple_band") or snap.get("couple_band") or ""
    detail = ""
    if score is not None:
        detail = f"score {score}"
        if band:
            detail += f" · {band}"
    out = _base_row(
        kind="milan_pro",
        label="Kundli Milan Pro",
        order_id=str(row.get("order_id") or ""),
        created_at=row.get("created_at"),
        status=str(row.get("status") or "pending"),
        lang=str(row.get("lang") or "en"),
        urgent=bool(row.get("urgent")),
        user_id=int(row.get("user_id") or 0),
        cosmo_user_id=str(row.get("cosmo_user_id") or ""),
        subject=f"{p1b['name']} & {p2b['name']}",
        detail=detail,
        contact_method=str(row.get("contact_method") or "my_reports"),
        contact_value=str(row.get("contact_value") or ""),
        admin_accepted_at=row.get("admin_accepted_at"),
    )
    out["p1"] = p1b
    out["p2"] = p2b
    out["couple_score"] = score
    out["couple_band"] = band
    out["engine_snapshot"] = {
        "p1_name": snap.get("p1_name") or p1b["name"],
        "p2_name": snap.get("p2_name") or p2b["name"],
        "couple_score": score,
        "couple_band": band,
        "alert_count": snap.get("alert_count"),
    }
    out["deliverable"] = str(row.get("deliverable") or "report")
    out["amount_inr"] = row.get("amount_inr")
    out["priority_fee_inr"] = row.get("priority_fee_inr")
    out["eta_hours"] = row.get("eta_hours") if row.get("eta_hours") is not None else (12 if row.get("urgent") else 144)
    out["eta_label"] = row.get("eta_label") or (
        "⚡ Priority — deliver within 12 hours"
        if row.get("urgent")
        else "📦 Standard — 4–6 business days"
    )
    return out


def enrich_numerology_row(row: dict[str, Any]) -> dict[str, Any]:
    person = row.get("person") if isinstance(row.get("person"), dict) else {}
    params = row.get("params") if isinstance(row.get("params"), dict) else {}
    merged = {**params, **person}
    brief = person_brief(
        merged,
        str(row.get("subject_name") or person.get("name") or params.get("name") or "—"),
    )
    if not brief.get("dob"):
        brief["dob"] = str(row.get("dob") or params.get("dob") or "")
    if not brief.get("tob"):
        brief["tob"] = str(merged.get("tob") or params.get("tob") or "")
    for k in ("lat", "lon", "tz"):
        if brief.get(k) in (None, "") and merged.get(k) not in (None, ""):
            brief[k] = merged.get(k)
    out = _base_row(
        kind="numerology_pro",
        label="Numerology Pro",
        order_id=str(row.get("order_id") or ""),
        created_at=row.get("created_at"),
        status=str(row.get("status") or "pending"),
        lang=str(row.get("lang") or "en"),
        urgent=bool(row.get("urgent")),
        user_id=int(row.get("user_id") or 0),
        cosmo_user_id=str(row.get("cosmo_user_id") or ""),
        subject=brief["name"],
        detail=brief.get("dob") or "",
        contact_method=str(row.get("contact_method") or "my_reports"),
        admin_accepted_at=row.get("admin_accepted_at"),
    )
    out["deliverable"] = str(row.get("deliverable") or "report")
    out["contact_value"] = str(row.get("contact_value") or "")
    out["person"] = brief
    birth = out.get("birth") if isinstance(out.get("birth"), dict) else {}
    for k in ("dob", "tob", "place", "mobile", "lat", "lon", "tz", "gender"):
        if not brief.get(k) and birth.get(k) not in (None, ""):
            brief[k] = birth[k]
    if brief.get("name") in ("", "—") and birth.get("name"):
        brief["name"] = birth["name"]
    out["person"] = brief
    out["purchase_id"] = row.get("purchase_id")
    amount = row.get("amount_inr")
    try:
        amount_n = int(amount) if amount is not None else 0
    except (TypeError, ValueError):
        amount_n = 0
    if amount_n <= 0:
        # Backfill for older bypass orders / missing purchase snapshot.
        try:
            pid = int(row.get("purchase_id") or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid:
            try:
                from models import CoupleReportPurchase

                purchase = CoupleReportPurchase.query.get(pid)
                if purchase and purchase.amount:
                    amount_n = int(purchase.amount)
            except Exception:
                pass
        if amount_n <= 0:
            deliverable = str(row.get("deliverable") or "report").lower()
            urgent = bool(row.get("urgent"))
            try:
                fee = int(row.get("priority_fee_inr") or 0)
            except (TypeError, ValueError):
                fee = 0
            if urgent and fee <= 0:
                fee = 299 if deliverable == "video" else 149
            try:
                from numerology_report_billing import CATALOG, PRODUCT_LIFE_MASTERY
                import os

                base = int(CATALOG[PRODUCT_LIFE_MASTERY].get("amount_inr") or 299)
                if deliverable == "video":
                    base = int(os.environ.get("LIFE_MASTERY_VIDEO_PRICE_INR", "799"))
            except Exception:
                base = 799 if deliverable == "video" else 299
            amount_n = base + (fee if urgent else 0)
        amount = amount_n
    out["amount_inr"] = amount
    out["priority_fee_inr"] = row.get("priority_fee_inr")
    out["eta_hours"] = row.get("eta_hours") if row.get("eta_hours") is not None else (12 if row.get("urgent") else 144)
    out["eta_label"] = row.get("eta_label") or (
        "⚡ Priority — deliver within 12 hours"
        if row.get("urgent")
        else "📦 Standard — 4–6 business days"
    )
    return out


def enrich_astrovastu_row(row: dict[str, Any]) -> dict[str, Any]:
    room = (str(row.get("room_type") or "").replace("_", " ") or "Room").title()
    direction = str(row.get("direction") or "")
    amount = row.get("amount_inr")
    detail = direction
    if amount:
        detail = f"{direction} · ₹{amount}" if direction else f"₹{amount}"
    out = _base_row(
        kind="astrovastu_pro",
        label="AstroVastu Pro",
        order_id=str(row.get("order_id") or ""),
        created_at=row.get("created_at"),
        status=str(row.get("status") or "pending"),
        lang="",
        urgent=bool(row.get("urgent")),
        user_id=int(row.get("user_id") or 0),
        cosmo_user_id=str(row.get("cosmo_user_id") or ""),
        subject=room,
        detail=detail,
        contact_method="founder",
        admin_accepted_at=row.get("admin_accepted_at"),
    )
    out["room_type"] = row.get("room_type")
    out["direction"] = direction
    out["purchase_id"] = row.get("purchase_id")
    out["amount_inr"] = amount
    out["priority_fee_inr"] = row.get("priority_fee_inr")
    out["eta_hours"] = row.get("eta_hours") if row.get("eta_hours") is not None else (12 if row.get("urgent") else 144)
    out["eta_label"] = row.get("eta_label") or (
        "⚡ Priority — deliver within 12 hours"
        if row.get("urgent")
        else "📦 Standard — 4–6 business days"
    )
    out["sku"] = row.get("sku")
    out["has_image"] = bool(row.get("has_image") or row.get("image_data_url"))
    out["media_kind"] = row.get("media_kind") or None
    return out


def enrich_business_vastu_row(row: dict[str, Any]) -> dict[str, Any]:
    btype = (str(row.get("business_type") or "").strip() or "business").title()
    prop = str(row.get("property_name") or "").strip()
    photos = int(row.get("photo_count") or 0)
    detail_bits = [f"{photos} photos"] if photos else []
    if row.get("has_pdf"):
        detail_bits.append("PDF plan")
    out = _base_row(
        kind="business_vastu_pro",
        label="Business Vastu",
        order_id=str(row.get("order_id") or ""),
        created_at=row.get("created_at"),
        status=str(row.get("status") or "pending"),
        lang="",
        urgent=bool(row.get("urgent")),
        user_id=int(row.get("user_id") or 0),
        cosmo_user_id=str(row.get("cosmo_user_id") or ""),
        subject=f"{btype}" + (f" — {prop}" if prop else ""),
        detail=" · ".join(detail_bits),
        contact_method="founder",
        admin_accepted_at=row.get("admin_accepted_at"),
    )
    out["business_type"] = row.get("business_type")
    out["property_name"] = prop
    out["photo_count"] = photos
    out["has_pdf"] = bool(row.get("has_pdf"))
    out["pdf_filename"] = row.get("pdf_filename") or ""
    rooms = row.get("photo_rooms")
    out["photo_rooms"] = rooms if isinstance(rooms, list) else []
    out["amount_inr"] = row.get("amount_inr")
    out["priority_fee_inr"] = row.get("priority_fee_inr")
    out["eta_hours"] = row.get("eta_hours") if row.get("eta_hours") is not None else (12 if row.get("urgent") else 144)
    out["eta_label"] = row.get("eta_label") or (
        "⚡ Priority — deliver within 12 hours"
        if row.get("urgent")
        else "📦 Standard — 4–6 business days"
    )
    return out


def _validate_body(
    body_text: str, *, has_images: bool = False
) -> str | None:
    body = (body_text or "").strip()
    if has_images and body:
        return None
    if has_images and not body:
        return None
    if len(body) < _MIN_BODY:
        return "body_too_short"
    return None


def _resolve_order_user_id(
    order: dict[str, Any],
    attach_user_id: int | str | None = None,
) -> int:
    """Prefer explicit admin attach, then order.user_id, then cosmo_user_id → DB id."""
    if attach_user_id is not None and str(attach_user_id).strip():
        raw = str(attach_user_id).strip()
        # Allow typing COSMO123 in admin attach field.
        if raw.upper().startswith("COSMO"):
            try:
                from models import User

                row = User.query.filter(User.cosmo_user_id.ilike(raw.upper())).first()
                if row is not None:
                    return int(row.id)
            except Exception:
                return 0
        try:
            attached = int(raw)
            if attached > 0:
                return attached
        except (TypeError, ValueError):
            pass
    try:
        uid = int(order.get("user_id") or 0)
    except (TypeError, ValueError):
        uid = 0
    if uid > 0:
        return uid
    cosmo = str(order.get("cosmo_user_id") or "").strip().upper()
    if not cosmo:
        return 0
    try:
        from models import User

        row = User.query.filter(User.cosmo_user_id.ilike(cosmo)).first()
        if row is not None:
            return int(row.id)
    except Exception:
        pass
    return 0


def fulfill_numerology_with_founder_text(
    order_id: str,
    body_text: str,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    from numerology_human_orders import get_order, save_order_record
    from founder_text_pdf import render_founder_text_pdf
    import report_cache as rc

    has_images = any(bool(x) for x in (page_images or []))
    err = _validate_body(
        body_text if not pages else "\n\n".join(pages or []),
        has_images=has_images,
    )
    if err:
        return {"ok": False, "error": err}

    order = get_order(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if str(order.get("status") or "").lower() == "delivered":
        return {"ok": False, "error": "order_already_delivered"}

    user_id = int(order.get("user_id") or 0)
    if not user_id:
        return {"ok": False, "error": "missing_user_id"}

    person = order.get("person") if isinstance(order.get("person"), dict) else {}
    name = str(order.get("subject_name") or person.get("name") or "Client")
    lang = str(order.get("lang") or "en")
    oid = str(order.get("order_id") or "")

    try:
        pdf_bytes = render_founder_text_pdf(
            title="Numerology Pro Report",
            subject=name,
            subtitle="",
            lang=lang,
            body_text=body_text,
            pages=pages,
            page_images=page_images,
            order_id=oid,
            mystic_theme=True,
            prepared_by="Ashutosh Bharadwaj",
        )
    except Exception as exc:
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    params = {
        "name": name,
        "dob": person.get("dob") or "",
        "lang": lang,
        "order_id": oid,
        "source": "founder_admin",
    }
    safe = re.sub(r"[^\w\-]+", "_", name)[:60]
    report_id = rc.save(
        user_id=user_id,
        kind="numerology_pro",
        report_type="Numerology Pro",
        params=params,
        pdf_bytes=pdf_bytes,
        filename=f"Numerology_Pro_{safe}.pdf",
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "admin_lifemap"
    save_order_record(order)

    notify = _notify_pdf_ready(
        user_id,
        "Numerology report ready",
        f"{name} — My Reports mein PDF save ho gayi.",
        "numerology_pro",
        report_id,
    )

    return {
        "ok": True,
        "order_id": oid,
        "report_id": report_id,
        "user_id": user_id,
        "bytes": len(pdf_bytes),
        "kind": "numerology_pro",
        "notified": int(notify.get("sent") or 0) > 0,
    }


def fulfill_palmistry_with_founder_text(
    order_id: str,
    body_text: str,
    attach_user_id: int | str | None = None,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    """Paste founder palmistry report → branded PDF → user My Reports."""
    from palmistry_human_orders import get_order, save_order_record
    from founder_text_pdf import render_founder_text_pdf
    import report_cache as rc

    has_images = any(bool(x) for x in (page_images or []))
    err = _validate_body(
        body_text if not pages else "\n\n".join(pages or []),
        has_images=has_images,
    )
    if err:
        return {"ok": False, "error": err}

    order = get_order(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if str(order.get("status") or "").lower() == "delivered":
        return {"ok": False, "error": "order_already_delivered"}

    plan = str(order.get("plan") or "pdf").strip().lower()
    deliverable = str(
        order.get("deliverable") or ("video" if plan == "vip" else "report")
    ).strip().lower()
    if deliverable == "video" or plan == "vip":
        return {
            "ok": False,
            "error": "video_order_no_pdf",
            "detail": "Yeh WhatsApp video order hai — PDF/report deliver nahi hota.",
        }

    if not order.get("admin_accepted_at"):
        return {
            "ok": False,
            "error": "order_not_approved",
            "detail": "Pehle Approve karo — uske baad report paste / deliver open hoga.",
        }

    user_id = _resolve_order_user_id(order, attach_user_id=attach_user_id)
    if not user_id:
        return {
            "ok": False,
            "error": "missing_user_id",
            "detail": (
                "Is order pe app user id nahi hai (guest upload). "
                "Admin me user # / COSMO id attach karke dubara Send karo, "
                "ya user ko login karke naya order bhejne bolo."
            ),
        }
    # Persist recovery attach so re-deliver / ledger stays consistent.
    if int(order.get("user_id") or 0) != user_id:
        order["user_id"] = user_id
        if str(order.get("contact_method") or "") == "my_reports":
            order["contact_value"] = str(user_id)

    name = str(
        order.get("user_name") or order.get("subject") or "Client"
    ).strip() or "Client"
    lang = str(order.get("lang") or "en")
    oid = str(order.get("order_id") or "")
    writing = str(order.get("writing_hand") or "").strip().upper()
    # No "Founder-reviewed…" / writing-hand meta line — byline is the founder name only.
    try:
        pdf_bytes = render_founder_text_pdf(
            title="Palmistry Report",
            subject=name,
            subtitle="",
            lang=lang,
            body_text=body_text,
            pages=pages,
            page_images=page_images,
            order_id=oid,
            mystic_theme=True,
            prepared_by="Ashutosh Bharadwaj",
        )
    except Exception as exc:
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    params = {
        "name": name,
        "lang": lang,
        "order_id": oid,
        "public_order_id": str(order.get("public_order_id") or ""),
        "writing_hand": writing.lower() if writing else "",
        "source": "founder_admin",
    }
    safe = re.sub(r"[^\w\-]+", "_", name)[:60]
    report_id = rc.save(
        user_id=user_id,
        kind="palmistry_pro",
        report_type="Palmistry Pro",
        params=params,
        pdf_bytes=pdf_bytes,
        filename=f"Palmistry_Pro_{safe}.pdf",
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "admin_lifemap"
    order["updated_at"] = now
    save_order_record(order)

    notify = _notify_pdf_ready(
        user_id,
        "Palmistry report ready",
        f"{name} — My Reports mein Palmistry PDF save ho gayi.",
        "palmistry_pro",
        report_id,
    )

    return {
        "ok": True,
        "order_id": oid,
        "report_id": report_id,
        "user_id": user_id,
        "bytes": len(pdf_bytes),
        "kind": "palmistry_pro",
        "notified": int(notify.get("sent") or 0) > 0,
    }


def fulfill_astrovastu_with_founder_text(
    order_id: str,
    body_text: str,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    from astrovastu_human_orders import get_order, save_order_record
    from founder_text_pdf import render_founder_text_pdf
    import report_cache as rc

    has_images = any(bool(x) for x in (page_images or []))
    err = _validate_body(body_text, has_images=has_images)
    if err:
        return {"ok": False, "error": err}

    order = get_order(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if str(order.get("status") or "").lower() == "delivered":
        return {"ok": False, "error": "order_already_delivered"}

    user_id = int(order.get("user_id") or 0)
    if not user_id:
        return {"ok": False, "error": "missing_user_id"}

    room = (str(order.get("room_type") or "Room").replace("_", " ")).title()
    direction = str(order.get("direction") or "")
    subject = f"{room}" + (f" · {direction}" if direction else "")
    oid = str(order.get("order_id") or "")
    lang = "en"

    try:
        pdf_bytes = render_founder_text_pdf(
            title="AstroVastu Pro Report",
            subject=subject,
            subtitle="",
            lang=lang,
            body_text=body_text,
            pages=pages,
            page_images=page_images,
            order_id=oid,
            mystic_theme=True,
            prepared_by="Ashutosh Bharadwaj",
        )
    except Exception as exc:
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    params = {
        "name": subject,
        "room_type": order.get("room_type"),
        "direction": direction,
        "order_id": oid,
        "source": "founder_admin",
    }
    safe = re.sub(r"[^\w\-]+", "_", room)[:60]
    report_id = rc.save(
        user_id=user_id,
        kind="astrovastu_pro",
        report_type="AstroVastu Pro",
        params=params,
        pdf_bytes=pdf_bytes,
        filename=f"AstroVastu_Pro_{safe}.pdf",
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "admin_lifemap"
    save_order_record(order)

    notify = _notify_pdf_ready(
        user_id,
        "AstroVastu report ready",
        f"{subject} — My Reports mein PDF save ho gayi.",
        "astrovastu_pro",
        report_id,
    )

    return {
        "ok": True,
        "order_id": oid,
        "report_id": report_id,
        "user_id": user_id,
        "bytes": len(pdf_bytes),
        "kind": "astrovastu_pro",
        "notified": int(notify.get("sent") or 0) > 0,
    }


def fulfill_business_vastu_with_founder_text(
    order_id: str,
    body_text: str,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    from business_vastu_human_orders import get_order, save_order_record
    from founder_text_pdf import render_founder_text_pdf
    import report_cache as rc

    has_images = any(bool(x) for x in (page_images or []))
    err = _validate_body(body_text, has_images=has_images)
    if err:
        return {"ok": False, "error": err}

    order = get_order(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if str(order.get("status") or "").lower() == "delivered":
        return {"ok": False, "error": "order_already_delivered"}

    user_id = int(order.get("user_id") or 0)
    if not user_id:
        return {"ok": False, "error": "missing_user_id"}

    btype = (str(order.get("business_type") or "business").strip()).title()
    prop = str(order.get("property_name") or "").strip()
    subject = f"{btype}" + (f" — {prop}" if prop else "")
    oid = str(order.get("order_id") or "")

    try:
        pdf_bytes = render_founder_text_pdf(
            title="Business Vastu Report",
            subject=subject,
            subtitle="",
            lang="en",
            body_text=body_text,
            pages=pages,
            page_images=page_images,
            order_id=oid,
            mystic_theme=True,
            prepared_by="Ashutosh Bharadwaj",
        )
    except Exception as exc:
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    params = {
        "name": subject,
        "business_type": order.get("business_type"),
        "property_name": prop,
        "order_id": oid,
        "source": "founder_admin",
    }
    safe = re.sub(r"[^\w\-]+", "_", f"{btype}_{prop}" if prop else btype)[:60]
    report_id = rc.save(
        user_id=user_id,
        kind="business_vastu_pro",
        report_type="Business Vastu",
        params=params,
        pdf_bytes=pdf_bytes,
        filename=f"Business_Vastu_{safe}.pdf",
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "admin_lifemap"
    save_order_record(order)

    notify = _notify_pdf_ready(
        user_id,
        "Business Vastu report ready",
        f"{subject} — My Reports mein PDF save ho gayi.",
        "business_vastu_pro",
        report_id,
    )

    return {
        "ok": True,
        "order_id": oid,
        "report_id": report_id,
        "user_id": user_id,
        "bytes": len(pdf_bytes),
        "kind": "business_vastu_pro",
        "notified": int(notify.get("sent") or 0) > 0,
    }


def fulfill_birth_time_rectification_with_founder_text(
    order_id: str,
    body_text: str,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    from birth_time_rectification_orders import (
        _save_order,
        get_birth_time_rectification_order,
    )
    from founder_text_pdf import render_founder_text_pdf
    import report_cache as rc

    has_images = any(bool(x) for x in (page_images or []))
    err = _validate_body(
        body_text if not pages else "\n\n".join(pages or []),
        has_images=has_images,
    )
    if err:
        return {"ok": False, "error": err}

    order = get_birth_time_rectification_order(order_id)
    if not order:
        return {"ok": False, "error": "order_not_found"}
    if str(order.get("status") or "").lower() == "delivered":
        return {"ok": False, "error": "order_already_delivered"}

    user_id = int(order.get("user_id") or 0)
    if not user_id:
        return {"ok": False, "error": "missing_user_id"}

    name = str(order.get("full_name") or "Client")
    oid = str(order.get("order_id") or "")
    lang = str(order.get("lang") or "en")

    try:
        pdf_bytes = render_founder_text_pdf(
            title="Birth Time Rectification Report",
            subject=name,
            subtitle="",
            lang=lang,
            body_text=body_text,
            pages=pages,
            page_images=page_images,
            order_id=oid,
            mystic_theme=True,
            prepared_by="Ashutosh Bharadwaj",
        )
    except Exception as exc:
        return {"ok": False, "error": "pdf_render_failed", "detail": str(exc)}

    params = {
        "name": name,
        "dob": order.get("dob") or "",
        "approx_tob": order.get("approx_tob") or "",
        "birth_place": order.get("birth_place") or "",
        "order_id": oid,
        "source": "founder_admin",
    }
    safe = re.sub(r"[^\w\-]+", "_", name)[:60]
    report_id = rc.save(
        user_id=user_id,
        kind="birth_time_rectification",
        report_type="Birth Time Rectification",
        params=params,
        pdf_bytes=pdf_bytes,
        filename=f"Birth_Time_Rectification_{safe}.pdf",
    )
    if not report_id:
        return {"ok": False, "error": "report_save_failed"}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "delivered"
    order["delivered_at"] = now
    order["report_id"] = report_id
    order["delivery_source"] = "admin_lifemap"
    _save_order(order)

    notify = _notify_pdf_ready(
        user_id,
        "Birth time report ready",
        f"{name} — My Reports mein PDF save ho gayi.",
        "birth_time_rectification",
        report_id,
    )

    return {
        "ok": True,
        "order_id": oid,
        "report_id": report_id,
        "user_id": user_id,
        "bytes": len(pdf_bytes),
        "kind": "birth_time_rectification",
        "notified": int(notify.get("sent") or 0) > 0,
    }


def deliver_lifemap_order(
    kind: str,
    order_id: str,
    body_text: str,
    attach_user_id: int | str | None = None,
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
) -> dict[str, Any]:
    """Route admin paste → correct fulfill path. Returns {ok, ...}."""
    from founder_structure import normalize_founder_pages_and_images

    k = (kind or "").strip().lower()
    oid = (order_id or "").strip()
    page_list, img_list = normalize_founder_pages_and_images(
        body_text, pages, page_images
    )
    body = "\n\n".join(page_list)
    has_images = any(bool(x) for x in img_list)
    if not oid:
        return {"ok": False, "error": "order_id_required"}
    if not page_list and not has_images:
        return {
            "ok": False,
            "error": "body_too_short",
            "detail": f"Paste at least {_MIN_BODY} characters or add an image.",
        }
    err = _validate_body(body, has_images=has_images)
    if err:
        return {
            "ok": False,
            "error": err,
            "detail": f"Paste at least {_MIN_BODY} characters or add an image.",
        }

    # LifeMap Pro queues require Approve before PDF deliver.
    if k in (
        "love_reality_pro",
        "love_reality",
        "lr",
        "milan_pro",
        "milan",
        "ml",
        "numerology_pro",
        "numerology",
        "life_mastery",
        "nm",
        "astrovastu_pro",
        "astrovastu",
        "vastu_pro",
        "av",
        "business_vastu_pro",
        "business_vastu",
        "bv",
        "palmistry",
        "palm_scan",
        "palm",
    ):
        order, _, resolve_err = _resolve_lifemap_order(k, oid)
        if resolve_err == "order_not_found" or not order:
            return {"ok": False, "error": "order_not_found"}
        if not order.get("admin_accepted_at"):
            return {
                "ok": False,
                "error": "order_not_approved",
                "detail": "Pehle Approve karo — uske baad report paste / deliver open hoga.",
            }

    if k in ("love_reality_pro", "love_reality", "milan_pro", "milan"):
        from love_reality_telegram_deliver import fulfill_order_with_founder_text

        return fulfill_order_with_founder_text(
            oid, body, pages=page_list, page_images=img_list
        )

    if k in ("numerology_pro", "numerology", "life_mastery"):
        return fulfill_numerology_with_founder_text(
            oid, body, pages=page_list, page_images=img_list
        )

    if k in ("astrovastu_pro", "astrovastu", "vastu_pro"):
        return fulfill_astrovastu_with_founder_text(
            oid, body, pages=page_list, page_images=img_list
        )

    if k in ("business_vastu_pro", "business_vastu"):
        return fulfill_business_vastu_with_founder_text(
            oid, body, pages=page_list, page_images=img_list
        )

    if k in ("palmistry", "palm_scan", "palm"):
        return fulfill_palmistry_with_founder_text(
            oid,
            body,
            attach_user_id=attach_user_id,
            pages=page_list,
            page_images=img_list,
        )

    if k in ("birth_time_rectification", "btr", "birth_time"):
        return fulfill_birth_time_rectification_with_founder_text(
            oid, body, pages=page_list, page_images=img_list
        )

    return {"ok": False, "error": "unsupported_kind"}


def delete_lifemap_order(kind: str, order_id: str) -> dict[str, Any]:
    """Admin removes a pending LifeMap booking from the queue (soft-cancel)."""
    from datetime import datetime, timezone

    order, saver, err = _resolve_lifemap_order(kind, order_id)
    if err:
        return {"ok": False, "error": err}
    assert order is not None and saver is not None
    oid = str(order.get("order_id") or order_id).strip()

    status = str(order.get("status") or "").strip().lower()
    if status == "delivered":
        return {"ok": False, "error": "order_already_delivered"}
    if status in ("cancelled", "canceled", "deleted"):
        return {"ok": True, "already": True, "order_id": oid}

    now = datetime.now(timezone.utc).isoformat()
    order["status"] = "cancelled"
    order["cancelled_at"] = now
    order["cancelled_by"] = "admin"
    order["updated_at"] = now
    saver(order)
    return {
        "ok": True,
        "deleted": True,
        "order_id": oid,
        "status": "cancelled",
    }


def lookup_order_by_any_id(raw_id: str) -> dict[str, Any]:
    """Find a LifeMap / palmistry order by UUID, prefix, or public id (e.g. PALM-1001)."""
    needle = (raw_id or "").strip()
    if not needle:
        return {"ok": False, "found": False, "error": "order_id_required"}

    loaders: list[tuple[str, str, Any]] = []
    try:
        from palmistry_human_orders import get_order as _get_palm

        loaders.append(("palmistry", "Palmistry", _get_palm))
    except Exception:
        pass
    try:
        from love_reality_human_orders import get_order as _get_lr

        loaders.append(("love_reality_pro", "Love Reality Pro", _get_lr))
    except Exception:
        pass
    try:
        from milan_human_orders import get_order as _get_ml

        loaders.append(("milan_pro", "Kundli Milan Pro", _get_ml))
    except Exception:
        pass
    try:
        from numerology_human_orders import get_order as _get_nm

        loaders.append(("numerology_pro", "Numerology Pro", _get_nm))
    except Exception:
        pass
    try:
        from astrovastu_human_orders import get_order as _get_av

        loaders.append(("astrovastu_pro", "AstroVastu Pro", _get_av))
    except Exception:
        pass
    try:
        from business_vastu_human_orders import get_order as _get_bv

        loaders.append(("business_vastu_pro", "Business Vastu", _get_bv))
    except Exception:
        pass

    for kind, label, getter in loaders:
        try:
            order = getter(needle)
        except Exception:
            order = None
        if not order or not isinstance(order, dict):
            continue
        status = str(order.get("status") or "pending").strip().lower() or "pending"
        if status in ("delivered",):
            delivery_state = "successful"
        elif status in ("cancelled", "canceled", "deleted"):
            delivery_state = "cancelled"
        else:
            delivery_state = "pending"

        uid = 0
        try:
            uid = int(order.get("user_id") or 0)
        except (TypeError, ValueError):
            uid = 0
        cosmo = str(order.get("cosmo_user_id") or "").strip()
        name = str(
            order.get("user_name")
            or order.get("subject")
            or order.get("subject_name")
            or ""
        ).strip()
        pub = str(order.get("public_order_id") or "").strip()
        oid = str(order.get("order_id") or "").strip()
        return {
            "ok": True,
            "found": True,
            "kind": kind,
            "label": str(order.get("label") or label).strip() or label,
            "order_id": oid,
            "public_order_id": pub,
            "status": status,
            "delivery_state": delivery_state,
            "user_id": uid,
            "cosmo_user_id": cosmo,
            "user_name": name,
            "created_at": order.get("created_at"),
            "delivered_at": order.get("delivered_at"),
            "admin_accepted_at": order.get("admin_accepted_at"),
            "admin_accepted": bool(order.get("admin_accepted_at")),
            "plan": order.get("plan"),
            "deliverable": order.get("deliverable"),
            "amount_inr": order.get("amount_inr"),
            "eta_label": order.get("eta_label"),
            "contact_method": order.get("contact_method"),
            "contact_value": order.get("contact_value"),
        }

    return {
        "ok": True,
        "found": False,
        "error": "order_not_found",
        "message": "No order found for this Order ID.",
    }


def _resolve_lifemap_order(
    kind: str, order_id: str
) -> tuple[dict[str, Any] | None, Any, str | None]:
    """Return (order, save_fn, error_code)."""
    k = (kind or "").strip().lower()
    oid = (order_id or "").strip()
    if not oid:
        return None, None, "order_id_required"

    order: dict[str, Any] | None = None
    saver = None

    if k in ("love_reality_pro", "love_reality", "lr"):
        from love_reality_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
        if not order:
            from milan_human_orders import get_order as get_ml
            from milan_human_orders import save_order_record as save_ml

            order = get_ml(oid)
            saver = save_ml
    elif k in ("milan_pro", "milan", "ml"):
        from milan_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
    elif k in ("numerology_pro", "numerology", "life_mastery", "nm"):
        from numerology_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
    elif k in ("astrovastu_pro", "astrovastu", "vastu_pro", "av"):
        from astrovastu_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
    elif k in ("business_vastu_pro", "business_vastu", "bv"):
        from business_vastu_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
    elif k in ("palmistry", "palm_scan", "palm"):
        from palmistry_human_orders import get_order, save_order_record

        order = get_order(oid)
        saver = save_order_record
    else:
        return None, None, "unsupported_kind"

    if not order or saver is None:
        return None, None, "order_not_found"
    return order, saver, None


def accept_lifemap_order(kind: str, order_id: str, *, source: str = "admin") -> dict[str, Any]:
    """Admin acknowledges a LifeMap order (Telegram or web). Does not deliver PDF."""
    from datetime import datetime, timezone

    order, saver, err = _resolve_lifemap_order(kind, order_id)
    if err:
        return {"ok": False, "error": err}
    assert order is not None and saver is not None
    oid = str(order.get("order_id") or order_id).strip()

    status = str(order.get("status") or "").strip().lower()
    if status == "delivered":
        return {"ok": False, "error": "order_already_delivered"}
    if status in ("cancelled", "canceled", "deleted"):
        return {"ok": False, "error": "order_cancelled"}

    if order.get("admin_accepted_at"):
        return {
            "ok": True,
            "already": True,
            "order_id": oid,
            "admin_accepted_at": order.get("admin_accepted_at"),
            "source": order.get("admin_accepted_source") or source,
        }

    now = datetime.now(timezone.utc).isoformat()
    order["admin_accepted_at"] = now
    order["admin_accepted_source"] = (source or "admin").strip() or "admin"
    order["updated_at"] = now
    # Keep status=pending so order stays in the working delivery queue.
    saver(order)
    return {
        "ok": True,
        "accepted": True,
        "order_id": oid,
        "admin_accepted_at": now,
        "source": order["admin_accepted_source"],
    }


def unaccept_lifemap_order(kind: str, order_id: str) -> dict[str, Any]:
    """Clear admin accept so Approve is required again."""
    from datetime import datetime, timezone

    order, saver, err = _resolve_lifemap_order(kind, order_id)
    if err:
        return {"ok": False, "error": err}
    assert order is not None and saver is not None
    oid = str(order.get("order_id") or order_id).strip()
    status = str(order.get("status") or "").strip().lower()
    if status == "delivered":
        return {"ok": False, "error": "order_already_delivered"}
    order.pop("admin_accepted_at", None)
    order.pop("admin_accepted_source", None)
    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    saver(order)
    return {"ok": True, "accepted": False, "order_id": oid}


def is_lifemap_order_accepted(kind: str, order_id: str) -> bool:
    order, _, err = _resolve_lifemap_order(kind, order_id)
    if err or not order:
        return True  # stop reminders if missing
    status = str(order.get("status") or "").strip().lower()
    if status in ("delivered", "cancelled", "canceled", "deleted"):
        return True
    return bool(order.get("admin_accepted_at"))

