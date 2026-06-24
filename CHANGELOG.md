# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
