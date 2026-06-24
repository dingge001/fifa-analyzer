#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理工具
用于查看缓存状态、清理过期缓存
"""

import argparse
import io
import sys
import time
from pathlib import Path
from typing import Dict

# 修复Windows终端编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 缓存TTL配置（秒）
TTL_CONFIG = {
    "matches": 300,           # 5分钟
    "odds": 3600,             # 1小时
    "schedules": 86400,       # 24小时
    "head-to-head": 2592000,  # 30天
    "okooo": 3600,            # 1小时
}

# 脚本所在目录
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_ttl(seconds: int) -> str:
    """格式化TTL"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟"
    elif seconds < 86400:
        return f"{seconds // 3600}小时"
    else:
        return f"{seconds // 86400}天"


def get_cache_status() -> Dict:
    """获取缓存状态"""
    total_size = 0
    total_files = 0
    total_valid = 0
    total_expired = 0
    stats = {}

    for cache_type, ttl in TTL_CONFIG.items():
        cache_dir = DATA_DIR / cache_type

        if not cache_dir.exists():
            stats[cache_type] = {
                "path": str(cache_dir),
                "files": 0,
                "size": 0,
                "valid": 0,
                "expired": 0,
                "ttl": ttl,
            }
            continue

        files = list(cache_dir.rglob("*"))
        files = [f for f in files if f.is_file() and f.name != ".gitkeep"]
        dir_size = sum(f.stat().st_size for f in files)
        valid_count = 0
        expired_count = 0

        for f in files:
            age = time.time() - f.stat().st_mtime
            if age < ttl:
                valid_count += 1
            else:
                expired_count += 1

        stats[cache_type] = {
            "path": str(cache_dir),
            "files": len(files),
            "size": dir_size,
            "valid": valid_count,
            "expired": expired_count,
            "ttl": ttl,
        }

        total_size += dir_size
        total_files += len(files)
        total_valid += valid_count
        total_expired += expired_count

    return {
        "total_size": total_size,
        "total_files": total_files,
        "total_valid": total_valid,
        "total_expired": total_expired,
        "by_type": stats,
    }


def clean_expired(cache_type: str = None) -> Dict:
    """清理过期缓存"""
    cleaned_count = 0
    cleaned_size = 0

    types_to_clean = [cache_type] if cache_type else list(TTL_CONFIG.keys())

    for ct in types_to_clean:
        cache_dir = DATA_DIR / ct
        ttl = TTL_CONFIG.get(ct, 3600)

        if not cache_dir.exists():
            continue

        for f in cache_dir.rglob("*"):
            if not f.is_file() or f.name == ".gitkeep":
                continue
            age = time.time() - f.stat().st_mtime
            if age >= ttl:
                file_size = f.stat().st_size
                f.unlink()
                cleaned_count += 1
                cleaned_size += file_size
                print(f"[Clean] 删除: {f.name} (年龄: {int(age / 3600)}h)")

    return {"cleaned_files": cleaned_count, "cleaned_size": cleaned_size}


def clean_all() -> Dict:
    """清理所有缓存"""
    cleaned_count = 0
    cleaned_size = 0

    for ct in TTL_CONFIG.keys():
        cache_dir = DATA_DIR / ct
        if not cache_dir.exists():
            continue

        for f in cache_dir.rglob("*"):
            if not f.is_file() or f.name == ".gitkeep":
                continue
            file_size = f.stat().st_size
            f.unlink()
            cleaned_count += 1
            cleaned_size += file_size

    return {"cleaned_files": cleaned_count, "cleaned_size": cleaned_size}


def main():
    parser = argparse.ArgumentParser(description="缓存管理工具")
    parser.add_argument(
        "action",
        choices=["status", "clean", "clean-all"],
        help="操作类型"
    )
    parser.add_argument(
        "--type",
        choices=list(TTL_CONFIG.keys()),
        help="缓存类型 (clean操作时可选)"
    )

    args = parser.parse_args()

    if args.action == "status":
        status = get_cache_status()

        print("=" * 50)
        print("缓存状态报告")
        print("=" * 50)
        print()
        print(f"总文件数: {status['total_files']}")
        print(f"总大小:   {format_size(status['total_size'])}")
        print(f"有效缓存: {status['total_valid']}")
        print(f"过期缓存: {status['total_expired']}")
        print()
        print("-" * 50)

        for ct, info in sorted(status["by_type"].items()):
            print(f"\n[{ct}]")
            print(f"  路径:   {info['path']}")
            print(f"  文件数: {info['files']}")
            print(f"  大小:   {format_size(info['size'])}")
            print(f"  TTL:    {format_ttl(info['ttl'])}")
            print(f"  有效:   {info['valid']} | 过期: {info['expired']}")

    elif args.action == "clean":
        print("正在清理过期缓存...")
        result = clean_expired(args.type)
        print(f"\n清理完成! 删除 {result['cleaned_files']} 个文件，释放 {format_size(result['cleaned_size'])}")

    elif args.action == "clean-all":
        confirm = input("确定要清理所有缓存吗? (y/n): ")
        if confirm.lower() != "y":
            print("已取消")
            return

        print("正在清理所有缓存...")
        result = clean_all()
        print(f"\n清理完成! 删除 {result['cleaned_files']} 个文件，释放 {format_size(result['cleaned_size'])}")


if __name__ == "__main__":
    main()
