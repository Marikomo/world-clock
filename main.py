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
    .holiday-text {
        color: #ff4b4b;
        font-weight: bold;
    }
    .calendar-table {
        font-family: monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
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
    .tz-small {
        font-size: 0.9rem;
        color: #666;
        font-weight: normal;
    }
</style>
""", unsafe_allow_html=True)

def draw_calendar(date_obj, country_code):
    # 祝日データの取得
    target_holidays = holidays.CountryHoliday(country_code)
    
    # 日付と時計
    date_str = date_obj.strftime('%Y / %m / %d')
    time_str = date_obj.strftime('%H:%M:%S')
    tz_info = ""
    if country_code == 'US':
        is_dst = date_obj.dst() != timedelta(0)
        tz_info = f'<span class="tz-small"> ({"サマータイム: EDT" if is_dst else "標準時: EST"})</span>'
    
    st.markdown(f'<div class="date-time-row"><span>{date_str}</span><span>{time_str}{tz_info}</span></div>', unsafe_allow_html=True)

    # カレンダー描画
    cal = calendar.monthcalendar(date_obj.year, date_obj.month)
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td></td>'
            else:
                current_date = date(date_obj.year, date_obj.month, day)
                is_holiday = current_date in target_holidays
                
                # 今日のマーク優先、祝日は赤字
                if day == date_obj.day:
                    html += f'<td><span class="today-marker">{day}</span></td>'
                elif is_holiday:
                    html += f'<td><span class="holiday-text">{day}</span></td>'
                else:
                    html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)
    
    # 本日が祝日の場合、祝日名を表示
    if date(date_obj.year, date_obj.month, date_obj.day) in target_holidays:
        st.caption(f"📍 本日は祝日です: {target_holidays.get(date(date_obj.year, date_obj.month, date_obj.day))}")

def get_market_info(now, market_type):
    # 祝日判定
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
        reason = "週末休み" if not is_weekday else "祝日休場"
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
tz_ny = pytz.timezone('America/New_York')
tz_jp = pytz.timezone('Asia/Tokyo')
now_ny = datetime.now(tz_ny)
now_jp = datetime.now(tz_jp)

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
