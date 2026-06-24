#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预测跟踪与盈亏记录模块
每场直投胜/平/负，每日总预算 10000，自动记录盈亏
"""

import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).resolve().parent
TRACKER_DIR = SCRIPT_DIR.parent / "data" / "tracker"
DEFAULT_BUDGET = 10000


# ============================================================
# 数据模型
# ============================================================

def default_tracker_data() -> Dict:
    return {
        "config": {
            "daily_budget": DEFAULT_BUDGET,
            "currency": "CNY",
        },
        "predictions": [],
        "summary": {
            "total_predictions": 0,
            "correct": 0,
            "incorrect": 0,
            "pending": 0,
            "total_invested": 0.0,
            "total_returned": 0.0,
            "net_profit": 0.0,
            "roi": 0.0,
            "win_rate": 0.0,
        },
    }


def default_prediction(date: str, match: str, group: str,
                       home_team: str, away_team: str,
                       prediction: str, prediction_label: str,
                       odds: float, confidence: str,
                       reason: str = "") -> Dict:
    return {
        "id": f"pred_{int(time.time())}_{hash(match) % 10000:04d}",
        "date": date,
        "match": match,
        "group": group,
        "home_team": home_team,
        "away_team": away_team,
        "prediction": prediction,          # home_win / draw / away_win
        "prediction_label": prediction_label,  # 中文标签
        "odds": odds,
        "confidence": confidence,           # 强烈推荐/推荐/谨慎推荐/不建议
        "reason": reason,
        "bet_amount": 0.0,                  # 分配金额（后续计算）
        "status": "pending",                # pending / won / lost / void
        "actual_result": None,              # home_win / draw / away_win
        "profit_loss": 0.0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": None,
    }


# ============================================================
# Tracker 类
# ============================================================

class PredictionTracker:
    """预测跟踪器"""

    def __init__(self, tracker_dir: Path = TRACKER_DIR):
        self.tracker_dir = tracker_dir
        self.tracker_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = tracker_dir / "predictions.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return default_tracker_data()

    def _save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ---- 记录预测 ----

    def add_prediction(self, date: str, match: str, group: str,
                       home_team: str, away_team: str,
                       prediction: str, prediction_label: str,
                       odds: float, confidence: str,
                       reason: str = "") -> Dict:
        """添加一条预测记录，自动均分当日预算"""
        pred = default_prediction(
            date, match, group, home_team, away_team,
            prediction, prediction_label, odds, confidence, reason
        )

        self.data["predictions"].append(pred)

        # 重新均分当日预算
        budget = self.data["config"]["daily_budget"]
        day_preds = [p for p in self.data["predictions"] if p["date"] == date and p["status"] == "pending"]
        per_bet = round(budget / len(day_preds), 2) if day_preds else 0
        for p in day_preds:
            p["bet_amount"] = per_bet

        self._update_summary()
        self._save()
        return pred

    def add_predictions_batch(self, predictions: List[Dict]) -> List[Dict]:
        """批量添加预测（同一天的多场比赛）"""
        # 按当天预算平分
        n = len(predictions)
        if n == 0:
            return []

        budget = self.data["config"]["daily_budget"]
        per_bet = round(budget / n, 2)

        added = []
        for p in predictions:
            p["bet_amount"] = per_bet
            self.data["predictions"].append(p)
            added.append(p)

        self._update_summary()
        self._save()
        return added

    # ---- 更新赛果 ----

    def update_result(self, pred_id: str, actual_result: str) -> Optional[Dict]:
        """更新单条预测的实际结果"""
        for pred in self.data["predictions"]:
            if pred["id"] == pred_id:
                pred["actual_result"] = actual_result
                pred["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 计算盈亏
                if actual_result == pred["prediction"]:
                    pred["status"] = "won"
                    pred["profit_loss"] = round(pred["bet_amount"] * pred["odds"] - pred["bet_amount"], 2)
                else:
                    pred["status"] = "lost"
                    pred["profit_loss"] = round(-pred["bet_amount"], 2)

                self._update_summary()
                self._save()
                return pred

        return None

    def update_day_results(self, date: str, results: Dict[str, str]):
        """批量更新某天的赛果
        results: {match_key: actual_result}
        match_key 格式: "home_team vs away_team"
        """
        updated = []
        for pred in self.data["predictions"]:
            if pred["date"] != date:
                continue
            match_key = f"{pred['home_team']} vs {pred['away_team']}"
            if match_key in results:
                actual = results[match_key]
                if pred["actual_result"] is None:
                    pred["actual_result"] = actual
                    pred["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if actual == pred["prediction"]:
                        pred["status"] = "won"
                        pred["profit_loss"] = round(pred["bet_amount"] * pred["odds"] - pred["bet_amount"], 2)
                    else:
                        pred["status"] = "lost"
                        pred["profit_loss"] = round(-pred["bet_amount"], 2)

                    updated.append(pred)

        if updated:
            self._update_summary()
            self._save()
        return updated

    # ---- 统计 ----

    def _update_summary(self):
        preds = self.data["predictions"]
        total = len(preds)
        won = sum(1 for p in preds if p["status"] == "won")
        lost = sum(1 for p in preds if p["status"] == "lost")
        pending = sum(1 for p in preds if p["status"] == "pending")

        total_invested = sum(p["bet_amount"] for p in preds if p["status"] in ("won", "lost"))
        total_returned = sum(p["bet_amount"] * p["odds"] for p in preds if p["status"] == "won")
        net_profit = round(total_returned - total_invested, 2)
        roi = round(net_profit / total_invested * 100, 2) if total_invested > 0 else 0.0
        win_rate = round(won / (won + lost) * 100, 2) if (won + lost) > 0 else 0.0

        self.data["summary"] = {
            "total_predictions": total,
            "correct": won,
            "incorrect": lost,
            "pending": pending,
            "total_invested": round(total_invested, 2),
            "total_returned": round(total_returned, 2),
            "net_profit": net_profit,
            "roi": roi,
            "win_rate": win_rate,
        }

    def get_summary(self) -> Dict:
        return self.data["summary"]

    def get_predictions_by_date(self, date: str) -> List[Dict]:
        return [p for p in self.data["predictions"] if p["date"] == date]

    def get_pending(self) -> List[Dict]:
        return [p for p in self.data["predictions"] if p["status"] == "pending"]

    def get_all(self) -> Dict:
        return self.data

    # ---- 导出报告 ----

    def generate_report(self, date: Optional[str] = None) -> str:
        """生成可读的盈亏报告"""
        lines = []
        summary = self.data["summary"]

        lines.append("=" * 60)
        lines.append("  预测跟踪 · 盈亏报告")
        lines.append("=" * 60)
        lines.append("")

        # 总体统计
        lines.append("  总体统计")
        lines.append(f"    总预测数: {summary['total_predictions']}")
        lines.append(f"    命中:     {summary['correct']}  |  未命中: {summary['incorrect']}  |  待结算: {summary['pending']}")
        lines.append(f"    总投入:   ¥{summary['total_invested']:,.2f}")
        lines.append(f"    总回报:   ¥{summary['total_returned']:,.2f}")

        profit_color = "🟢" if summary["net_profit"] >= 0 else ""
        lines.append(f"    净盈亏:   {profit_color} ¥{summary['net_profit']:+,.2f}")
        lines.append(f"    ROI:      {summary['roi']:+.2f}%")
        lines.append(f"    命中率:   {summary['win_rate']:.1f}%")

        # 按日期分组
        if date:
            preds = self.get_predictions_by_date(date)
            lines.append("")
            lines.append(f"  {date} 明细")
        else:
            # 按日期倒序
            dates = sorted(set(p["date"] for p in self.data["predictions"]), reverse=True)
            preds = self.data["predictions"]

        lines.append("")
        lines.append(f"  {'比赛':<25} {'预测':<10} {'赔率':>6} {'投注':>10} {'结果':<6} {'盈亏':>10}")
        lines.append(f"  {'─'*65}")

        for p in preds:
            if date and p["date"] != date:
                continue
            match_short = f"{p['home_team'][:8]} vs {p['away_team'][:8]}"
            status_icon = {"won": "✅", "lost": "", "pending": "⏳"}.get(p["status"], "?")
            pl_str = f"¥{p['profit_loss']:+,.2f}" if p["status"] != "pending" else "-"

            lines.append(
                f"  {match_short:<25} {p['prediction_label']:<10} {p['odds']:>6.2f} "
                f"¥{p['bet_amount']:>9,.2f} {status_icon} {pl_str:>10}"
            )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# ============================================================
# CLI 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="预测跟踪与盈亏记录")
    parser.add_argument("action", choices=["report", "add", "update", "status"], help="操作类型")
    parser.add_argument("--date", help="日期 YYYY-MM-DD")
    parser.add_argument("--match", help="比赛描述 (add/update)")
    parser.add_argument("--prediction", help="预测结果: home_win/draw/away_win (add)")
    parser.add_argument("--odds", type=float, help="赔率 (add)")
    parser.add_argument("--result", help="实际结果: home_win/draw/away_win (update)")
    parser.add_argument("--confidence", default="推荐", help="信心等级 (add)")
    parser.add_argument("--reason", default="", help="理由 (add)")

    args = parser.parse_args()
    tracker = PredictionTracker()

    if args.action == "report":
        print(tracker.generate_report(args.date))

    elif args.action == "status":
        s = tracker.get_summary()
        print(f"总预测: {s['total_predictions']} | 命中: {s['correct']} | 未中: {s['incorrect']} | 待结算: {s['pending']}")
        profit_icon = "+" if s["net_profit"] >= 0 else ""
        print(f"净盈亏: ¥{s['net_profit']:+,.2f} | ROI: {s['roi']:+.2f}% | 命中率: {s['win_rate']:.1f}%")

    elif args.action == "add":
        if not args.match or not args.prediction or not args.odds:
            parser.error("add 需要 --match --prediction --odds")
        parts = args.match.split(" vs ")
        home = parts[0].strip() if len(parts) > 0 else "?"
        away = parts[1].strip() if len(parts) > 1 else "?"
        date = args.date or datetime.now().strftime("%Y-%m-%d")

        # 中文标签映射
        label_map = {"home_win": "主胜", "draw": "平局", "away_win": "客胜"}
        label = label_map.get(args.prediction, args.prediction)

        pred = tracker.add_prediction(
            date=date, match=args.match, group="",
            home_team=home, away_team=away,
            prediction=args.prediction, prediction_label=label,
            odds=args.odds, confidence=args.confidence, reason=args.reason
        )
        print(f"已记录: {pred['id']} | {args.match} | {label} @ {args.odds} | 投注 ¥{pred['bet_amount']:,.2f}")

    elif args.action == "update":
        if not args.match or not args.result:
            parser.error("update 需要 --match --result")
        # 通过比赛名查找最近的 pending 预测
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        preds = tracker.get_predictions_by_date(date)
        for p in preds:
            if args.match.lower() in p["match"].lower() and p["status"] == "pending":
                updated = tracker.update_result(p["id"], args.result)
                if updated:
                    status = "✅ 命中" if updated["status"] == "won" else "❌ 未中"
                    print(f"{status} | {p['match']} | 盈亏: ¥{updated['profit_loss']:+,.2f}")
                break


if __name__ == "__main__":
    main()
