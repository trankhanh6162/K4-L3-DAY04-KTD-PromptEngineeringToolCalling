from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS


def test_resolve_asset():
    func = TOOL_FUNCTIONS.get("resolve_asset")
    assert func is not None, "resolve_asset not registered in TOOL_FUNCTIONS"

    # Case 1: Exact ID match (malformed → normalised)
    res1 = func(query="lt204")
    print("[1] Fuzzy ID 'lt204':", res1)
    assert res1.get("match_count", 0) >= 1
    assert res1["matches"][0]["asset_id"] == "LT-204"
    assert res1["matches"][0]["match_score"] >= 100
    print("    ✅ Exact ID normalisation works")

    # Case 2: ID with space
    res2 = func(query="LT 204")
    print("[2] Fuzzy ID 'LT 204':", res2)
    assert res2["matches"][0]["asset_id"] == "LT-204"
    print("    ✅ Spaced ID normalisation works")

    # Case 3: Model name search
    res3 = func(query="thinkpad")
    print("[3] Model search 'thinkpad':", res3)
    assert any(m["asset_id"] == "LT-204" for m in res3["matches"])
    print("    ✅ Model name matching works")

    # Case 4: Manufacturer search
    res4 = func(query="HP desktop")
    print("[4] Manufacturer search 'HP desktop':", res4)
    assert any(m["asset_id"] == "DT-031" for m in res4["matches"])
    print("    ✅ Manufacturer + type matching works")

    # Case 5: Employee name search
    res5 = func(query="An Nguyen")
    print("[5] Employee name 'An Nguyen':", res5)
    assert any(m["asset_id"] == "LT-204" for m in res5["matches"])
    print("    ✅ Employee name matching works")

    # Case 6: Location search
    res6 = func(query="printer floor 4")
    print("[6] Location search 'printer floor 4':", res6)
    assert any(m["asset_id"] == "PR-404" for m in res6["matches"])
    print("    ✅ Location + type matching works")

    # Case 7: Partial numeric ID
    res7 = func(query="404")
    print("[7] Partial ID '404':", res7)
    assert any(m["asset_id"] == "PR-404" for m in res7["matches"])
    print("    ✅ Partial numeric matching works")

    # Case 8: Missing query
    res8 = func(query="")
    print("[8] Empty query:", res8)
    assert res8.get("error") == "missing_query"
    print("    ✅ Missing query error works")

    # Case 9: No match
    res9 = func(query="zzzznotexist")
    print("[9] No match 'zzzznotexist':", res9)
    assert res9.get("match_count", 0) == 0 or len(res9.get("matches", [])) == 0
    print("    ✅ No match handled correctly")

    # Case 10: Employee ID search
    res10 = func(query="EMP-1005")
    print("[10] Employee ID 'EMP-1005':", res10)
    assert any(m["asset_id"] == "LT-318" for m in res10["matches"])
    print("    ✅ Employee ID matching works")

    print("\n✅ All resolve_asset unit tests PASSED successfully!")


if __name__ == "__main__":
    test_resolve_asset()
