#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成FIFA Analyzer效果展示图片"""

import os
import sys
import io
from PIL import Image, ImageDraw, ImageFont

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置
# ============================================================
W, H = 1200, 680
OUT_DIR = r"E:\workspace-claude\fifa-go\docs\images"
FONT_DIR = r"C:\Users\程嘉嘉\.claude\skills\canvas-design\canvas-fonts"

# 颜色
BG = "#0a0e17"
BG_CARD = "#111827"
BG_CARD2 = "#1a1f2e"
BORDER = "#1e293b"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_DIM = "#64748b"
ACCENT_GREEN = "#10b981"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_BLUE = "#3b82f6"
ACCENT_PURPLE = "#8b5cf6"

# 加载字体
def load_font(name, size):
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

font_title = load_font("Jura-Medium.ttf", 28)
font_subtitle = load_font("Jura-Medium.ttf", 18)
font_body = load_font("WorkSans-Regular.ttf", 15)
font_body_bold = load_font("WorkSans-Bold.ttf", 15)
font_mono = load_font("GeistMono-Regular.ttf", 14)
font_mono_bold = load_font("GeistMono-Bold.ttf", 16)
font_small = load_font("WorkSans-Regular.ttf", 12)
font_small_mono = load_font("JetBrainsMono-Regular.ttf", 11)
font_big_num = load_font("GeistMono-Bold.ttf", 32)
font_team = load_font("WorkSans-Bold.ttf", 17)
font_vs = load_font("Jura-Medium.ttf", 14)


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    r = radius
    if fill:
        draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
        draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
        draw.pieslice([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill)
        draw.pieslice([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill)
        draw.pieslice([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill)
        draw.pieslice([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill)
    if outline:
        draw.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=outline, width=width)
        draw.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=outline, width=width)
        draw.line([x0+r, y0, x1-r, y0], fill=outline, width=width)
        draw.line([x0+r, y1, x1-r, y1], fill=outline, width=width)
        draw.line([x0, y0+r, x0, y1-r], fill=outline, width=width)
        draw.line([x1, y0+r, x1, y1-r], fill=outline, width=width)


def draw_gradient_bar(draw, xy, color, pct):
    x0, y0, x1, y1 = xy
    bar_w = int((x1 - x0) * pct)
    r = (y1 - y0) // 2
    if bar_w > 0:
        draw_rounded_rect(draw, (x0, y0, x0 + bar_w, y1), r, fill=color)


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ============================================================
# 图片1: 今日赛程
# ============================================================
def create_schedule():
    img = Image.new('RGB', (W, H), hex_to_rgb(BG))
    draw = ImageDraw.Draw(img)

    # 顶部装饰线
    draw.rectangle([0, 0, W, 3], fill=hex_to_rgb(ACCENT_CYAN))

    # 标题区域
    draw.text((40, 28), "TODAY'S MATCHES", font=font_title, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((40, 62), "2026 FIFA WORLD CUP  ·  GROUP STAGE  ·  MATCHDAY 3", font=font_small, fill=hex_to_rgb(TEXT_DIM))

    # 右上角时间
    draw.text((W - 200, 35), "2026-06-24", font=font_mono, fill=hex_to_rgb(ACCENT_CYAN))
    draw.text((W - 200, 55), "6 MATCHES SCHEDULED", font=font_small, fill=hex_to_rgb(TEXT_DIM))

    # 分隔线
    draw.line([(40, 88), (W - 40, 88)], fill=hex_to_rgb(BORDER), width=1)

    matches = [
        ("03:00", "BIH", "QAT", "B", "Lumen Field, Seattle", "🇧🇦", "🇶🇦"),
        ("03:00", "SUI", "CAN", "B", "BC Place, Vancouver", "🇨🇭", "🇨🇦"),
        ("06:00", "MAR", "HAI", "C", "Mercedes-Benz, Atlanta", "🇲🇦", "🇭🇹"),
        ("06:00", "SCO", "BRA", "C", "Hard Rock, Miami", "🏴", "🇧🇷"),
        ("09:00", "CZE", "MEX", "A", "Estadio Banorte, CDMX", "🇨🇿", "🇲🇽"),
        ("09:00", "RSA", "KOR", "A", "Estadio BBVA, Monterrey", "🇿🇦", "🇰🇷"),
    ]

    team_names = {
        "BIH": "Bosnia", "QAT": "Qatar", "SUI": "Switzerland", "CAN": "Canada",
        "MAR": "Morocco", "HAI": "Haiti", "SCO": "Scotland", "BRA": "Brazil",
        "CZE": "Czechia", "MEX": "Mexico", "RSA": "S. Africa", "KOR": "S. Korea",
    }

    # 2行3列网格
    card_w, card_h = 355, 235
    gap_x, gap_y = 20, 20
    start_x, start_y = 40, 108

    for i, (time, home, away, group, venue, flag_h, flag_a) in enumerate(matches):
        col = i % 3
        row = i // 3
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        # 卡片背景
        draw_rounded_rect(draw, (x, y, x + card_w, y + card_h), 10, fill=hex_to_rgb(BG_CARD))
        draw_rounded_rect(draw, (x, y, x + card_w, y + card_h), 10, outline=hex_to_rgb(BORDER), width=1)

        # 顶部小组标签
        group_colors = {"A": ACCENT_GREEN, "B": ACCENT_CYAN, "C": ACCENT_AMBER}
        gc = group_colors.get(group, ACCENT_BLUE)
        draw_rounded_rect(draw, (x + 14, y + 14, x + 72, y + 36), 4, fill=hex_to_rgb(gc))
        tw, th = text_size(draw, f"GROUP {group}", font_small_mono)
        draw.text((x + 14 + (58 - tw) // 2, y + 17), f"GROUP {group}", font=font_small_mono, fill=hex_to_rgb("#ffffff"))

        # 时间
        time_tw, _ = text_size(draw, time, font_mono_bold)
        draw.text((x + card_w - time_tw - 14, y + 16), time, font=font_mono_bold, fill=hex_to_rgb(ACCENT_CYAN))

        # VS 区域
        cy = y + card_h // 2 - 10

        # 主队
        draw.text((x + 30, cy - 12), flag_h, font=font_body, fill=hex_to_rgb(TEXT_PRIMARY))
        draw.text((x + 55, cy - 10), team_names[home], font=font_team, fill=hex_to_rgb(TEXT_PRIMARY))
        draw.text((x + 55, cy + 12), home, font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

        # VS
        vs_tw, _ = text_size(draw, "VS", font_vs)
        draw.text((x + card_w // 2 - vs_tw // 2, cy - 5), "VS", font=font_vs, fill=hex_to_rgb(TEXT_DIM))

        # 客队
        away_tw, _ = text_size(draw, team_names[away], font_team)
        draw.text((x + card_w - away_tw - 55, cy - 10), team_names[away], font=font_team, fill=hex_to_rgb(TEXT_PRIMARY))
        draw.text((x + card_w - 50, cy - 12), flag_a, font=font_body, fill=hex_to_rgb(TEXT_PRIMARY))
        away_code_tw, _ = text_size(draw, away, font_small_mono)
        draw.text((x + card_w - away_code_tw - 30, cy + 12), away, font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

        # 场地
        draw.line([(x + 14, y + card_h - 42), (x + card_w - 14, y + card_h - 42)], fill=hex_to_rgb(BORDER), width=1)
        draw.text((x + 14, y + card_h - 32), venue, font=font_small, fill=hex_to_rgb(TEXT_DIM))

    # 底部状态栏
    draw.rectangle([0, H - 32, W, H], fill=hex_to_rgb(BG_CARD2))
    draw.text((40, H - 26), "DATA SOURCE: ESPN API  |  UPDATE: REAL-TIME  |  FIFA ANALYZER v1.0", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    # 小绿点
    draw.ellipse([W - 130, H - 20, W - 122, H - 12], fill=hex_to_rgb(ACCENT_GREEN))
    draw.text((W - 118, H - 24), "LIVE", font=font_small_mono, fill=hex_to_rgb(ACCENT_GREEN))

    img.save(os.path.join(OUT_DIR, "screenshot-schedule.png"), quality=95)
    print("✅ screenshot-schedule.png")


# ============================================================
# 图片2: 赔率分析
# ============================================================
def create_odds():
    img = Image.new('RGB', (W, H), hex_to_rgb(BG))
    draw = ImageDraw.Draw(img)

    # 顶部装饰线
    draw.rectangle([0, 0, W, 3], fill=hex_to_rgb(ACCENT_AMBER))

    # 标题
    draw.text((40, 28), "ODDS ANALYSIS", font=font_title, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((40, 62), "SCOTLAND  VS  BRAZIL  ·  GROUP C  ·  2026-06-25 06:00", font=font_small, fill=hex_to_rgb(TEXT_DIM))
    draw.text((W - 180, 40), "DRAFTKINGS", font=font_mono_bold, fill=hex_to_rgb(ACCENT_AMBER))

    draw.line([(40, 88), (W - 40, 88)], fill=hex_to_rgb(BORDER), width=1)

    # === 左侧面板: 欧赔 ===
    panel_x, panel_y = 40, 108
    panel_w, panel_h = 540, 250

    draw_rounded_rect(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), 10, fill=hex_to_rgb(BG_CARD))
    draw_rounded_rect(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), 10, outline=hex_to_rgb(BORDER))

    draw.text((panel_x + 20, panel_y + 16), "1X2  MATCH ODDS", font=font_subtitle, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((panel_x + 20, panel_y + 42), "EUROPEAN ODDS (DECIMAL)", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

    # 三个赔率卡片
    odds_data = [
        ("HOME WIN", "8.00", "12.0%", ACCENT_RED, "SCO"),
        ("DRAW", "5.25", "18.3%", ACCENT_AMBER, "X"),
        ("AWAY WIN", "1.38", "69.7%", ACCENT_GREEN, "BRA"),
    ]

    card_w2 = 155
    card_gap = 18
    odds_start_x = panel_x + 22
    odds_y = panel_y + 70

    for i, (label, odds, prob, color, code) in enumerate(odds_data):
        cx = odds_start_x + i * (card_w2 + card_gap)

        # 小卡片
        draw_rounded_rect(draw, (cx, odds_y, cx + card_w2, odds_y + 150), 8, fill=hex_to_rgb(BG_CARD2))
        # 顶部色条
        draw.rectangle([cx + 1, odds_y + 1, cx + card_w2 - 1, odds_y + 5], fill=hex_to_rgb(color))

        # 代码
        draw.text((cx + 15, odds_y + 18), code, font=font_mono_bold, fill=hex_to_rgb(color))

        # 赔率大数字
        draw.text((cx + 15, odds_y + 48), odds, font=font_big_num, fill=hex_to_rgb(TEXT_PRIMARY))

        # 标签
        draw.text((cx + 15, odds_y + 92), label, font=font_small, fill=hex_to_rgb(TEXT_SECONDARY))

        # 概率
        draw.text((cx + 15, odds_y + 115), f"IMPL PROB", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
        draw.text((cx + 15, odds_y + 130), prob, font=font_mono_bold, fill=hex_to_rgb(color))

    # 利润率
    margin_y = odds_y + 155 + 8
    draw.text((panel_x + 22, margin_y), "MARGIN", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    draw.text((panel_x + 100, margin_y), "4.0%", font=font_small_mono, fill=hex_to_rgb(ACCENT_GREEN))

    # === 右侧面板: 大小球 + 亚盘 ===
    r_panel_x = panel_x + panel_w + 20
    r_panel_w = W - r_panel_x - 40

    # 大小球
    draw_rounded_rect(draw, (r_panel_x, panel_y, r_panel_x + r_panel_w, panel_y + 120), 10, fill=hex_to_rgb(BG_CARD))
    draw_rounded_rect(draw, (r_panel_x, panel_y, r_panel_x + r_panel_w, panel_y + 120), 10, outline=hex_to_rgb(BORDER))

    draw.text((r_panel_x + 20, panel_y + 16), "OVER / UNDER", font=font_subtitle, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((r_panel_x + 20, panel_y + 42), "LINE: 2.5 GOALS", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

    # Over
    draw_rounded_rect(draw, (r_panel_x + 20, panel_y + 65, r_panel_x + 150, panel_y + 100), 6, fill=hex_to_rgb(BG_CARD2))
    draw.text((r_panel_x + 30, panel_y + 72), "OVER", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    draw.text((r_panel_x + 85, panel_y + 72), "1.87", font=font_mono_bold, fill=hex_to_rgb(ACCENT_GREEN))

    # Under
    draw_rounded_rect(draw, (r_panel_x + 165, panel_y + 65, r_panel_x + 300, panel_y + 100), 6, fill=hex_to_rgb(BG_CARD2))
    draw.text((r_panel_x + 175, panel_y + 72), "UNDER", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    draw.text((r_panel_x + 235, panel_y + 72), "1.95", font=font_mono_bold, fill=hex_to_rgb(ACCENT_AMBER))

    # 亚盘
    asy_y = panel_y + 140
    draw_rounded_rect(draw, (r_panel_x, asy_y, r_panel_x + r_panel_w, asy_y + 110), 10, fill=hex_to_rgb(BG_CARD))
    draw_rounded_rect(draw, (r_panel_x, asy_y, r_panel_x + r_panel_w, asy_y + 110), 10, outline=hex_to_rgb(BORDER))

    draw.text((r_panel_x + 20, asy_y + 16), "ASIAN HANDICAP", font=font_subtitle, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((r_panel_x + 20, asy_y + 42), "BRAZIL -0.5", font=font_mono_bold, fill=hex_to_rgb(ACCENT_CYAN))

    # 水位指示条
    bar_y = asy_y + 70
    bar_x = r_panel_x + 20
    bar_w = r_panel_w - 40
    bar_h = 18

    # 背景条
    draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), bar_h // 2, fill=hex_to_rgb(BG_CARD2))
    # 填充（巴西被看好，70%位置）
    draw_gradient_bar(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), hex_to_rgb(ACCENT_CYAN), 0.70)
    # 标记
    mark_x = bar_x + int(bar_w * 0.70)
    draw.line([(mark_x, bar_y - 4), (mark_x, bar_y + bar_h + 4)], fill=hex_to_rgb("#ffffff"), width=2)

    draw.text((bar_x, bar_y + bar_h + 6), "SCO +0.5", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    sco_tw, _ = text_size(draw, "BRA -0.5", font_small_mono)
    draw.text((bar_x + bar_w - sco_tw, bar_y + bar_h + 6), "BRA -0.5", font=font_small_mono, fill=hex_to_rgb(ACCENT_CYAN))

    # === 底部: 隐含概率条形图 ===
    prob_y = panel_y + panel_h + 20
    prob_h = H - prob_y - 50

    draw_rounded_rect(draw, (40, prob_y, W - 40, prob_y + prob_h), 10, fill=hex_to_rgb(BG_CARD))
    draw_rounded_rect(draw, (40, prob_y, W - 40, prob_y + prob_h), 10, outline=hex_to_rgb(BORDER))

    draw.text((60, prob_y + 16), "IMPLIED PROBABILITY", font=font_subtitle, fill=hex_to_rgb(TEXT_PRIMARY))

    # 三个概率条
    bar_data = [
        ("HOME WIN (SCO)", 0.120, ACCENT_RED),
        ("DRAW", 0.183, ACCENT_AMBER),
        ("AWAY WIN (BRA)", 0.697, ACCENT_GREEN),
    ]

    bar_start_y = prob_y + 50
    label_w = 180
    avail_w = W - 80 - label_w - 80  # 左padding + label + gap + percentage

    for i, (label, pct, color) in enumerate(bar_data):
        by = bar_start_y + i * 42
        bx = 60 + label_w

        # 标签
        draw.text((60, by + 2), label, font=font_small_mono, fill=hex_to_rgb(TEXT_SECONDARY))

        # 背景条
        draw_rounded_rect(draw, (bx, by, bx + avail_w, by + 24), 6, fill=hex_to_rgb(BG_CARD2))
        # 填充条
        fill_w = max(int(avail_w * pct), 12)
        draw_gradient_bar(draw, (bx, by, bx + fill_w, by + 24), hex_to_rgb(color), 1.0)

        # 百分比
        pct_text = f"{pct*100:.1f}%"
        draw.text((bx + avail_w + 12, by + 2), pct_text, font=font_mono_bold, fill=hex_to_rgb(color))

    # 底部状态栏
    draw.rectangle([0, H - 32, W, H], fill=hex_to_rgb(BG_CARD2))
    draw.text((40, H - 26), "DATA SOURCE: ESPN / DRAFTKINGS  |  MARGIN: 4.0%  |  FIFA ANALYZER v1.0", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

    img.save(os.path.join(OUT_DIR, "screenshot-odds.png"), quality=95)
    print("✅ screenshot-odds.png")


# ============================================================
# 图片3: 积分榜
# ============================================================
def create_standings():
    img = Image.new('RGB', (W, H), hex_to_rgb(BG))
    draw = ImageDraw.Draw(img)

    # 顶部装饰线
    draw.rectangle([0, 0, W, 3], fill=hex_to_rgb(ACCENT_GREEN))

    # 标题
    draw.text((40, 28), "GROUP H  STANDINGS", font=font_title, fill=hex_to_rgb(TEXT_PRIMARY))
    draw.text((40, 62), "2026 FIFA WORLD CUP  ·  GROUP STAGE  ·  UPDATED REAL-TIME", font=font_small, fill=hex_to_rgb(TEXT_DIM))
    draw.text((W - 180, 40), "MATCHDAY 2/3", font=font_mono_bold, fill=hex_to_rgb(ACCENT_GREEN))

    draw.line([(40, 88), (W - 40, 88)], fill=hex_to_rgb(BORDER), width=1)

    # 积分榜主体
    table_x = 40
    table_y = 108
    table_w = W - 80
    row_h = 68

    # 表头
    draw_rounded_rect(draw, (table_x, table_y, table_x + table_w, table_y + 44), 8, fill=hex_to_rgb(BG_CARD2))

    headers = [
        ("#", 55), ("TEAM", 230), ("MP", 340), ("W", 400), ("D", 450), ("L", 500),
        ("GF", 560), ("GA", 620), ("GD", 690), ("PTS", 770), ("STATUS", 900)
    ]
    for label, hx in headers:
        draw.text((hx, table_y + 14), label, font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

    # 数据行
    teams = [
        (1, "ESP", "Spain", "🇪🇸", 2, 1, 0, 0, 4, 0, "+4", 4, True, False),
        (2, "URU", "Uruguay", "🇺🇾", 2, 0, 0, 0, 3, 3, "0", 2, True, False),
        (3, "CPV", "Cape Verde", "🇨🇻", 2, 0, 0, 0, 2, 2, "0", 2, False, False),
        (4, "KSA", "Saudi Arabia", "🇸🇦", 2, 0, 0, 1, 1, 5, "-4", 1, False, True),
    ]

    for i, (rank, code, name, flag, mp, w, d, l, gf, ga, gd, pts, advanced, eliminated) in enumerate(teams):
        ry = table_y + 52 + i * row_h

        # 行背景
        bg = hex_to_rgb(BG_CARD) if i % 2 == 0 else hex_to_rgb(BG_CARD2)
        draw_rounded_rect(draw, (table_x, ry, table_x + table_w, ry + row_h - 8), 6, fill=bg)

        # 左边状态色条
        if advanced:
            draw.rectangle([table_x + 1, ry + 4, table_x + 5, ry + row_h - 12], fill=hex_to_rgb(ACCENT_GREEN))
        elif eliminated:
            draw.rectangle([table_x + 1, ry + 4, table_x + 5, ry + row_h - 12], fill=hex_to_rgb(ACCENT_RED))
        else:
            draw.rectangle([table_x + 1, ry + 4, table_x + 5, ry + row_h - 12], fill=hex_to_rgb(TEXT_DIM))

        # 排名
        draw.text((55, ry + 22), str(rank), font=font_mono_bold, fill=hex_to_rgb(TEXT_PRIMARY))

        # 队名
        draw.text((230, ry + 12), name, font=font_team, fill=hex_to_rgb(TEXT_PRIMARY))
        draw.text((230, ry + 36), code, font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

        # 数据
        data_y = ry + 22
        for val, col in [(mp, 340), (w, 400), (d, 450), (l, 500), (gf, 560), (ga, 620)]:
            draw.text((col, data_y), str(val), font=font_mono, fill=hex_to_rgb(TEXT_SECONDARY))

        # 净胜球（正绿负红）
        gd_color = ACCENT_GREEN if gd.startswith("+") else (ACCENT_RED if gd.startswith("-") else TEXT_SECONDARY)
        draw.text((690, data_y), gd, font=font_mono_bold, fill=hex_to_rgb(gd_color))

        # 积分
        draw.text((770, data_y - 2), str(pts), font=font_mono_bold, fill=hex_to_rgb(TEXT_PRIMARY))

        # 状态
        if advanced:
            draw_rounded_rect(draw, (880, ry + 16, 1020, ry + 40), 4, fill=hex_to_rgb(ACCENT_GREEN))
            stw, _ = text_size(draw, "ADVANCED", font_small_mono)
            draw.text((880 + (140 - stw) // 2, ry + 21), "ADVANCED", font=font_small_mono, fill=hex_to_rgb("#ffffff"))
        elif eliminated:
            draw_rounded_rect(draw, (880, ry + 16, 1020, ry + 40), 4, fill=hex_to_rgb(ACCENT_RED))
            stw, _ = text_size(draw, "ELIMINATED", font_small_mono)
            draw.text((880 + (140 - stw) // 2, ry + 21), "ELIMINATED", font=font_small_mono, fill=hex_to_rgb("#ffffff"))
        else:
            draw_rounded_rect(draw, (880, ry + 16, 1020, ry + 40), 4, outline=hex_to_rgb(TEXT_DIM))
            stw, _ = text_size(draw, "IN CONTENTION", font_small_mono)
            draw.text((880 + (140 - stw) // 2, ry + 21), "IN CONTENTION", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))

    # === 右侧信息面板 ===
    info_y = table_y + 52 + 4 * row_h + 10

    # 出线规则说明
    draw_rounded_rect(draw, (table_x, info_y, table_x + table_w, info_y + 80), 10, fill=hex_to_rgb(BG_CARD))
    draw_rounded_rect(draw, (table_x, info_y, table_x + table_w, info_y + 80), 10, outline=hex_to_rgb(BORDER))

    draw.text((table_x + 20, info_y + 14), "QUALIFICATION RULES", font=font_subtitle, fill=hex_to_rgb(TEXT_PRIMARY))

    # 图例
    legend_y = info_y + 44
    items = [
        (ACCENT_GREEN, "Top 2 + Best 3rd → Round of 32"),
        (ACCENT_RED, "4th Place → Eliminated"),
    ]
    for lx, (color, text) in enumerate(items):
        ix = table_x + 20 + lx * 380
        draw.rectangle([ix, legend_y, ix + 12, legend_y + 12], fill=hex_to_rgb(color))
        draw.text((ix + 20, legend_y - 1), text, font=font_small, fill=hex_to_rgb(TEXT_SECONDARY))

    # 底部状态栏
    draw.rectangle([0, H - 32, W, H], fill=hex_to_rgb(BG_CARD2))
    draw.text((40, H - 26), "DATA SOURCE: ESPN API  |  SEASON: 2026  |  FIFA ANALYZER v1.0", font=font_small_mono, fill=hex_to_rgb(TEXT_DIM))
    draw.ellipse([W - 130, H - 20, W - 122, H - 12], fill=hex_to_rgb(ACCENT_GREEN))
    draw.text((W - 118, H - 24), "LIVE", font=font_small_mono, fill=hex_to_rgb(ACCENT_GREEN))

    img.save(os.path.join(OUT_DIR, "screenshot-standings.png"), quality=95)
    print("✅ screenshot-standings.png")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    create_schedule()
    create_odds()
    create_standings()
    print(f"\n🎉 3 images saved to {OUT_DIR}")
