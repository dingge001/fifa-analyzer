#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳客网数据抓取模块
用于获取竞彩赛程、赔率、专家推荐等中文数据
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))  # UTC+8
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# ============================================================
# 配置
# ============================================================
BASE_URLS = {
    "schedule": "https://info.sporttery.cn/football/match_list.php",
    "odds": "https://info.sporttery.cn/football/match_info.php",
    "experts": "https://info.sporttery.cn/football/expert_list.php",
    "standings": "https://info.sporttery.cn/football/standings.php",
    "live": "https://info.sporttery.cn/football/live_score.php",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 脚本所在目录
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "okooo"


# ============================================================
# 缓存管理
# ============================================================
class CacheManager:
    """简单的文件缓存管理器"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        return self.data_dir / f"{key}.html"

    def get(self, key: str, ttl: int = 3600) -> Optional[str]:
        path = self._cache_path(key)
        if not path.exists():
            return None

        age = time.time() - path.stat().st_mtime
        if age >= ttl:
            print(f"[Cache] 过期: {key} (年龄: {int(age)}s)", file=sys.stderr)
            return None

        print(f"[Cache] 命中: {key}", file=sys.stderr)
        return path.read_text(encoding="utf-8")

    def set(self, key: str, content: str) -> None:
        path = self._cache_path(key)
        path.write_text(content, encoding="utf-8")
        print(f"[Cache] 保存: {key}", file=sys.stderr)

    def get_fallback(self, key: str) -> Optional[str]:
        """获取过期缓存（降级用）"""
        path = self._cache_path(key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")


# ============================================================
# HTML 解析
# ============================================================
def parse_html_table(soup: BeautifulSoup) -> List[List[List[str]]]:
    """解析HTML中所有表格，返回 [table[row[cell]]]"""
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = []
            for td in tr.find_all(["td", "th"]):
                text = td.get_text(strip=True)
                cells.append(text)
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def parse_odds_table(html: str) -> Dict:
    """解析赔率页面"""
    soup = BeautifulSoup(html, "lxml")
    tables = parse_html_table(soup)

    result = {
        "odds_1x2": [],
        "over_under": [],
        "asian_handicap": [],
    }

    for table in tables:
        for row in table[1:]:  # 跳过表头
            if len(row) >= 4:
                # 尝试识别赔率行（包含数字格式的赔率）
                try:
                    float(row[1])
                    result["odds_1x2"].append({
                        "bookmaker": row[0],
                        "home_win": row[1],
                        "draw": row[2],
                        "away_win": row[3],
                    })
                except (ValueError, IndexError):
                    pass

    return result


def parse_schedule_table(html: str) -> List[Dict]:
    """解析赛程页面"""
    soup = BeautifulSoup(html, "lxml")
    tables = parse_html_table(soup)

    matches = []
    if not tables:
        return matches

    main_table = tables[0]
    for row in main_table[1:]:  # 跳过表头
        if len(row) >= 5:
            matches.append({
                "id": row[0],
                "competition": row[1],
                "time": row[2],
                "match": row[3],
                "home_win": row[4] if len(row) > 4 else "",
                "draw": row[5] if len(row) > 5 else "",
                "away_win": row[6] if len(row) > 6 else "",
            })

    return matches


def parse_experts(html: str) -> List[Dict]:
    """解析专家推荐页面"""
    soup = BeautifulSoup(html, "lxml")
    experts = []

    # 尝试多种选择器
    for card in soup.select(".expert-card, .expert-item, .expert"):
        name_el = card.select_one(".name, .expert-name")
        rate_el = card.select_one(".rate, .win-rate")
        match_el = card.select_one(".match, .prediction")

        if name_el:
            experts.append({
                "name": name_el.get_text(strip=True),
                "win_rate": rate_el.get_text(strip=True) if rate_el else "",
                "match": match_el.get_text(strip=True) if match_el else "",
            })

    return experts


# ============================================================
# 客户端
# ============================================================
class OkoooClient:
    """澳客网数据客户端"""

    def __init__(self, cache: Optional[CacheManager] = None):
        self.cache = cache or CacheManager()
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _fetch(self, url: str, cache_key: str, ttl: int = 3600) -> str:
        """获取页面，带缓存"""
        cached = self.cache.get(cache_key, ttl)
        if cached is not None:
            return cached

        print(f"[Request] 请求: {url}", file=sys.stderr)

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            content = resp.text

            self.cache.set(cache_key, content)
            return content

        except requests.RequestException as e:
            print(f"[Error] 请求失败: {e}", file=sys.stderr)

            # 降级：使用过期缓存
            fallback = self.cache.get_fallback(cache_key)
            if fallback is not None:
                print(f"[Fallback] 使用过期缓存: {cache_key}", file=sys.stderr)
                return fallback

            raise

    def get_schedule(self) -> Dict:
        """获取竞彩赛程"""
        html = self._fetch(BASE_URLS["schedule"], "schedule", ttl=3600)
        matches = parse_schedule_table(html)

        return {
            "source": "澳客网/竞彩官方",
            "update_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches,
        }

    def get_odds(self, match_id: str) -> Dict:
        """获取单场赔率"""
        url = f"{BASE_URLS['odds']}?match_id={match_id}"
        html = self._fetch(url, f"odds_{match_id}", ttl=1800)
        odds = parse_odds_table(html)

        return {
            "source": "澳客网/竞彩官方",
            "match_id": match_id,
            "update_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
            **odds,
        }

    def get_experts(self) -> Dict:
        """获取专家推荐"""
        html = self._fetch(BASE_URLS["experts"], "experts", ttl=3600)
        experts = parse_experts(html)

        return {
            "source": "澳客网/竞彩官方",
            "update_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
            "experts": experts,
        }

    def get_live(self) -> Dict:
        """获取实时比分"""
        html = self._fetch(BASE_URLS["live"], "live", ttl=30)
        soup = BeautifulSoup(html, "lxml")
        tables = parse_html_table(soup)

        return {
            "source": "澳客网/竞彩官方",
            "update_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
            "tables_count": len(tables),
        }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="澳客网数据抓取工具")
    parser.add_argument(
        "action",
        choices=["schedule", "odds", "experts", "live"],
        help="操作类型"
    )
    parser.add_argument("--match-id", help="比赛ID (odds操作需要)")

    args = parser.parse_args()
    client = OkoooClient()

    try:
        result = None

        if args.action == "schedule":
            result = client.get_schedule()

        elif args.action == "odds":
            if not args.match_id:
                parser.error("odds 操作需要 --match-id 参数")
            result = client.get_odds(args.match_id)

        elif args.action == "experts":
            result = client.get_experts()

        elif args.action == "live":
            result = client.get_live()

        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"[Error] 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
