#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理层 - 统一的JSON数据读写接口
matches.json 是唯一数据源，HTML生成、盈亏计算、统计全部从它读取
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "docs" / "data" / "matches.json"
DOCS_DIR = ROOT_DIR / "docs"

# ============================================================
# 配置
# ============================================================
DAILY_BUDGET = 10000  # 每日总预算
CONFIDENCE_WEIGHTS = {
    "强烈推荐": 2.0,
    "推荐": 1.0,
    "谨慎推荐": 0.5,
    "不建议": 0.0,
}
CONFIDENCE_STAR_MAP = {
    "强烈推荐": "⭐⭐⭐⭐⭐",
    "推荐": "⭐⭐⭐⭐",
    "谨慎推荐": "⭐⭐⭐",
    "不建议": "⭐",
}


def load_matches() -> dict:
    """读取 matches.json"""
    if not DATA_FILE.exists():
        return {
            "version": "2.0",
            "last_update": datetime.now().isoformat(),
            "dates": {},
            "summary": {
                "total_matches": 0,
                "total_dates": 0,
                "analyzed": 0,
                "settled": 0,
                "pending": 0,
            },
        }

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_matches(data: dict) -> None:
    """保存 matches.json"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 更新统计
    all_matches = []
    for date_str, matches in data.get("dates", {}).items():
        all_matches.extend(matches)

    settled = sum(1 for m in all_matches if m.get("result"))
    pending = sum(
        1 for m in all_matches if not m.get("result") and m.get("prediction")
    )
    analyzed = sum(1 for m in all_matches if m.get("prediction"))

    data["summary"] = {
        "total_matches": len(all_matches),
        "total_dates": len(data.get("dates", {})),
        "analyzed": analyzed,
        "settled": settled,
        "pending": pending,
    }
    data["last_update"] = datetime.now().isoformat()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_match(match_data: dict) -> dict:
    """添加/更新一场比赛的分析"""
    data = load_matches()
    date_str = match_data["date"]

    if date_str not in data["dates"]:
        data["dates"][date_str] = []

    # 检查是否已存在（按 event_id 去重）
    existing_idx = None
    for i, m in enumerate(data["dates"][date_str]):
        if m.get("id") == match_data.get("id"):
            existing_idx = i
            break

    if existing_idx is not None:
        data["dates"][date_str][existing_idx] = match_data
    else:
        data["dates"][date_str].append(match_data)

    # 按时间排序
    data["dates"][date_str].sort(key=lambda m: m.get("time", "99:99"))

    save_matches(data)
    return data


def get_date(date_str: str) -> list:
    """获取某天所有比赛"""
    data = load_matches()
    return data.get("dates", {}).get(date_str, [])


def get_match(event_id: str) -> Optional[dict]:
    """按 event_id 查找比赛"""
    data = load_matches()
    for date_str, matches in data.get("dates", {}).items():
        for m in matches:
            if m.get("id") == event_id:
                return m
    return None


def update_result(event_id: str, home_score: int, away_score: int) -> Optional[dict]:
    """更新赛果，自动计算盈亏"""
    data = load_matches()

    for date_str, matches in data.get("dates", {}).items():
        for m in matches:
            if m.get("id") == event_id:
                pred = m.get("prediction", {})
                odds = m.get("odds", {})

                # 实际结果
                if home_score > away_score:
                    actual = "home_win"
                elif home_score == away_score:
                    actual = "draw"
                else:
                    actual = "away_win"

                m["result"] = {
                    "home_score": home_score,
                    "away_score": away_score,
                    "type": actual,
                    "updated_at": datetime.now().isoformat(),
                }

                # 计算盈亏
                bet_amount = pred.get("bet_amount", 0)
                pred_result = pred.get("result", "")
                predicted_odds = pred.get("best_odds", odds.get(
                    {"home_win": "home", "draw": "draw", "away_win": "away"}.get(
                        pred_result, "away"
                    ),
                    2.0,
                ))

                if pred_result == actual:
                    profit = bet_amount * float(predicted_odds) - bet_amount
                    m["pnl"] = {"profit": round(profit, 2), "hit": True}
                else:
                    m["pnl"] = {"profit": round(-bet_amount, 2), "hit": False}

                save_matches(data)
                return m

    return None


def update_batch_results(results: List[Dict]) -> dict:
    """批量更新赛果
    results: [{"event_id": "...", "home_score": 2, "away_score": 1}, ...]
    """
    data = load_matches()
    for r in results:
        update_result(r["event_id"], r["home_score"], r["away_score"])

    data = load_matches()  # 重新加载
    save_matches(data)
    return data


def auto_allocate_budget(data: dict, date_str: str) -> dict:
    """为某天的所有pending比赛自动分配预算"""
    matches = data.get("dates", {}).get(date_str, [])

    # 计算权重总和
    total_weight = 0
    for m in matches:
        if not m.get("result"):
            confidence = m.get("prediction", {}).get("confidence", "推荐")
            total_weight += CONFIDENCE_WEIGHTS.get(confidence, 1.0)

    if total_weight == 0:
        return data

    # 分配预算
    for m in matches:
        if not m.get("result"):
            confidence = m.get("prediction", {}).get("confidence", "推荐")
            weight = CONFIDENCE_WEIGHTS.get(confidence, 1.0)
            bet_amount = round((weight / total_weight) * DAILY_BUDGET, 2)
            if "prediction" not in m:
                m["prediction"] = {}
            m["prediction"]["bet_amount"] = bet_amount

    save_matches(data)
    return data


def get_pnl_summary(data: dict = None) -> dict:
    """获取盈亏汇总"""
    if data is None:
        data = load_matches()

    total_bet = 0
    total_profit = 0
    hits = 0
    misses = 0
    pending = 0

    for date_str, matches in data.get("dates", {}).items():
        for m in matches:
            bet = m.get("prediction", {}).get("bet_amount", 0)
            pnl = m.get("pnl", {})

            if pnl:
                total_bet += bet
                total_profit += pnl.get("profit", 0)
                if pnl.get("hit"):
                    hits += 1
                else:
                    misses += 1
            elif m.get("prediction"):
                pending += 1

    return {
        "total_bet": round(total_bet, 2),
        "total_profit": round(total_profit, 2),
        "net_pnl": round(total_profit, 2),
        "roi": round((total_profit / total_bet * 100), 2) if total_bet > 0 else 0,
        "hits": hits,
        "misses": misses,
        "pending": pending,
        "win_rate": round((hits / (hits + misses) * 100), 2) if (hits + misses) > 0 else 0,
    }


def export_markdown(event_id: str) -> str:
    """将一场比赛从JSON导出为Markdown"""
    m = get_match(event_id)
    if not m:
        return ""

    a = m.get("analysis", {})
    scores = a.get("scores", {})
    dims = a.get("dimensions", [])
    pred = m.get("prediction", {})
    odds = m.get("odds", {})
    form = m.get("recent_form", {})

    md = f"""# {m['home']} vs {m['away']} 分析报告

## 比赛信息
| 项目 | 内容 |
|------|------|
| 比赛 | {m['home']} vs {m['away']} |
| 时间 | {m['date']} {m.get('time', '')} |
| 分组 | {m.get('group', '?')}组 |
| 场地 | {m.get('venue', '待定')} |

## 赔率数据
| 结果 | 赔率 |
|------|:---:|
| 主胜 | {odds.get('home', '-')} |
| 平局 | {odds.get('draw', '-')} |
| 客胜 | {odds.get('away', '-')} |

## 7维度评分
| 维度 | 权重 | {m['home']} | {m['away']} |
|------|:---:|:---:|:---:|
"""

    for d in dims:
        md += f"| {d['name']} | {d['weight']}% | {d['home']} | {d['away']} |\n"

    md += f"""
| **总分** | **100%** | **{scores.get('home', 0)}** | **{scores.get('away', 0)}** |

## 预测
- 推荐: {pred.get('label', '-')}
- 比分: {pred.get('score', '-')}
- 信心: {a.get('confidence_stars', '')} {a.get('confidence_label', '')}
- 赔率: {pred.get('best_odds', '-')}
"""

    if m.get("notes"):
        md += f"\n## 备注\n{m['notes']}\n"

    return md


def migrate_from_markdown() -> dict:
    """从现有 Markdown 文件迁移数据到 JSON"""
    md_files = list(DOCS_DIR.glob("*_分析报告.md"))

    if not md_files:
        print("No markdown files found to migrate")
        return load_matches()

    data = load_matches()
    if data.get("dates") and sum(len(v) for v in data["dates"].values()) > 0:
        print("JSON already has data, skipping migration")
        return data

    print(f"Migrating {len(md_files)} markdown files...")

    for filepath in md_files:
        content = filepath.read_text(encoding="utf-8")
        filename = filepath.stem
        parts = filename.split("_")
        date_str = parts[0]
        teams = parts[1].split("vs") if "vs" in parts[1] else ["", ""]
        home_team = teams[0].strip()
        away_team = teams[1].strip() if len(teams) > 1 else ""

        # 提取分组
        group_match = re.search(r'Group\s+([A-L])', content, re.IGNORECASE)
        group = group_match.group(1).upper() if group_match else "?"

        # 提取赔率
        odds = {}
        for key, pattern in [
            ("home", r'主胜.*?(\d+\.?\d*)'),
            ("draw", r'平局.*?(\d+\.?\d*)'),
            ("away", r'客胜.*?(\d+\.?\d*)'),
        ]:
            m = re.search(pattern, content)
            if m:
                try:
                    odds[key] = float(m.group(1))
                except:
                    pass

        # 提取预测
        rec_match = re.search(r'推荐结果\*\*[：:]\s*(.+?)(?:\n|$)', content)
        label = rec_match.group(1).strip() if rec_match else ""

        score_match = re.search(r'预测比分\*\*[：:]\s*(\d+\s*-\s*\d+)', content)
        score = score_match.group(1).replace(" ", "") if score_match else ""

        pred_result = "home_win"
        if "客胜" in label or "客胜" in content[content.find("推荐"):][:50] if "推荐" in content else "":
            pred_result = "away_win"
        elif "平局" in label:
            pred_result = "draw"

        # 提取信心
        conf_match = re.search(r'信心指数.*?(\d+)%', content)
        conf_pct = float(conf_match.group(1)) if conf_match else 50
        if conf_pct >= 75:
            conf_label, conf_stars = "强烈推荐", "⭐⭐⭐⭐⭐"
        elif conf_pct >= 60:
            conf_label, conf_stars = "推荐", "⭐⭐⭐⭐"
        elif conf_pct >= 40:
            conf_label, conf_stars = "谨慎推荐", "⭐⭐⭐"
        else:
            conf_label, conf_stars = "不建议", "⭐"

        # 提取比分
        score_parts = score.split("-") if score else ["0", "0"]

        match_entry = {
            "id": f"migrated_{date_str}_{home_team}",
            "date": date_str,
            "time": m.group(1).strip() if (m := re.search(r'时间\*\*[：:]\s*(.+?)(?:\n|\|)', content)) else "",
            "group": group,
            "home": home_team,
            "away": away_team,
            "odds": odds,
            "analysis": {
                "scores": {"home": 40, "away": 70},
                "dimensions": [],
                "confidence": conf_pct,
                "confidence_label": conf_label,
                "confidence_stars": conf_stars,
            },
            "prediction": {
                "result": pred_result,
                "label": label,
                "score": score,
                "bet_amount": 0,
                "best_odds": odds.get({"home_win": "home", "draw": "draw", "away_win": "away"}[pred_result], 2.0),
            },
            "result": None,
            "notes": "",
            "created_at": datetime.now().isoformat(),
        }

        if date_str not in data["dates"]:
            data["dates"][date_str] = []
        data["dates"][date_str].append(match_entry)
        print(f"  Migrated: {home_team} vs {away_team}")

    save_matches(data)
    print(f"Migration complete: {sum(len(v) for v in data['dates'].values())} matches")
    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据管理工具")
    parser.add_argument("action", choices=["migrate", "list", "export", "add-match", "auto-budget", "update-result"])
    parser.add_argument("--date", help="日期")
    parser.add_argument("--event-id", help="比赛ID")
    parser.add_argument("--file", help="JSON文件路径（add-match用）")
    parser.add_argument("--json-str", help="JSON字符串（add-match用）")
    parser.add_argument("--home-score", type=int, help="主队进球（update-result用）")
    parser.add_argument("--away-score", type=int, help="客队进球（update-result用）")

    args = parser.parse_args()

    if args.action == "migrate":
        data = migrate_from_markdown()
        print(f"Total matches: {data['summary']['total_matches']}")

    elif args.action == "list":
        data = load_matches()
        pnl = get_pnl_summary(data)
        print(f"盈亏: CNY{pnl['net_pnl']:+.2f} | 命中 {pnl['hits']}/{pnl['hits']+pnl['misses']} | ROI {pnl['roi']}%")
        print()
        for date_str in sorted(data.get("dates", {}).keys()):
            matches = data["dates"][date_str]
            print(f"{date_str} ({len(matches)}场):")
            for m in matches:
                pred = m.get("prediction", {})
                result_str = ""
                if m.get("result"):
                    r = m["result"]
                    hit = m.get("pnl", {}).get("hit", False)
                    p = m.get("pnl", {}).get("profit", 0)
                    result_str = f" → {r['home_score']}-{r['away_score']} ({'✅' if hit else '❌'} CNY{p:+.0f})"
                print(f"  [{m.get('group','?')}组] {m['home']} vs {m['away']} | {pred.get('label','未分析')} | {pred.get('score','?')}{result_str}")

    elif args.action == "export":
        if not args.event_id:
            parser.error("export 需要 --event-id")
        md = export_markdown(args.event_id)
        print(md)

    elif args.action == "add-match":
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                match_data = json.load(f)
        elif args.json_str:
            match_data = json.loads(args.json_str)
        else:
            print("请输入 JSON 数据（从 stdin 读取，Ctrl+D 结束）:")
            match_data = json.load(sys.stdin)

        data = add_match(match_data)
        print(f"添加成功: {match_data.get('home')} vs {match_data.get('away')} [{match_data.get('date')}]")

    elif args.action == "auto-budget":
        if not args.date:
            parser.error("auto-budget 需要 --date")
        data = load_matches()
        data = auto_allocate_budget(data, args.date)
        for m in data["dates"].get(args.date, []):
            pred = m.get("prediction", {})
            print(f"  {m['home']} vs {m['away']}: CNY{pred.get('bet_amount', 0):,.2f} ({pred.get('label','?')})")
        print("自动分配完成")

    elif args.action == "update-result":
        if not args.event_id or args.home_score is None or args.away_score is None:
            parser.error("update-result 需要 --event-id --home-score --away-score")
        result = update_result(args.event_id, args.home_score, args.away_score)
        if result:
            pnl = result.get("pnl", {})
            print(f"更新: {result['home']} {args.home_score}-{args.away_score} {result['away']} → {'✅命中' if pnl.get('hit') else '❌未中'} CNY{pnl.get('profit',0):+.2f}")
            save_matches(load_matches())
        else:
            print(f"未找到比赛: {args.event_id}")
