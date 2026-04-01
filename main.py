import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 言語設定の初期化 ---
if 'lang' not in st.session_state:
    st.session_state.lang = "JP"

# サイドバーで言語切り替え
with st.sidebar:
    st.session_state.lang = st.radio("Language / 言語", ["JP", "EN"], horizontal=True)

# テキスト辞書（中略：以前と同じものを維持）
T = {
    "JP": {
        "title": "📊 日/米 株式市場リアルタイムカレンダー",
        "us_market": "🇺🇸 米国株式市場",
        "jp_market": "🇯🇵 日本株式市場",
        "dst": "サマータイム中",
        "std": "標準時",
        "open": "🟢 OPEN (閉場まで: ",
        "closed_pre": "⏳ CLOSED (開場まで: ",
        "closed_post": "🔴 CLOSED (本日終了)",
        "next_open": "次回の開場まで: ",
        "weekend": "週末",
        "holiday": "祝日",
        "update": "最終更新：",
        "prev": "◀",
        "next": "▶",
        "today": "今月"
    },
    "EN": {
        "title": "📊 Japan/US Stock Market Real-time Calendar",
        "us_market": "🇺🇸 US Stock Market",
        "jp_market": "🇯🇵 Japan Stock Market",
        "dst": "Daylight Saving",
        "std": "Standard Time",
        "open": "🟢 OPEN (Closes in: ",
        "closed_pre": "⏳ CLOSED (Opens in: ",
        "closed_post": "🔴 CLOSED (Market Closed)",
        "next_open": "Next Open in: ",
        "weekend": "Weekend",
        "holiday": "Holiday",
        "update": "Last Update: ",
        "prev": "Prev",
        "next": "Next",
        "today": "Current"
    }
}
L = T[st.session_state.lang]

# --- 基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title=L["title"], layout="wide")

# --- スタイル設定（おしゃれヘッダータイトルの実装） ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500&display=swap" rel="stylesheet">

<style>
    body { color: #444; }
    
    /* ヘッダーのロゴ位置にタイトルを表示するためのスタイル */
    [data-testid="stHeader"] {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        padding-left: 15px;
    }
    
    /* ストリームリットのロゴ、その他アイコンを非表示 */
    [data-testid="stHeader"] .viewerBadge_container__1QSob,
    [data-testid="stHeader"] .main-svg,
    [data-testid="stHeader"] header a,
    [data-testid="stHeader"] .stHeaderActionElements,
    [data-testid="stSidebar"] div:nth-child(1) button {
        display: none !important;
    }
    
    /* 自作のヘッダータイトル */
    .header-logo-title {
        font-family: 'Playfair Display', serif; /* おしゃれフォント */
        font-size: 1.0rem; /* ロゴサイズ */
        color: #666; /* 目立ちすぎないグレー */
        font-style: italic; /* 斜体でよりおしゃれに */
        margin-right: auto; /* 左寄せ */
        padding: 5px 10px;
        line-height: 1;
        cursor: default;
    }

    /* その他既存のスタイル */
    .indicator-box { border: 1px solid #ddd; padding: 10px; text-align: center; background-color: #fff; margin-bottom: 20px; }
    .indicator-label { font-size: 0.8rem; color: #888; font-weight: bold; }
    .indicator-value { font-size: 1.2rem; font-weight: bold; margin: 5px 0; }
    .price-up { color: #ff4b4b; }
    .price-down { color: #1e90ff; }
    .calendar-table { font-family: 'Courier New', Courier, monospace; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }
    .calendar-table tr { height: 40px; }
    .calendar-table td, .calendar-table th { vertical-align: middle; padding: 0; position: relative; }
    .today-marker { background-color: #ff4b4b; color: white; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; font-weight: bold; }
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    .event-blue { color: #1e90ff; font-weight: bold; border-bottom: 1px dotted #1e90ff; }
    .tooltip-container { position: relative; display: inline-block; cursor: pointer; }
    .tooltip-text { visibility: hidden; width: max-content; background-color: #333; color: #fff; text-align: left; border-radius: 4px; padding: 6px 10px; position: absolute; z-index: 100; bottom: 125%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.1s; font-size: 0.7rem; pointer-events: none; }
    .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }
    .news-box { border: 1px solid #ddd; padding: 15px; background-color: #fff; min-height: 280px; }
    .market-status { font-size: 1.1rem; font-weight: bold; padding: 10px; border: 1px solid #ddd; }
    .date-time-row { font-size: 1.2rem; font-weight: 600; margin-bottom: 10px; display: flex; gap: 10px; align-items: center; }
    .stButton > button { border-radius: 0px !important; border: 1px solid #ddd !important; width: 100%; height: 40px; font-weight: bold; }
    [data-testid="column"]:first-of-type { padding-right: 60px !important; }
    [data-testid="column"]:last-of-type { padding-left: 60px !important; }
</style>
""", unsafe_allow_html=True)

# --- ロジック関数 (中略：以前と同じものを維持) ---
@st.cache_data(ttl=60)
def get_market_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            diff = curr - prev
            data[name] = {"price": curr, "diff": diff, "pct": (diff/prev)*100}
        except: data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

def get_next_open(now, country_code):
    cc = "US" if country_code == "US" else "JP"
    th, open_time = holidays.CountryHoliday(cc), time(9, 30) if country_code == "US" else time(9, 0)
    temp_date = now.date()
    if now < datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo) and temp_date.weekday() < 5 and temp_date not in th:
        return datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo)
    while True:
        temp_date += timedelta(days=1)
        if temp_date.weekday() < 5 and temp_date not in th:
            return datetime.combine(temp_date, open_time).replace(tzinfo=now.tzinfo)

def get_market_status_ui(now, market_type):
    cc, th = "US" if market_type == "US" else "JP", holidays.CountryHoliday("US" if market_type == "US" else "JP")
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    next_o = get_next_open(now, market_type)
    diff = next_o - now
    c_down = f"{diff.days*24 + diff.seconds//3600}:{(diff.seconds//60)%60:02d}:{diff.seconds%60:02d}"
    if not (0 <= now.weekday() <= 4) or is_h:
        reason = L["weekend"] if not (0 <= now.weekday() <= 4) else f"{L['holiday']} ({th.get(now.date())})"
        return f"😴 CLOSED ({reason}) <br><small>{L['next_open']} {c_down}</small>", "#f5f5f5"
    if now < ot: d = ot - now; return f"{L['closed_pre']} {d.seconds//3600:02d}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#fffbe6"
    elif ot <= now < ct: d = ct - now; return f"{L['open']} {d.seconds//3600:02d}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#e6ffed"
    else: return f"{L['closed_post']} <br><small>{L['next_open']} {c_down}</small>", "#fff1f0"

def draw_market_calendar(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"### {view_date.strftime('%Y/%m' if st.session_state.lang == 'JP' else '%B %Y')}")
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    html = f'<table class="calendar-table"><tr><th>{"Su" if st.session_state.lang == "EN" else "日"}</th><th>{"Mo" if st.session_state.lang == "EN" else "月"}</th><th>{"Tu" if st.session_state.lang == "EN" else "火"}</th><th>{"We" if st.session_state.lang == "EN" else "水"}</th><th>{"Th" if st.session_state.lang == "EN" else "木"}</th><th>{"Fr" if st.session_state.lang == "EN" else "金"}</th><th>{"Sa" if st.session_state.lang == "EN" else "土"}</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0: html += '<td></td>'
            else:
                curr_date = date(view_date.year, view_date.month, day)
                h_name = target_holidays.get(curr_date)
                content, cls, tip = str(day), "", ""
                if h_name: cls, tip = "holiday-red", f"[{L['holiday']}]\\n{h_name}"
                elif i == 0 or i == 6: cls = "holiday-red"
                if curr_date == now_full.date(): content = f'<span class="today-marker">{day}</span>'
                if tip: html += f'<td><div class="tooltip-container"><span class="{cls}">{content}</span><span class="tooltip-text">{tip}</span></div></td>'
                else: html += f'<td><span class="{cls}">{content}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 2, 1.2, 1.2])
    with c1: 
        if st.button(L["prev"], key=f"p_{state_key}"):
            m, y = st.session_state[state_key].month - 1, st.session_state[state_key].year
            if m < 1: m=12; y-=1
            st.session_state[state_key] = date(y, m, 1)
    with c3:
        if st.button(L["today"], key=f"t_{state_key}"): st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)
    with c5:
        if st.button(L["next"], key=f"n_{state_key}"):
            m, y = st.session_state[state_key].month + 1, st.session_state[state_key].year
            if m > 12: m=1; y+=1
            st.session_state[state_key] = date(y, m, 1)

# --- メイン実行 ---

# おしゃれなヘッダータイトル（ロゴ位置）を強制挿入
st.markdown('<div class="header-logo-title">Stock Market Real-time Event Calendar</div>', unsafe_allow_html=True)

# メイン画面のタイトルは日英切り替え対応
st.title(L["title"])

p = get_market_prices()
cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c_cls, sym = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with cols[i]: st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["price"]:,.2f}</div><div class="{c_cls}" style="font-size:0.85rem;">{sym} {abs(d["diff"]):,.2f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)

col_us, col_jp = st.columns(2, gap="large")
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)

if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

with col_us:
    st.header(L["us_market"])
    dst_lbl = L["dst"] if now_ny.dst() != timedelta(0) else L["std"]
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span style="font-size:0.8rem;color:#666;margin-left:5px;">({dst_lbl})</span></div>', unsafe_allow_html=True)
    st_val, color = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{st_val}</div>', unsafe_allow_html=True)
    draw_market_calendar(now_ny, "US", "v_us", "America/New_York")

with col_jp:
    st.header(L["jp_market"])
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    st_val, color = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{st_val}</div>', unsafe_allow_html=True)
    draw_market_calendar(now_jp, "JP", "v_jp", "Asia/Tokyo")
