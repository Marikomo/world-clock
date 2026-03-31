import streamlit as st
from datetime import datetime
import pytz

st.set_page_config(page_title="Market Clock", layout="wide")
st.title("🕒 Global Market Monitor")

# タイムゾーンの設定
tz_ny = pytz.timezone('America/New_York')
tz_jp = pytz.timezone('Asia/Tokyo')

# 現在時刻の取得
now_ny = datetime.now(tz_ny)
now_jp = datetime.now(tz_jp)

# 画面を2列に分ける
col1, col2 = st.columns(2)

with col1:
    st.subheader("🇺🇸 New York (EST/EDT)")
    st.metric("Current Time", now_ny.strftime('%H:%M:%S'))
    
    # 市場が開いているかどうかの判定 (9:30 - 16:00)
    is_open_ny = 9 <= now_ny.hour < 16 or (now_ny.hour == 9 and now_ny.minute >= 30)
    if 0 <= now_ny.weekday() <= 4 and is_open_ny:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")

with col2:
    st.subheader("🇯🇵 Tokyo (JST)")
    st.metric("Current Time", now_jp.strftime('%H:%M:%S'))
    
    # 日本市場の判定 (9:00 - 15:00, 昼休み除く)
    is_open_jp = 9 <= now_jp.hour < 15
    if 0 <= now_jp.weekday() <= 4 and is_open_jp:
        st.success("🟢 Market is OPEN")
    else:
        st.error("🔴 Market is CLOSED")

st.info("※ 土日は両市場とも閉場しています。")
