import streamlit as st
from datetime import datetime
import pytz
import calendar

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
        width: 25px;
        height: 25px;
        line-height: 25px;
    }
    .calendar-table {
        font-family: monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
    }
    .market-status {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .time-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #31333F;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def draw_calendar(date_obj):
    # 1. 日付の表示
    st.markdown(f"#### {date_obj.strftime('%Y / %m / %d')}")
    
    # 2. 時計の表示（日付のすぐ後ろ）
    time_str = date_obj.strftime('%H:%M:%S')
    
    # サマータイム判定（アメリカのみ）
    tz_info = ""
    if date_obj.tzinfo.zone == 'America/New_York':
        is_dst = date_obj.dst() != timedelta(0)
        tz_info = " (サマータイム中: EDT)" if is_dst else " (標準時: EST)"
    
    st.markdown(f'<div class="time-display">{time_str}{tz_info}</div>', unsafe_allow_html=True)

    # 3. カレンダーの表示
    cal = calendar.monthcalendar(date_obj.year, date_obj.month)
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    for week in cal:
        html += '<tr>'
        for day in week:
            if day == 0:
                html += '<td></td>'
            elif day == date_obj.day:
                html += f'<td><span class="today-marker">{day}</span></td>'
            else:
                html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

def get_market_info(now, market_type):
    if market_type == "US":
        open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    else: # JP
        open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        close_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    
    is_weekday = 0 <= now.weekday() <= 4
    if is_weekday:
        if now < open_time:
            diff = open_time - now
            h, m = divmod(diff.seconds // 60, 60)
            status_text = f"⏳ CLOSED (開場まで: {h}時間{m}分)"
            color = "#fffbe6"
        elif open_time <= now < close_time:
            diff = close_time - now
            h, m = divmod(diff.seconds // 60, 60)
            status_text = f"🟢 OPEN (閉場まで: {h}時間{m}分)"
            color = "#e6ffed"
        else:
            status_text = "🔴 CLOSED (本日の取引終了)"
            color = "#fff1f0"
    else:
        status_text = "😴 CLOSED (週末休み)"
        color = "#f5f5f5"
    return status_text, color

# タイムゾーン設定
from datetime import timedelta
tz_ny = pytz.timezone('America/New_York')
tz_jp = pytz.timezone('Asia/Tokyo')
now_ny = datetime.now(tz_ny)
now_jp = datetime.now(tz_jp)

# タイトル
st.title("📊 日
