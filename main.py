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
    body { color: #444; }
    header a { display: none !important; } 
    .stHeaderActionElements { display: none !important; }

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
    
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px; height: 32px; font-weight: bold;
    }
    
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    /* 経済イベント用の青色設定 */
    .event-blue { color: #1e90ff; font-weight: bold; border-bottom: 1px dotted #1e90ff; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    
    /* ツールチップ */
    .tooltip-container { position: relative; display: inline-block; cursor: pointer; }
    .tooltip-text {
        visibility: hidden;
        width: max-content;
        background-color: #333;
        color: #fff;
        text-align: left;
        border-radius: 4px;
        padding: 6px 10px;
        position: absolute;
        z-index: 100;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.1s;
        font-size: 0.7rem;
        white-space: pre-wrap;
        pointer-events: none;
        line-height: 1.4;
    }
    .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

    .news-box {
        border: 1px solid #ddd;
        padding: 15px;
        margin-top: 20px;
        color: #444;
        background-color: #fff;
        min-height: 280px;
    }
    .news-title { font-weight: bold; font-size: 1.0rem; margin-bottom: 5px; }
    .news-update-time { font-size: 0.75rem; color: #888; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
    .news-list { margin: 0; padding-left: 20px; font-size: 0.9rem; line-height: 1.8; }

    .market-status {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 10px;
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
    .tz-label { font-size: 0.8rem; color: #666; }

    .stButton > button {
        border: 1px solid #ddd !important;
        background-color: white; color: #444; font-weight: bold;
        width: 100%; height: 40px;
    }

    [data-testid="column"]:first-of-type { padding-right: 60px !important; }
    [data-testid="column"]:last-of-type { padding-left: 60px !important; }
</style>
""", unsafe_allow_html=True)

# --- イベント判定ロジック ---
def get_market_events(country_code, year, month, day):
    evs = []
    d = date(year, month, day)
    weekday = d.weekday() # 0=Mon, 4=Fri
    
    if country_code == "US":
        # ISM製造業 (第1営業日)
        if day <= 7 and weekday == 0: evs.append("ISM製造業景況指数 (10:00)")
        # 雇用統計 (第1金曜日)
        if day <= 7 and weekday == 4: evs.append("雇用統計 (08:30)")
        # CPI (中旬 10-15日頃)
        if 10 <= day <= 14 and weekday <= 4: evs.append("CPI 消費者物価指数 (08:30)")
        # PPI (CPIの翌営業日付近)
        if 13 <= day <= 17 and weekday <= 4: evs.append("PPI 生産者物価指数 (08:30)")
        # ジャクソンホール (8月下旬)
        if month == 8 and 20 <= day <= 28: evs.append("ジャクソンホール会合")
        # 中間選挙 (11月第1月曜の翌火曜 - 偶数年)
        if month == 11 and year % 4 == 2 and 2 <= day <= 8 and weekday == 1: evs.append("中間選挙")

    else: # JP
        # 日銀短観 (4,7,10,12月の月初)
        if month in [4, 7, 10, 12] and day <= 3: evs.append("日銀短観 (08:50)")
        # 春闘回答 (3月半ば)
        if month == 3 and 10 <= day <= 20 and weekday <= 4: evs.append("春闘集中回答日")
        # CPI (20日頃)
        if 18 <= day <= 22 and weekday <= 4: evs.append("CPI 消費者物価指数 (08:30)")
        # 日銀会合 (各月下旬)
        if 15 <= day <= 31 and weekday <= 4: evs.append("日銀金融政策決定会合")
        
    return evs

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
                m_events = get_market_events(country_code, view_date.year, view_date.month, day)
                
                content = str(day)
                cls = ""
                tip = ""
                
                if h_name:
                    cls = "holiday-red"
                    tip = f"【祝日】\n{h_name}"
                elif m_events:
                    cls = "event-blue"
                    tip = f"【経済イベント】\n" + "\n".join(m_events)
                elif i == 0 or i == 6:
                    cls = "holiday-red"

                # 今日の強調
                if curr_date == now_full.date():
                    content = f'<span class="today-marker">{day}</span>'
                
                if tip:
                    html += f'<td><div class="tooltip-container"><span class="{cls}">{content}</span><span class="tooltip-text">{tip}</span></div></td>'
                else:
                    html += f'<td><span class="{cls}">{content}</span></td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])
    with c1:
        if st.button("◀", key=f"p_{state_key}"): move_month(state_key, -1)
    with c3:
        if st.button("今月", key=f"t_{state_key}"): reset_month(state_key, country_tz)
    with c5:
        if st.button("▶", key=f"n_{state_key}"): move_month(state_key, 1)

def move_month(key, delta):
    curr = st.session_state[key]
    nm = curr.month + delta
    ny = curr.year
    if nm > 12: nm=1; ny+=1
    elif nm < 1: nm=12; ny-=1
    st.session_state[key] = date(ny, nm, 1)

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

# --- セッション状態 ---
if 'view_date_us' not in st.session_state:
    st.session_state.view_date_us = datetime.now(pytz.timezone('America/New_York')).date().replace(day=1)
if 'view_date_jp' not in st.session_state:
    st.session_state.view_date_jp = datetime.now(pytz.timezone('Asia/Tokyo')).date().replace(day=1)

st.title("📊 日/米 株式市場リアルタイムカレンダー")
col1, col2 = st.columns(2, gap="large")
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)

with col1:
    st.header("🇺🇸 米国株式市場")
    dst_label = "（サマータイム中）" if now_ny.dst() != timedelta(0) else "（標準時）"
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span class="tz-label">{dst_label}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_ny, "US", "view_date_us", "America/New_York")
    
    st.markdown(f'<div class="news-box"><div class="news-title">AIが選ぶ今週の政治経済ニュース10（{now_ny.strftime("%Y年%m月%d日")}）</div><div class="news-update-time">（最終更新：{now_ny.strftime("%Y/%m/%d %H:%M")}）</div><ul class="news-list"><li>雇用統計の結果を受けた市場の反応</li><li>FOMC議事録に見る利下げのタイミング</li><li>ハイテク株の決算発表に向けた動き</li><li>原油価格上昇によるインフレ懸念の再燃</li><li>大統領選に向けた支持率調査の最新動向</li></ul></div>', unsafe_allow_html=True)

with col2:
    st.header("🇯🇵 日本株式市場")
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_jp, "JP", "view_date_jp", "Asia/Tokyo")
    
    st.markdown(f'<div class="news-box"><div class="news-title">AIが選ぶ今週の政治経済ニュース10（{now_jp.strftime("%Y年%m月%d日")}）</div><div class="news-update-time">（最終更新：{now_jp.strftime("%Y/%m/%d %H:%M")}）</div><ul class="news-list"><li>日銀会合での追加利上げ議論の行方</li><li>春闘回答を受けた国内消費の回復見通し</li><li>円安進行に伴う介入警戒感の強まり</li><li>半導体関連株の国内投資拡大に関する最新報</li><li>総選挙に向けた各党の経済公約比較</li></ul></div>', unsafe_allow_html=True)
