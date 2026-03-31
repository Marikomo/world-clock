import streamlit as st
from datetime import datetime
import pytz
import calendar

st.set_page_config(page_title="Market Calendar & Clock", layout="wide")

# --- スタイル設定（カレンダーの見た目） ---
st.markdown("""
<style>
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        border-radius: 50%;
        padding: 5px;
        font-weight: bold;
    }
    .calendar-table {
        font-family: monospace;
        line-height: 2;
        text-align: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def draw_calendar(date_obj):
    # 年月を表示
    st.markdown(f"### {date_obj.strftime('%Y / %m / %d')}")
    
    # カレンダーの作成
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

st.title("🗓️ Global Market Dashboard")

# タイムゾーンの設定
tz_ny = pytz.timezone('America/New_York')
tz_jp = pytz.timezone('Asia/Tokyo')

now_ny = datetime.now(tz_ny)
now_jp = datetime.now(tz_jp)

col1, col2 = st.columns(2)

# --- アメリカ（ニューヨーク）側 ---
with col1:
    st.subheader("🇺🇸 New York / East Coast")
    draw_calendar(now_ny) # カレンダー描画
    st.metric("Current Time", now_ny.strftime('%H:%M:%S'))
    
    is_open_ny = 9 <= now_ny.hour < 16 or (now_ny.hour == 9 and now_ny.minute >= 30)
    if 0 <= now_ny.weekday() <= 4 and is_open_ny:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")

# --- 日本（東京）側 ---
with col2:
    st.subheader("🇯🇵 Tokyo / Japan")
    draw_calendar(now_jp) # カレンダー描画
    st.metric("Current Time", now_jp.strftime('%H:%M:%S'))
    
    is_open_jp = 9 <= now_jp.hour < 15
    if 0 <= now_jp.weekday() <= 4 and is_open_jp:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")
