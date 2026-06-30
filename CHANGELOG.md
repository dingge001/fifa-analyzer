# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-30

### Updated
- 📊 更新 06/26、06/27、06/30 预测结果（共 27/28 场已结算）
- 💰 更新盈亏统计：命中率 67% | ROI -4.38% | 净亏损 ¥1,750.02
- 📋 README 预测跟踪表格全面更新，含每日小计

### Results Summary
| 日期 | 轮次 | 命中 | 总数 | 盈亏 |
|------|------|------|------|------|
| 06/25 | 小组赛 | 3 | 4 | +2,275.00 |
| 06/26 | 小组赛 | 3 | 6 | -2,500.00 |
| 06/27 | 小组赛 | 10 | 12 | +3,508.32 |
| 06/30 | 32强赛 | 2 | 5 | -3,366.67 |
| **合计** | | **18** | **27** | **-1,750.02** |

### Pending
- 荷兰 vs 摩洛哥（06/30 32强赛）- 比赛中

## [1.0.0] - 2026-06-24

### Added
- 🎉 Initial release of FIFA Analyzer skill for Claude Code
- 📊 ESPN API integration for match data, odds, and standings
- 💰 Complete odds support (1X2, Asian Handicap, Over/Under)
- 📈 Real-time group standings for all 12 groups
- 🧠 7-dimension scoring model for match analysis
- 🎯 14 user intent types supported
- 💾 Smart caching system with configurable TTL
- 📋 14 output templates for different analysis types
- 🔄 Graceful degradation across multiple data sources
- ⚠️ Mandatory disclaimer on all outputs

### Data Sources
- ESPN API (primary) - match schedules, scores, odds, standings
- DraftKings (via ESPN) - betting odds
- Okooo (澳客网) - Chinese betting data

### Technical
- Python 3.8+ support
- requests + BeautifulSoup for data fetching
- UTF-8 encoding support for Windows
- File-based caching with TTL management
