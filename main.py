import streamlit as st
from datetime import datetime
import pytz
import calendar

st.set_page_config(page_title="Market Calendar & Clock", layout="wide")
st.title("🗓️ Global Market Dashboard")

# タイムゾーンの設定
tz_ny = pytz.timezone('America/New_York')
tz_jp = pytz.timezone('Asia/Tokyo')

# 現在時刻の取得
now_ny = datetime.now(tz_ny)
now_jp = datetime.now(tz_jp)

# 画面を2列に分ける
col1, col2 = st.columns(2)

# --- アメリカ（ニューヨーク）側 ---
with col1:
    st.subheader("🇺🇸 New York / East Coast")
    
    # カレンダーの表示
    cal_ny = calendar.TextCalendar(calendar.SUNDAY).formatmonth(now_ny.year, now_ny.month)
    # 今日をハイライト（簡易的なテキスト置換）
    day_str = str(now_ny.day).rjust(2)
    cal_ny = cal_ny.replace(f" {day_str} ", f"[{day_str}]")
    
    st.code(cal_ny, language='text') # 等幅フォントでカレンダーを表示
    
    st.metric("Current Time", now_ny.strftime('%H:%M:%S'))
    
    # 市場判定
    is_open_ny = 9 <= now_ny.hour < 16 or (now_ny.hour == 9 and now_ny.minute >= 30)
    if 0 <= now_ny.weekday() <= 4 and is_open_ny:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")

# --- 日本（東京）側 ---
with col2:
    st.subheader("🇯🇵 Tokyo / Japan")
    
    # カレンダーの表示
    cal_jp = calendar.TextCalendar(calendar.SUNDAY).formatmonth(now_jp.year, now_jp.month)
    day_str_jp = str(now_jp.day).rjust(2)
    cal_jp = cal_jp.replace(f" {day_str_jp} ", f"[{day_str_jp}]")
    
    st.code(cal_jp, language='text')
    
    st.metric("Current Time", now_jp.strftime('%H:%M:%S'))
    
    # 市場判定
    is_open_jp = 9 <= now_jp.hour < 15
    if 0 <= now_jp.weekday() <= 4 and is_open_jp:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")

st.info("※ カレンダーの [ ] で囲まれた数字が、それぞれの地域の今日の日付です。")
