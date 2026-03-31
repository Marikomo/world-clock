import streamlit as st
from datetime import datetime, timedelta, date
import pytz
import calendar
import holidays
from streamlit_autorefresh import st_autorefresh

# 1秒ごとに更新
st_autorefresh(interval=1000, key="datetimereload")

st.set_page_config(page_title="日/米 株式市場リアルタイムカレンダー", layout="wide")

# --- セッション状態の初期化 ---
if 'view_date_us' not in st.session_state:
    st.session_state.view_date_us = datetime.now(pytz.timezone('America/New_York')).date().replace(day=1)
if 'view_date_jp' not in st.session_state:
    st.session_state.view_date_jp = datetime.now(pytz.timezone('Asia/Tokyo')).date().replace(day=1)

# --- スタイル設定（爆速ツールチップの実装） ---
st.markdown("""
<style>
    body { color: #444; }

    /* カレンダーテーブル */
    .calendar-table {
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        margin-bottom: 20px;
        color: #444;
    }
    .calendar-table tr { height: 40px; }
    .calendar-table td, .calendar-table th { vertical-align: middle; padding: 0; position: relative; }
    
    /* 今日のマーカー */
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        border-radius: 0%; 
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        font-weight: bold;
    }
    
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    
    /* --- カスタムツールチップの魔法 --- */
    .tooltip-container {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }

    /* 祝日の下線 */
    .has-holiday {
        border-bottom: 1px dotted #ff4b4b;
    }

    /* ツールチップ本体（最初は非表示） */
    .tooltip-text {
        visibility: hidden;
        width: max-content;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 4px;
        padding: 4px 8px;
        position: absolute;
        z-index: 100;
        bottom: 125%; /* 数字の上に表示 */
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.1s; /* 0.1秒でパッと出る */
        font-size: 0.75rem;
        font-family: sans-serif;
        white-space: nowrap;
        pointer-events: none;
    }

    /* マウスが重なった瞬間に表示 */
    .tooltip-container:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }

    /* 市場ステータス枠 */
    .market-status {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 10px;
        border-radius: 0px !important;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        color: #444;
    }
    
    .date-time-row {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex; gap: 10px; align-items: center; color: #444;
    }
    .tz-label { font-size: 0.9rem; color: #666; font-weight: normal; margin-left: 5px; }

    /* ボタンのデザイン */
    .stButton > button {
        border-radius: 0px !important;
        border: 1px solid #ddd !important;
        background-color: white; color: #444; font-weight: bold;
        width: 100%; height: 40px;
    }
    [data-testid="stHorizontalBlock"] div:nth-child(1) button { text-align: left; padding-left: 10px; }
    [data-testid="stHorizontalBlock"] div:nth-child(5) button { text-align: right; padding-right: 10px; }

    /* 左右の余白 */
    [data-testid="column"]:first-of-type { padding-right: 60px !important; }
    [data-testid="column"]:last-of-type { padding-left: 60px !important; }
</style>
""", unsafe_allow_html=True)

def draw_calendar_area(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"### {view_date.strftime('%Y年 %m月')}")
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                html += '<td></td>'
            else:
                curr_date = date(view_date.year, view_date.month, day)
                h_name = target_holidays.get(curr_date)
                is_weekend = (i == 0 or i == 6)
                
                # HTML構造の組み立て
                content = f'{day}'
                span_class = ""
                tooltip_html = f'<span class="tooltip-text">{h_name}</span>' if h_name else ""
                container_class = "tooltip-container" if h_name else ""
                underline_class = "has-holiday" if h_name else ""

                if curr_date == now_full.date():
                    html += f'<td><div class="{container_class}"><span class="today-marker">{day}</span>{tooltip_html}</div></td>'
                elif h_name:
                    html += f'<td><div class="{container_class}"><span class="holiday-red {underline_class}">{day}</span>{tooltip_html}</div></td>'
                elif is_weekend:
                    html += f'<td><span class="holiday-red">{day}</span></td>'
                else:
                    html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 2, 1.2, 1.2])
    with c1:
        if st.button("◀", key=f"prev_{state_key}"): move_month(state_key, -1)
    with c3:
        if st.button("今月", key=f"today_{state_key}"): reset_month(state_key, country_tz)
    with c5:
        if st.button("▶", key=f"next_{state_key}"): move_month(state_key, 1)

def move_month(key, delta):
    current = st.session_state[key]
    new_month = current.month + delta
    new_year = current.year
    if new_month > 12: new_month = 1; new_year += 1
    elif new_month < 1: new_month = 12; new_year -= 1
    st.session_state[key] = date(new_year, new_month, 1)

def reset_month(key, country_tz):
    st.session_state[key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)

def get_market_info(now, market_type):
    cc = "US" if market_type == "US" else "JP"
    th = holidays.CountryHoliday(cc)
    is_h = now.date() in th
    if market_type == "US":
        ot, ct = now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)
    else:
        ot, ct = now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0)
    is_wd = 0 <= now.weekday() <= 4
    if not is_wd or is_h:
        r = "週末休み" if not is_wd else f"祝日休場 ({th.get(now.date())})"
        return f"😴 CLOSED ({r})", "#f5f5f5"
    if now < ot:
        d = ot - now
        return f"⏳ CLOSED (開場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#fffbe6"
    elif ot <= now < ct:
        d = ct - now
        return f"🟢 OPEN (閉場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#e6ffed"
    else:
        return "🔴 CLOSED (本日の取引終了)", "#fff1f0"

st.title("📊 日/米 株式市場リアルタイムカレンダー")
col1, col2 = st.columns(2, gap="large")
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)

with col1:
    st.header("🇺🇸 米国市場")
    is_dst = now_ny.dst() != timedelta(0)
    dst_label = "（サマータイム中）" if is_dst else "（非サマータイム：標準時）"
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span class="tz-label">{dst_label}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_ny, "US", "view_date_us", "America/New_York")

with col2:
    st.header("🇯🇵 日本市場")
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_jp, "JP", "view_date_jp", "Asia/Tokyo")
