import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- カレンダーの基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)

# 1分ごとにデータ再取得、1秒ごとに時計更新
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")

st.set_page_config(page_title="日/米 株式市場リアルタイムカレンダー", layout="wide")

# --- 市場データの取得 ---
@st.cache_data(ttl=60)
def get_market_prices():
    tickers = {
        "S&P 500": "^GSPC",
        "金先物": "GC=F",
        "ドル円": "JPY=X"
    }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                data[name] = {"price": curr, "diff": diff, "pct": pct}
            else:
                data[name] = {"price": 0, "diff": 0, "pct": 0}
        except:
            data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

# --- スタイル設定 ---
st.markdown("""
<style>
    body { color: #444; }
    header a { display: none !important; } 
    .stHeaderActionElements { display: none !important; }

    /* ミニボード */
    .indicator-box {
        border: 1px solid #ddd; padding: 10px; text-align: center; background-color: #fff; margin-bottom: 20px;
    }
    .indicator-label { font-size: 0.8rem; color: #888; font-weight: bold; }
    .indicator-value { font-size: 1.2rem; font-weight: bold; margin: 5px 0; }
    .price-up { color: #ff4b4b; } /* 上昇：赤 */
    .price-down { color: #1e90ff; } /* 下落：青 */

    /* カレンダー */
    .calendar-table {
        font-family: 'Courier New', Courier, monospace; text-align: center; width: 100%;
        border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; color: #444;
    }
    .calendar-table tr { height: 40px; }
    .calendar-table td, .calendar-table th { vertical-align: middle; padding: 0; position: relative; }
    .today-marker {
        background-color: #ff4b4b; color: white; display: inline-flex;
        align-items: center; justify-content: center; width: 32px; height: 32px; font-weight: bold;
    }
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    .event-blue { color: #1e90ff; font-weight: bold; border-bottom: 1px dotted #1e90ff; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    
    /* ツールチップ */
    .tooltip-container { position: relative; display: inline-block; cursor: pointer; }
    .tooltip-text {
        visibility: hidden; width: max-content; background-color: #333; color: #fff;
        text-align: left; border-radius: 4px; padding: 6px 10px; position: absolute;
        z-index: 100; bottom: 125%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.1s; font-size: 0.7rem; pointer-events: none;
    }
    .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

    /* その他枠 */
    .event-list-box { border: 1px solid #ddd; padding: 12px; margin-top: 10px; margin-bottom: 15px; background-color: #fafafa; }
    .news-box { border: 1px solid #ddd; padding: 15px; background-color: #fff; min-height: 280px; }
    .market-status { font-size: 1.1rem; font-weight: bold; padding: 10px; border: 1px solid #ddd; color: #444; }
    .date-time-row { font-size: 1.2rem; font-weight: 600; margin-bottom: 10px; display: flex; gap: 10px; align-items: center; }
    .stButton > button { border-radius: 0px !important; border: 1px solid #ddd !important; width: 100%; height: 40px; font-weight: bold; }

    /* 左右の余白（米国左、日本右） */
    [data-testid="column"]:first-of-type { padding-right: 60px !important; }
    [data-testid="column"]:last-of-type { padding-left: 60px !important; }
</style>
""", unsafe_allow_html=True)

# --- 共通ロジック ---
def get_next_open(now, country_code):
    cc = "US" if country_code == "US" else "JP"
    th = holidays.CountryHoliday(cc)
    open_time = time(9, 30) if country_code == "US" else time(9, 0)
    temp_date = now.date()
    if now < datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo) and temp_date.weekday() < 5 and temp_date not in th:
        return datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo)
    while True:
        temp_date += timedelta(days=1)
        if temp_date.weekday() < 5 and temp_date not in th:
            return datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo)

def get_market_info(now, market_type):
    cc = "US" if market_type == "US" else "JP"
    th = holidays.CountryHoliday(cc)
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    next_o = get_next_open(now, market_type)
    diff = next_o - now
    c_down = f"{diff.days*24 + diff.seconds//3600}:{(diff.seconds//60)%60:02d}:{diff.seconds%60:02d}"
    if not (0 <= now.weekday() <= 4) or is_h:
        return f"😴 CLOSED ({'祝日' if is_h else '週末'}) <br><small>次回の開場まで: {c_down}</small>", "#f5f5f5"
    if now < ot: return f"⏳ CLOSED (開場まで: {(ot-now).seconds//3600}:{(ot-now).seconds//60%60:02d}:{(ot-now).seconds%60:02d})", "#fffbe6"
    elif ot <= now < ct: return f"🟢 OPEN (閉場まで: {(ct-now).seconds//3600}:{(ct-now).seconds//60%60:02d}:{(ct-now).seconds%60:02d})", "#e6ffed"
    else: return f"🔴 CLOSED (本日終了) <br><small>次回の開場まで: {c_down}</small>", "#fff1f0"

def get_events(cc, y, m, d):
    evs = []
    wd = date(y,m,d).weekday()
    if cc == "US":
        if d <= 7 and wd == 0: evs.append("ISM製造業 (10:00)")
        if d <= 7 and wd == 4: evs.append("雇用統計 (08:30)")
        if 10 <= d <= 14 and wd <= 4: evs.append("CPI (08:30)")
    else:
        if m in [4,7,10,12] and d <= 3: evs.append("日銀短観 (08:50)")
        if 15 <= d <= 31 and wd <= 4: evs.append("日銀会合")
    return evs

def draw_calendar(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"### {view_date.strftime('%Y年 %m月')}")
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    monthly_events = []
    
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0: html += '<td></td>'
            else:
                curr_date = date(view_date.year, view_date.month, day)
                h_name = target_holidays.get(curr_date)
                m_evs = get_events(country_code, view_date.year, view_date.month, day)
                for e in m_evs: monthly_events.append(f"{day}日: {e}")
                
                content, cls, tip = str(day), "", ""
                if h_name: cls, tip = "holiday-red", f"【祝日】\\n{h_name}"
                elif m_evs: cls, tip = "event-blue", f"【経済イベント】\\n" + "\\n".join(m_evs)
                elif i == 0 or i == 6: cls = "holiday-red"
                if curr_date == now_full.date(): content = f'<span class="today-marker">{day}</span>'
                
                if tip: html += f'<td><div class="tooltip-container"><span class="{cls}">{content}</span><span class="tooltip-text">{tip}</span></div></td>'
                else: html += f'<td><span class="{cls}">{content}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 2, 1.2, 1.2])
    with c1: 
        if st.button("◀", key=f"p_{state_key}"):
            m = st.session_state[state_key].month - 1
            y = st.session_state[state_key].year
            if m < 1: m=12; y-=1
            st.session_state[state_key] = date(y, m, 1)
    with c3:
        if st.button("今月", key=f"t_{state_key}"): st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)
    with c5:
        if st.button("▶", key=f"n_{state_key}"):
            m = st.session_state[state_key].month + 1
            y = st.session_state[state_key].year
            if m > 12: m=1; y+=1
            st.session_state[state_key] = date(y, m, 1)

    if monthly_events:
        items = "".join([f'<div style="font-size:0.85rem;">• {e}</div>' for e in monthly_events])
        st.markdown(f'<div class="event-list-box"><div style="font-weight:bold;font-size:0.9rem;color:#1e90ff;margin-bottom:5px;">📋 {view_date.month}月のイベント</div>{items}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="event-list-box">イベントなし</div>', unsafe_allow_html=True)

# --- 実行 ---
if 'view_date_us' not in st.session_state: st.session_state.view_date_us = datetime.now(pytz.timezone('America/New_York')).date().replace(day=1)
if 'view_date_jp' not in st.session_state: st.session_state.view_date_jp = datetime.now(pytz.timezone('Asia/Tokyo')).date().replace(day=1)

# 指標表示
p = get_market_prices()
cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c_cls = "price-up" if d['diff'] >= 0 else "price-down"
    sym = "▲" if d['diff'] >= 0 else "▼"
    with cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["price"]:,.2f}</div><div class="{c_cls}" style="font-size:0.85rem;">{sym} {abs(d["diff"]):,.2f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)

# 米国・日本の順にカラムを作成
col_us, col_jp = st.columns(2, gap="large")
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)

with col_us:
    st.header("🇺🇸 米国株式市場")
    is_dst = now_ny.dst() != timedelta(0)
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span style="font-size:0.8rem;color:#666;margin-left:5px;">({"サマータイム中" if is_dst else "標準時"})</span></div>', unsafe_allow_html=True)
    st_val, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{st_val}</div>', unsafe_allow_html=True)
    draw_calendar(now_ny, "US", "view_date_us", "America/New_York")
    st.markdown(f'<div class="news-box"><div style="font-weight:bold;">AIが選ぶ今週の政治経済ニュース10</div><div style="font-size:0.75rem;color:#888;">最終更新：{now_ny.strftime("%Y/%m/%d %H:%M")}</div><ul style="font-size:0.9rem;"><li>雇用統計の結果を受けた市場の反応</li><li>FOMC議事録に見る利下げのタイミング</li></ul></div>', unsafe_allow_html=True)

with col_jp:
    st.header("🇯🇵 日本株式市場")
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    st_val, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{st_val}</div>', unsafe_allow_html=True)
    draw_calendar(now_jp, "JP", "view_date_jp", "Asia/Tokyo")
    st.markdown(f'<div class="news-box"><div style="font-weight:bold;">AIが選ぶ今週の政治経済ニュース10</div><div style="font-size:0.75rem;color:#888;">最終更新：{now_jp.strftime("%Y/%m/%d %H:%M")}</div><ul style="font-size:0.9rem;"><li>日銀会合後の金利動向と為替への影響</li><li>春闘回答集計結果と内需セクターの展望</li></ul></div>', unsafe_allow_html=True)
