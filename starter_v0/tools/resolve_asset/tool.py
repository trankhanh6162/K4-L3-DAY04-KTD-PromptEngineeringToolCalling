from __future__ import annotations

import json
import re
from typing import Any

from tools._shared import ROOT, err, fold_text, terms


ASSET_FILE = ROOT / "helpdesk_data" / "assets.json"
USER_FILE = ROOT / "helpdesk_data" / "users.json"

# Normalise asset-ID-like strings: "lt204" → "LT-204", "lt 204" → "LT-204"
_ID_LIKE = re.compile(
    r"^(LT|DT|MB|PR|RM)\s*[-_.]?\s*(\d{1,4})$", re.IGNORECASE
)


def _normalise_id(raw: str) -> str | None:
    """Try to normalise a string into a canonical asset ID (e.g. LT-204)."""
    m = _ID_LIKE.match(raw.strip())
    if m:
        return f"{m.group(1).upper()}-{m.group(2).zfill(3)}"
    return None


def _score_asset(asset: dict[str, Any], query_terms: set[str], query_raw: str, users_by_id: dict[str, dict]) -> tuple[float, str]:
    """Return (score, match_reason) for a single asset against the query."""
    score = 0.0
    reasons: list[str] = []

    # 1. Exact or normalised ID match
    normalised = _normalise_id(query_raw)
    if normalised and normalised == asset["asset_id"]:
        score += 100
        reasons.append(f"exact_id_match:{asset['asset_id']}")
        return score, "; ".join(reasons)

    asset_id_lower = asset["asset_id"].lower()

    # 2. Partial ID match (query contains the numeric part or prefix)
    for term in query_terms:
        if term in asset_id_lower or asset_id_lower.endswith(term):
            score += 40
            reasons.append(f"partial_id_match:{term}")

    # 3. Model / manufacturer match
    model_terms = terms(asset.get("model", ""))
    mfr_terms = terms(asset.get("manufacturer", ""))
    model_overlap = query_terms & model_terms
    mfr_overlap = query_terms & mfr_terms
    if model_overlap:
        score += 30 * len(model_overlap)
        reasons.append(f"model_match:{','.join(sorted(model_overlap))}")
    if mfr_overlap:
        score += 20 * len(mfr_overlap)
        reasons.append(f"manufacturer_match:{','.join(sorted(mfr_overlap))}")

    # 4. Type match
    type_val = fold_text(asset.get("type", ""))
    query_folded = fold_text(query_raw)
    if type_val and type_val in query_folded:
        score += 10
        reasons.append(f"type_match:{type_val}")

    # 5. Assigned employee match (by ID or display_name)
    assigned_to = asset.get("assigned_to")
    if assigned_to:
        user = users_by_id.get(assigned_to, {})
        display_name = user.get("display_name", "")
        name_terms = terms(display_name)
        emp_id_lower = assigned_to.lower()
        if emp_id_lower in query_folded:
            score += 25
            reasons.append(f"employee_id_match:{assigned_to}")
        name_overlap = query_terms & name_terms
        if name_overlap:
            score += 20 * len(name_overlap)
            reasons.append(f"employee_name_match:{','.join(sorted(name_overlap))}")

    # 6. Location match
    location_terms = terms(asset.get("location", ""))
    loc_overlap = query_terms & location_terms
    if loc_overlap:
        score += 10 * len(loc_overlap)
        reasons.append(f"location_match:{','.join(sorted(loc_overlap))}")

    return score, "; ".join(reasons) if reasons else "no_match"


def resolve_asset(
    query: str = "",
    max_results: int = 5,
) -> dict[str, Any]:
    """Fuzzy-match a user query to registered assets.

    Accepts partial/malformed asset IDs, model names, manufacturer names,
    employee names/IDs, device types, or locations. Returns ranked matches
    so the agent can confirm the intended device before proceeding.
    """
    try:
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "tool": "resolve_asset",
                "error": "missing_query",
                "message": "Provide a device identifier, model name, employee name, or description.",
            }

        query_clean = query.strip()
        query_terms_set = terms(query_clean)
        limit = min(10, max(1, int(max_results or 5)))

        # Load assets
        asset_data = json.loads(ASSET_FILE.read_text(encoding="utf-8"))
        assets: list[dict[str, Any]] = asset_data.get("assets", [])

        # Load users for employee-name matching
        users_by_id: dict[str, dict] = {}
        try:
            user_data = json.loads(USER_FILE.read_text(encoding="utf-8"))
            users_by_id = {u["employee_id"]: u for u in user_data.get("users", [])}
        except Exception:
            pass  # degrade gracefully if users.json is missing

        # Score each asset
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for asset in assets:
            score, reason = _score_asset(asset, query_terms_set, query_clean, users_by_id)
            if score > 0:
                scored.append((score, reason, asset))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        matches = []
        for score, reason, asset in top:
            matches.append({
                "asset_id": asset["asset_id"],
                "manufacturer": asset.get("manufacturer"),
                "model": asset.get("model"),
                "type": asset.get("type"),
                "assigned_to": asset.get("assigned_to"),
                "location": asset.get("location"),
                "match_score": round(score, 1),
                "match_reason": reason,
            })

        if not matches:
            return {
                "tool": "resolve_asset",
                "query": query_clean,
                "matches": [],
                "message": "No assets matched the query. Ask the user for a valid asset ID.",
            }

        return {
            "tool": "resolve_asset",
            "query": query_clean,
            "match_count": len(matches),
            "matches": matches,
            "hint": "If exactly one match, use its asset_id directly. If multiple, present options to the user via clarify(choice).",
        }
    except Exception as exc:
        return err("resolve_asset", exc)
