#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界杯数据抓取模块
主数据源：ESPN API（免费、稳定、数据丰富）
降级数据源：WebSearch（通过Claude工具调用）
"""

import argparse
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))  # 北京时间 UTC+8
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# 修复Windows终端编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置
# ============================================================
ESPN_BASE = "https://site.api.espn.com/apis"
ESPN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# 缓存TTL（秒）
CACHE_TTL = {
    "matches": 300,           # 5分钟
    "odds": 1800,             # 30分钟
    "schedules": 86400,       # 24小时
    "standings": 43200,       # 12小时
    "head-to-head": 2592000,  # 30天
    "teams": 86400,           # 24小时
}

# ESPN 状态码映射
STATUS_MAP = {
    "STATUS_SCHEDULED": "未开始",
    "STATUS_IN_PROGRESS": "进行中",
    "STATUS_HALFTIME": "中场休息",
    "STATUS_END_PERIOD": "半场结束",
    "STATUS_FINAL": "已结束",
    "STATUS_FULL_TIME": "已结束",
    "STATUS_AET": "加时结束",
    "STATUS_PENALTY": "点球大战结束",
    "STATUS_POSTPONED": "推迟",
    "STATUS_CANCELLED": "取消",
}

# 脚本所在目录
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"


# ============================================================
# 工具函数
# ============================================================

def american_to_decimal(odds) -> Optional[float]:
    """美式赔率转欧赔（小数格式）
    正数: decimal = (odds / 100) + 1
    负数: decimal = (100 / |odds|) + 1
    """
    if odds is None:
        return None
    if isinstance(odds, str):
        odds = parse_american_odds(odds)
    if odds is None:
        return None
    if odds > 0:
        return round((odds / 100) + 1, 2)
    elif odds < 0:
        return round((100 / abs(odds)) + 1, 2)
    return None


def parse_american_odds(odds_str: Optional[str]) -> Optional[int]:
    """解析美式赔率字符串 (+400, -175)"""
    if not odds_str:
        return None
    try:
        return int(odds_str.replace("+", ""))
    except ValueError:
        return None


def get_country_flag(team_name: str) -> str:
    """根据球队名称返回国旗emoji（常用球队映射）"""
    flags = {
        "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
        "Algeria": "🇩🇿", "Bosnia-Herzegovina": "🇧🇦", "Belgium": "🇧🇪",
        "Brazil": "🇧🇷", "Canada": "🇨🇦", "Cape Verde": "🇨🇻",
        "Colombia": "🇨🇴", "Congo DR": "🇨🇩", "Croatia": "🇭🇷",
        "Czechia": "🇨🇿", "Côte d'Ivoire": "🇨🇮", "Ecuador": "🇪🇨",
        "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷",
        "Germany": "🇩🇪", "Ghana": "🇬🇭", "Haiti": "🇭🇹",
        "Iran": "🇮🇷", "Iraq": "🇮🇶", "Japan": "🇯🇵",
        "Jordan": "🇯🇴", "Korea Republic": "🇰🇷", "South Korea": "🇰🇷",
        "Mexico": "🇲🇽", "Morocco": "🇲🇦", "Netherlands": "🇳🇱",
        "New Zealand": "🇳🇿", "Norway": "🇳🇴", "Panama": "🇵🇦",
        "Paraguay": "🇵🇾", "Portugal": "🇵🇹", "Qatar": "🇶🇦",
        "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "Senegal": "🇸🇳", "South Africa": "🇿🇦", "Spain": "🇪🇸",
        "Switzerland": "🇨🇭", "Türkiye": "🇹🇷", "Turkey": "🇹🇷",
        "Tunisia": "🇹🇳", "United States": "🇺🇸", "USA": "🇺🇸",
        "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿", "Curaçao": "🇨🇼",
    }
    return flags.get(team_name, "🏳️")


# ============================================================
# 缓存管理
# ============================================================
class CacheManager:
    """简单的文件缓存管理器"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    def _cache_path(self, key: str) -> Path:
        return self.data_dir / f"{key}.json"

    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        path = self._cache_path(key)
        if not path.exists():
            return None

        age = time.time() - path.stat().st_mtime
        if age >= ttl:
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set(self, key: str, data: Any) -> None:
        path = self._cache_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_fallback(self, key: str) -> Optional[Any]:
        """获取过期缓存（降级用）"""
        path = self._cache_path(key)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


# ============================================================
# ESPN API 客户端
# ============================================================
class ESPNClient:
    """ESPN API 客户端"""

    def __init__(self, cache: Optional[CacheManager] = None):
        self.cache = cache or CacheManager()
        self.session = requests.Session()
        self.session.headers.update(ESPN_HEADERS)

    def _request(self, url: str, cache_key: str, ttl: int = 300) -> Dict:
        """发起API请求，带缓存"""
        cached = self.cache.get(cache_key, ttl)
        if cached is not None:
            return cached

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            self.cache.set(cache_key, data)
            return data
        except requests.RequestException as e:
            print(f"[Error] ESPN API: {e}", file=sys.stderr)
            fallback = self.cache.get_fallback(cache_key)
            if fallback is not None:
                return fallback
            raise

    def get_scoreboard(self, date: str) -> Dict:
        """获取指定日期赛程/比分 (日期格式: YYYYMMDD)"""
        url = f"{ESPN_BASE}/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}"
        return self._request(url, f"schedules/{date}", ttl=CACHE_TTL["schedules"])

    def get_event_summary(self, event_id: str) -> Dict:
        """获取比赛详情（含完整赔率、交锋、阵容等）"""
        url = f"{ESPN_BASE}/site/v2/sports/soccer/fifa.world/summary?event={event_id}"
        return self._request(url, f"summary/{event_id}", ttl=CACHE_TTL["odds"])

    def get_standings(self, season: int = 2026) -> Dict:
        """获取积分榜"""
        url = f"{ESPN_BASE}/v2/sports/soccer/fifa.world/standings?season={season}"
        return self._request(url, f"standings/{season}", ttl=CACHE_TTL["standings"])

    def get_team_info(self, team_id: str) -> Dict:
        """获取球队信息"""
        url = f"{ESPN_BASE}/site/v2/sports/soccer/fifa.world/teams/{team_id}"
        return self._request(url, f"teams/{team_id}", ttl=CACHE_TTL["teams"])

    def get_team_schedule(self, team_id: str) -> Dict:
        """获取球队赛程"""
        url = f"{ESPN_BASE}/site/v2/sports/soccer/fifa.world/teams/{team_id}/events"
        return self._request(url, f"teams/{team_id}/events", ttl=CACHE_TTL["schedules"])


# ============================================================
# 数据解析
# ============================================================

def parse_match(event: Dict) -> Dict:
    """解析单场比赛数据"""
    comp = event.get("competitions", [{}])[0]
    competitors = comp.get("competitors", [])

    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    home_team = home.get("team", {})
    away_team = away.get("team", {})

    # 比分
    home_score = home.get("score", "")
    away_score = away.get("score", "")

    # 状态
    status_type = comp.get("status", {}).get("type", {})
    status_name = status_type.get("name", "")
    status_detail = status_type.get("detail", status_type.get("shortDetail", ""))
    status_cn = STATUS_MAP.get(status_name, status_detail)

    # 比赛时钟（进行中的分钟数）
    clock = comp.get("status", {}).get("displayClock", "")

    # 时间
    date_str = event.get("date", "")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        start_time = local_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        start_time = date_str

    # 场地
    venue = comp.get("venue", {})
    venue_name = venue.get("fullName", "")
    venue_city = venue.get("address", {}).get("city", "")

    # 赔率
    odds_list = comp.get("odds", [])
    odds = parse_odds(odds_list, home_team.get("abbreviation", ""), away_team.get("abbreviation", ""))

    # 分组信息
    group_note = comp.get("altGameNote", "")

    return {
        "id": event.get("id"),
        "date": start_time,
        "home_team": home_team.get("displayName", ""),
        "home_short": home_team.get("abbreviation", ""),
        "home_flag": get_country_flag(home_team.get("displayName", "")),
        "home_score": home_score,
        "away_team": away_team.get("displayName", ""),
        "away_short": away_team.get("abbreviation", ""),
        "away_flag": get_country_flag(away_team.get("displayName", "")),
        "away_score": away_score,
        "status": status_cn,
        "status_name": status_name,
        "clock": clock,
        "venue": venue_name,
        "venue_city": venue_city,
        "group": group_note,
        "odds": odds,
    }


def parse_odds(odds_list: List[Dict], home_abbr: str, away_abbr: str) -> Dict:
    """解析赔率数据"""
    if not odds_list:
        return {}

    odds_data = odds_list[0]  # 通常只有一个博彩商的数据
    result = {
        "provider": odds_data.get("provider", {}).get("displayName", ""),
    }

    # 大小球
    over_under = odds_data.get("overUnder")
    if over_under:
        result["over_under_line"] = over_under

    # 大小球赔率
    total = odds_data.get("total", {})
    if total:
        over_info = total.get("over", {}).get("close", {})
        under_info = total.get("under", {}).get("close", {})
        if over_info:
            result["over_odds"] = over_info.get("odds", "")
            result["over_odds_decimal"] = american_to_decimal(parse_american_odds(over_info.get("odds")))
        if under_info:
            result["under_odds"] = under_info.get("odds", "")
            result["under_odds_decimal"] = american_to_decimal(parse_american_odds(under_info.get("odds")))

    # 主胜赔率
    home_odds_obj = odds_list[0]  # home team moneyline 通常在 competitors 里
    # 从 competitions[0].competitors 获取
    # ESPN的赔率结构：drawOdds, 以及 competitors 各自有 odds

    # 平局赔率
    draw_odds = odds_data.get("drawOdds", {})
    if draw_odds:
        ml = draw_odds.get("moneyLine")
        result["draw_odds_american"] = ml
        result["draw_odds_decimal"] = american_to_decimal(ml)

    return result


def parse_standings(data: Dict) -> List[Dict]:
    """解析积分榜"""
    groups = []
    for group in data.get("children", []):
        group_name = group.get("name", "")
        entries = []

        # entries 在 standings 嵌套下
        standings = group.get("standings", {})
        raw_entries = standings.get("entries", []) if isinstance(standings, dict) else []

        for entry in raw_entries:
            team = entry.get("team", {})
            note = entry.get("note", {})
            stats = {}

            for stat in entry.get("stats", []):
                name = stat.get("name", "")
                value = stat.get("value", 0)
                stats[name] = {
                    "value": value,
                    "display": stat.get("displayValue", str(value)),
                }

            entries.append({
                "team": team.get("displayName", ""),
                "abbreviation": team.get("abbreviation", ""),
                "flag": get_country_flag(team.get("displayName", "")),
                "played": int(stats.get("gamesPlayed", {}).get("value", 0)),
                "wins": int(stats.get("wins", {}).get("value", 0)),
                "draws": int(stats.get("draws", {}).get("value", 0)),
                "losses": int(stats.get("losses", {}).get("value", 0)),
                "goals_for": int(stats.get("pointsFor", {}).get("value", 0)),
                "goals_against": int(stats.get("pointsAgainst", {}).get("value", 0)),
                "goal_diff": int(stats.get("pointDifferential", {}).get("value", 0)),
                "points": int(stats.get("points", {}).get("value", 0)),
                "status": note.get("description", ""),
                "rank": note.get("rank", 0),
            })

        # 按积分排序
        entries.sort(key=lambda x: (x["points"], x["goal_diff"], x["goals_for"]), reverse=True)

        groups.append({
            "name": group_name,
            "entries": entries,
        })

    return groups


def parse_full_odds(summary: Dict, match: Dict) -> Dict:
    """从summary API解析完整赔率"""
    pickcenter = summary.get("pickcenter", [])
    if not pickcenter:
        return {}

    pc = pickcenter[0]
    result = {
        "provider": pc.get("provider", {}).get("displayName", ""),
    }

    # 大小球
    over_under = pc.get("overUnder")
    if over_under:
        result["over_under_line"] = over_under

    # 大小球赔率
    over_odds = pc.get("overOdds")
    under_odds = pc.get("underOdds")
    if over_odds is not None:
        result["over_odds_american"] = over_odds
        result["over_odds_decimal"] = american_to_decimal(over_odds)
    if under_odds is not None:
        result["under_odds_american"] = under_odds
        result["under_odds_decimal"] = american_to_decimal(under_odds)

    # 主客队赔率
    home_odds = pc.get("homeTeamOdds", {})
    away_odds = pc.get("awayTeamOdds", {})
    draw_odds = pc.get("drawOdds", {})

    if home_odds:
        ml = home_odds.get("moneyLine")
        if ml is not None:
            result["home_odds_american"] = ml
            result["home_odds_decimal"] = american_to_decimal(ml)
        spread_odds = home_odds.get("spreadOdds")
        if spread_odds is not None:
            result["home_spread_odds"] = spread_odds

    if away_odds:
        ml = away_odds.get("moneyLine")
        if ml is not None:
            result["away_odds_american"] = ml
            result["away_odds_decimal"] = american_to_decimal(ml)
        spread_odds = away_odds.get("spreadOdds")
        if spread_odds is not None:
            result["away_spread_odds"] = spread_odds

    if draw_odds:
        ml = draw_odds.get("moneyLine")
        if ml is not None:
            result["draw_odds_american"] = ml
            result["draw_odds_decimal"] = american_to_decimal(ml)

    # 让球盘口
    spread = pc.get("spread")
    if spread is not None:
        result["spread"] = spread

    return result


def parse_head_to_head(summary: Dict) -> List[Dict]:
    """从summary API解析历史交锋"""
    h2h_games = summary.get("headToHeadGames", [])
    results = []
    for game in h2h_games:
        comp = game.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        results.append({
            "date": game.get("date", ""),
            "home": home.get("team", {}).get("displayName", ""),
            "away": away.get("team", {}).get("displayName", ""),
            "home_score": home.get("score", ""),
            "away_score": away.get("score", ""),
            "status": comp.get("status", {}).get("type", {}).get("description", ""),
        })

    return results


# ============================================================
# 高级功能
# ============================================================

def get_today_matches(client: ESPNClient) -> List[Dict]:
    """获取今日比赛"""
    today = datetime.now(CST).strftime("%Y%m%d")
    data = client.get_scoreboard(today)

    matches = []
    for event in data.get("events", []):
        matches.append(parse_match(event))

    return matches


def get_schedule_by_date(client: ESPNClient, date: str) -> List[Dict]:
    """获取指定日期赛程 (格式: YYYY-MM-DD 或 YYYYMMDD)"""
    date_clean = date.replace("-", "")
    data = client.get_scoreboard(date_clean)

    matches = []
    for event in data.get("events", []):
        matches.append(parse_match(event))

    return matches


def get_all_standings(client: ESPNClient) -> List[Dict]:
    """获取所有小组积分榜"""
    data = client.get_standings()
    return parse_standings(data)


def get_group_standings(client: ESPNClient, group_letter: str) -> Optional[Dict]:
    """获取指定小组积分榜"""
    standings = get_all_standings(client)
    target = f"Group {group_letter.upper()}"

    for group in standings:
        if group["name"] == target:
            return group

    return None


def get_odds_for_match(client: ESPNClient, date: str, team_name: str) -> Optional[Dict]:
    """获取指定比赛的完整赔率（通过summary API）"""
    date_clean = date.replace("-", "")
    data = client.get_scoreboard(date_clean)

    for event in data.get("events", []):
        match = parse_match(event)
        if team_name.lower() in match["home_team"].lower() or team_name.lower() in match["away_team"].lower():
            # 获取完整赔率
            event_id = event.get("id")
            summary = client.get_event_summary(event_id)
            match["odds"] = parse_full_odds(summary, match)
            match["head_to_head"] = parse_head_to_head(summary)
            return match

    return None


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="世界杯数据抓取工具 (ESPN API)")
    parser.add_argument(
        "action",
        choices=["today", "schedule", "standings", "group", "odds", "team"],
        help="操作类型"
    )
    parser.add_argument("--date", help="日期 YYYY-MM-DD 或 YYYYMMDD")
    parser.add_argument("--group", help="小组字母 A-L")
    parser.add_argument("--team", help="球队名称 (用于查询赔率)")
    parser.add_argument("--team-id", help="球队ID (用于查询球队信息)")
    parser.add_argument("--json", action="store_true", help="输出原始JSON")

    args = parser.parse_args()
    client = ESPNClient()

    try:
        result = None

        if args.action == "today":
            result = get_today_matches(client)
            if not args.json:
                print_match_list(result, "今日比赛")
                return

        elif args.action == "schedule":
            date = args.date or datetime.now(CST).strftime("%Y-%m-%d")
            result = get_schedule_by_date(client, date)
            if not args.json:
                print_match_list(result, f"{date} 赛程")
                return

        elif args.action == "standings":
            result = get_all_standings(client)
            if not args.json:
                print_standings(result)
                return

        elif args.action == "group":
            if not args.group:
                parser.error("group 操作需要 --group 参数")
            result = get_group_standings(client, args.group)
            if not args.json:
                if result:
                    print_standings([result])
                else:
                    print(f"未找到小组 {args.group}")
                return

        elif args.action == "odds":
            date = args.date or datetime.now(CST).strftime("%Y-%m-%d")
            if not args.team:
                parser.error("odds 操作需要 --team 参数")
            result = get_odds_for_match(client, date, args.team)
            if not args.json:
                if result:
                    print_odds(result)
                else:
                    print(f"未找到 {args.team} 在 {date} 的比赛")
                return

        elif args.action == "team":
            if not args.team_id:
                parser.error("team 操作需要 --team-id 参数")
            result = client.get_team_info(args.team_id)

        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"[Error] 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


def print_match_list(matches: List[Dict], title: str):
    """打印比赛列表"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

    if not matches:
        print("  暂无比赛")
        return

    for m in matches:
        status_str = m["status"]
        if m.get("clock") and m["status_name"] == "STATUS_IN_PROGRESS":
            status_str = f"{m['clock']}"

        score_str = ""
        if m["home_score"] or m["away_score"]:
            score_str = f" {m['home_score']} - {m['away_score']} "
        else:
            score_str = " vs "

        odds_str = ""
        if m.get("odds", {}).get("home_odds_decimal"):
            odds_str = f"  [主{m['odds']['home_odds_decimal']} 平{m['odds'].get('draw_odds_decimal', '?')} 客{m['odds'].get('away_odds_decimal', '?')}]"

        group_str = f" ({m['group']})" if m.get("group") else ""

        print(f"\n  {m['date']}  {m['home_flag']} {m['home_team']}{score_str}{m['away_team']} {m['away_flag']}")
        print(f"    状态: {status_str} | 场地: {m['venue']}, {m['venue_city']}{group_str}{odds_str}")

    print(f"\n{'='*70}")


def print_standings(groups: List[Dict]):
    """打印积分榜"""
    for group in groups:
        print(f"\n{'='*60}")
        print(f"  {group['name']}")
        print(f"{'='*60}")
        print(f"  {'排名':>4} {'球队':<20} {'场':>3} {'胜':>3} {'平':>3} {'负':>3} {'进球':>4} {'失球':>4} {'净胜':>4} {'积分':>4} {'状态'}")
        print(f"  {'-'*56}")

        for i, entry in enumerate(group["entries"], 1):
            status_mark = ""
            if "Advance" in entry.get("status", ""):
                status_mark = "✅"
            elif "Eliminated" in entry.get("status", ""):
                status_mark = "❌"

            print(f"  {i:>4} {entry['flag']} {entry['team']:<18} {entry['played']:>3} {entry['wins']:>3} {entry['draws']:>3} {entry['losses']:>3} {entry['goals_for']:>4} {entry['goals_against']:>4} {entry['goal_diff']:>+4} {entry['points']:>4} {status_mark}")


def print_odds(match: Dict):
    """打印赔率信息"""
    print(f"\n{'='*50}")
    print(f"  赔率: {match['home_flag']} {match['home_team']} vs {match['away_team']} {match['away_flag']}")
    print(f"  时间: {match['date']}")
    print(f"{'='*50}")

    odds = match.get("odds", {})
    if odds:
        provider = odds.get("provider", "N/A")
        print(f"\n  数据源: {provider}")

        print(f"\n  欧赔 (1X2):")
        home_dec = odds.get("home_odds_decimal", "?")
        draw_dec = odds.get("draw_odds_decimal", "?")
        away_dec = odds.get("away_odds_decimal", "?")
        print(f"    主胜: {home_dec}  |  平局: {draw_dec}  |  客胜: {away_dec}")

        # 计算隐含概率
        if all(isinstance(x, (int, float)) for x in [home_dec, draw_dec, away_dec] if x != "?"):
            total = sum(1/x for x in [home_dec, draw_dec, away_dec])
            margin = (total - 1) * 100
            print(f"    利润率: {margin:.1f}%")
            print(f"    隐含概率: 主{1/home_dec/total*100:.1f}% 平{1/draw_dec/total*100:.1f}% 客{1/away_dec/total*100:.1f}%")

        ou_line = odds.get("over_under_line", 2.5)
        over_dec = odds.get("over_odds_decimal", "?")
        under_dec = odds.get("under_odds_decimal", "?")
        print(f"\n  大小球 ({ou_line}):")
        print(f"    大球: {over_dec}  |  小球: {under_dec}")

    print(f"\n{'='*50}")


if __name__ == "__main__":
    main()
