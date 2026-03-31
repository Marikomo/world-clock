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

# --- スタイル設定 ---
st.markdown("""
<style>
    /* カレンダーテーブル */
    .calendar-table {
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        margin-bottom: 20px;
    }
    .calendar-table tr { height: 40px; }
    .calendar-table td, .calendar-table th { vertical-align: middle; padding: 0; }
    
    /* 今日のマーカー（ここだけは意図的に丸いデザインを維持していますが、四角くすることも可能です） */
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        border-radius: 0%; /* 角張ったデザインに変更 */
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        font-weight: bold;
    }
    
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    .has-tooltip { cursor: pointer; border-bottom: 1px dotted #ff4b4b; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    
    /* 市場ステータス枠（角張ったデザイン） */
    .market-status {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 10px;
        border-radius: 0px !important; /* 角丸をゼロに */
        margin-bottom: 10px;
        border: 1px solid #ccc;
    }
    
    /* 時計と日付の行 */
    .date-time-row {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        gap: 10px;
        align-items: center;
    }
    .tz-small { font-size: 0.8rem; color: #666; font-weight: normal; }

    /* ボタンのデザイン（角張ったデザイン） */
    .stButton > button {
        border-radius: 0px !important; /* 角丸をゼロに */
        border: 1px solid #444;
        background-color: white;
        color: #444;
        font-weight: bold;
        width: 100%;
    }
    .stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

def move_month(key, delta):
    current = st.session_state[key]
    new_month = current.month + delta
    new_year = current.year
    if new_month > 12:
        new_month = 1; new_year += 1
    elif new_month < 1:
        new_month = 12; new_year -= 1
    st.session_state[key] = date(new_year, new_month, 1)

def reset_month(key, country_tz):
    st.session_state[key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)

def draw_calendar_area(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"### {view_date.strftime('%Y年 %m月')}")

    # 祝日取得
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    
    # カレンダー本体
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                html += '<td></td>'
            else:
                curr_date = date(view_date.year, view_date.month, day)
                holiday_name = target_holidays.get(curr_date)
                is_weekend = (i == 0 or i == 6)
                tooltip = f'title="{holiday_name}"' if holiday_name else ""
                
                if curr_date == now_full.date():
                    html += f'<td><span class="today-marker" {tooltip}>{day}</span></td>'
                elif holiday_name:
                    html += f'<td><span class="holiday-red has-tooltip" title="{holiday_name}">{day}</span></td>'
                elif is_weekend:
                    html += f'<td><span class="holiday-red">{day}</span></td>'
                else:
                    html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    # 操作ボタン（カレンダーの下に配置）
    col_prev, col_today, col_next = st.columns([1, 1, 1])
    with col_prev:
        if st.button("◀", key=f"prev_{state_key}"):
            move_month(state_key, -1)
    with col_today:
        if st.button("今月", key=f"today_{state_key}"):
            reset_month(state_key, country_tz)
    with col_next:
        if st.button("▶", key=f"next_{state_key}"):
            move_month(state_key, 1)

def get_market_info(now, market_type):
    country_code = "US" if market_type == "US" else "JP"
    target_holidays = holidays.CountryHoliday(country_code)
    is_holiday = now.date() in target_holidays
    
    if market_type == "US":
        open_t, close_t = now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)
    else:
        open_t, close_t = now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0)
    
    is_weekday = 0 <= now.weekday() <= 4
    if not is_weekday or is_holiday:
        reason = "週末休み" if not is_weekday else f"祝日休場 ({target_holidays.get(now.date())})"
        return f"😴 CLOSED ({reason})", "#f5f5f5"
    
    if now < open_t:
        d = open_t - now
        return f"⏳ CLOSED (開場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#fffbe6"
    elif open_t <= now < close_t:
        d = close_t - now
        return f"🟢 OPEN (閉場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#e6ffed"
    else:
        return "🔴 CLOSED (本日の取引終了)", "#fff1f0"

# メイン表示
st.title("📊 日/米 株式市場リアルタイムカレンダー")

now_ny = datetime.now(pytz.timezone('America/New_York'))
now_jp = datetime.now(pytz.timezone('Asia/Tokyo'))

col1, col2 = st.columns(2)

with col1:
    st.header("🇺🇸 米国市場")
    is_dst = now_ny.dst() != timedelta(0)
    tz_label = "EDT" if is_dst else "EST"
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span class="tz-small">({tz_label})</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_ny, "US", "view_date_us", "America/New_York")

with col2:
    st.header("🇯🇵 日本市場")
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_jp, "JP", "Asia/Tokyo")
