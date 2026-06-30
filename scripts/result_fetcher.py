#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛果自动拉取 - 从 ESPN API 批量获取比赛结果并更新盈亏
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "docs" / "data" / "matches.json"


def fetch_espn_results(date_str: str) -> list:
    """通过 curl 从 ESPN API 拉取指定日期的比赛结果
    返回: [{"event_id": "...", "home": "...", "away": "...", "home_score": 3, "away_score": 1}, ...]
    """
    date_clean = date_str.replace("-", "")
    cmd = [
        "curl", "-s",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date_clean}",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"[Error] ESPN fetch failed: {e}", file=sys.stderr)
        return []

    results = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        status = comp.get("status", {}).get("type", {}).get("name", "")

        # 只处理已结束的比赛
        if status not in ("STATUS_FINAL", "STATUS_FULL_TIME", "STATUS_AET", "STATUS_PENALTY"):
            continue

        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_score = int(home.get("score", 0) or 0)
        away_score = int(away.get("score", 0) or 0)

        results.append({
            "event_id": event.get("id", ""),
            "date": date_str,
            "home": home.get("team", {}).get("displayName", ""),
            "away": away.get("team", {}).get("displayName", ""),
            "home_score": home_score,
            "away_score": away_score,
        })

    return results


def update_results(date_str: str) -> dict:
    """拉取赛果并更新到 matches.json"""
    # 导入 data_manager
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from data_manager import load_matches, save_matches, update_result

    print(f"Fetching results for {date_str}...")
    fetched = fetch_espn_results(date_str)

    if not fetched:
        print(f"No finished matches found for {date_str}")
        return load_matches()

    data = load_matches()
    updated = 0
    pnl_summary = {"wins": 0, "losses": 0, "profit": 0.0}

    for r in fetched:
        event_id = r["event_id"]

        # 查找对应比赛
        match_found = None
        for ds, matches in data.get("dates", {}).items():
            for m in matches:
                if m.get("id") == event_id or (m.get("home") == r["home"] and m.get("date") == date_str):
                    match_found = m
                    break

        if match_found:
            result = update_result(event_id, r["home_score"], r["away_score"])
            if result:
                updated += 1
                pnl = result.get("pnl", {})
                if pnl.get("hit"):
                    pnl_summary["wins"] += 1
                else:
                    pnl_summary["losses"] += 1
                pnl_summary["profit"] += pnl.get("profit", 0)
                print(
                    f"  {result['home']} {r['home_score']}-{r['away_score']} {result['away']} "
                    f"→ {'✅' if pnl.get('hit') else '❌'} "
                    f"¥{pnl.get('profit', 0):+.2f}"
                )

    if updated == 0:
        print("No matching predictions found")

    # 重新加载并保存
    data = load_matches()
    save_matches(data)

    # 打印汇总
    print(f"\n{'='*40}")
    print(f"Updated {updated} results for {date_str}")
    print(f"Wins: {pnl_summary['wins']}, Losses: {pnl_summary['losses']}")
    print(f"Net P&L: ¥{pnl_summary['profit']:+.2f}")

    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="赛果自动拉取")
    parser.add_argument("date", help="日期 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="仅拉取不更新")

    args = parser.parse_args()

    if args.dry_run:
        results = fetch_espn_results(args.date)
        print(f"Found {len(results)} finished matches for {args.date}:")
        for r in results:
            print(f"  {r['home']} {r['home_score']}-{r['away_score']} {r['away']}")
    else:
        update_results(args.date)
