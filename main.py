import streamlit as st
from datetime import datetime, timedelta, date
import pytz
import calendar
import holidays
from streamlit_autorefresh import st_autorefresh

# 1秒ごとに更新
st_autorefresh(interval=1000, key="datetimereload")

st.set_page_config(page_title="日/米 株式市場リアルタイムカレンダー", layout="wide")

# --- スタイル設定 ---
st.markdown("""
<style>
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        border-radius: 50%;
        padding: 5px;
        font-weight: bold;
        display: inline-block;
        width: 28px;
        height: 28px;
        line-height: 28px;
    }
    .holiday-red {
        color: #ff4b4b;
        font-weight: bold;
    }
    /* 祝日（title属性あり）のみカーソルを「？」にする */
    [title] {
        cursor: help;
    }
    .calendar-table {
        font-family: monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .calendar-table th { padding: 5px; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    .market-status {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .date-time-row {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 5px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .tz-small { font-size: 0.9rem; color: #666; font-weight: normal; }
</style>
""", unsafe_allow_html=True)

def draw_calendar(date_obj, country_code):
    target_holidays = holidays.CountryHoliday(country_code)
    
    date_str = date_obj.strftime('%Y / %m / %d')
    time_str = date_obj.strftime('%H:%M:%S')
    tz_info = ""
    if country_code == 'US':
        is_dst = date_obj.dst() != timedelta(0)
        tz_info = f'<span class="tz-small"> ({"サマータイム: EDT" if is_dst else "標準時: EST"})</span>'
    
    st.markdown(f'<div class="date-time-row"><span>{date_str}</span><span>{time_str}{tz_info}</span></div>', unsafe_allow_html=True)

    cal = calendar.monthcalendar(date_obj.year, date_obj.month)
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                html += '<td></td>'
            else:
                current_date = date(date_obj.year, date_obj.month, day)
                holiday_name = target_holidays.get(current_date)
                is_weekend = (i == 0 or i == 6)
                
                # ホバー用テキスト（祝日の場合のみ設定）
                tooltip = f'title="{holiday_name}"' if holiday_name else ""
                
                if day == date_obj.day:
                    # 今日。祝日なら祝日名を出す
                    html += f'<td><span class="today-marker" {tooltip}>{day}</span></td>'
                elif holiday_name:
                    # 祝日（赤字 ＋ ホバーあり）
                    html += f'<td><span class="holiday-red" {tooltip}>{day}</span></td>'
                elif is_weekend:
                    # ただの土日（赤字 ＋ ホバーなし）
                    html += f'<td><span class="holiday-red">{day}</span></td>'
                else:
                    # 平日
                    html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

def get_market_info(now, market_type):
    country_code = "US" if market_type == "US" else "JP"
    target_holidays = holidays.CountryHoliday(country_code)
    is_holiday = date(now.year, now.month, now.day) in target_holidays
    
    if market_type == "US":
        open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    else:
        open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        close_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    
    is_weekday = 0 <= now.weekday() <= 4
    if not is_weekday or is_holiday:
        reason = "週末休み" if not is_weekday else f"祝日休場 ({target_holidays.get(date(now.year, now.month, now.day))})"
        return f"😴 CLOSED ({reason})", "#f5f5f5"
    
    if now < open_time:
        diff = open_time - now
        h, m, s = diff.seconds // 3600, (diff.seconds // 60) % 60, diff.seconds % 60
        return f"⏳ CLOSED (開場まで: {h}:{m:02d}:{s:02d})", "#fffbe6"
    elif open_time <= now < close_time:
        diff = close_time - now
        h, m, s = diff.seconds // 3600, (diff.seconds // 60) % 60, diff.seconds % 60
        return f"🟢 OPEN (閉場まで: {h}:{m:02d}:{s:02d})", "#e6ffed"
    else:
        return "🔴 CLOSED (本日の取引終了)", "#fff1f0"

# 実行
now_ny = datetime.now(pytz.timezone('America/New_York'))
now_jp = datetime.now(pytz.timezone('Asia/Tokyo'))

st.title("📊 日/米 株式市場リアルタイムカレンダー")

col1, col2 = st.columns(2)
with col1:
    st.header("🇺🇸 米国株式市場")
    status, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar(now_ny, "US")

with col2:
    st.header("🇯🇵 日本株式市場")
    status, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar(now_jp, "JP")
