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

# --- 基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Stock Market Calendar", layout="wide")

# テキスト辞書
T = {
    "JP": {
        "us_market": "🇺🇸 米国市場", "jp_market": "🇯🇵 日本市場",
        "dst": "サマータイム中", "std": "標準時",
        "open": "🟢 OPEN (閉場まで: ", "closed_pre": "⏳ CLOSED (開場まで: ",
        "closed_post": "🔴 CLOSED (本日終了)", "next_open": "次回の開場まで: ",
        "weekend": "週末", "holiday": "祝日", "prev": "◀", "next": "▶", "today": "今月"
    },
    "EN": {
        "us_market": "🇺🇸 US Market", "jp_market": "🇯🇵 JP Market",
        "dst": "Daylight Saving", "std": "Standard Time",
        "open": "🟢 OPEN (Closes in: ", "closed_pre": "⏳ CLOSED (Opens in: ",
        "closed_post": "🔴 CLOSED (Market Closed)", "next_open": "Next Open in: ",
        "weekend": "Weekend", "holiday": "Holiday", "prev": "Prev", "next": "Next", "today": "Current"
    }
}
L = T[st.session_state.lang]

# --- スタイル設定（経済系シンプル・太字・大余白） ---
st.markdown("""
<style>
    /* ヘッダー全体の設定 */
    header[data-testid="stHeader"] { background-color: white; height: 4rem; display: flex; align-items: center; padding: 0 1rem; border-bottom: 1px solid #f0f2f6; }
    header[data-testid="stHeader"] div:first-child, header[data-testid="stHeader"] .stHeaderActionElements { display: none !important; }
    
    /* 経済系シンプルフォントのロゴタイトル */
    .header-logo-title { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        font-weight: 800; 
        font-size: 1.0rem; 
        color: #222; 
        letter-spacing: -0.02em;
    }

    /* メインの大タイトル（経済系・極太・特大） */
    .main-big-title {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 3.5rem; /* さらに大きく */
        font-weight: 900; /* 極太 */
        color: #111;
        text-align: center;
        letter-spacing: -0.04em; /* 文字間を詰めて力強く */
        margin-top: 40px;
        margin-bottom: 80px; /* 下の余白を特大に */
        line-height: 1.1;
    }

    /* モバイル対応：タイトルのレスポンシブ設定 */
    @media (max-width: 640px) {
        .main-big-title { font-size: 1.8rem; margin-bottom: 40px; }
    }

    .main-spacer { margin-top: 60px; }
    
    /* 価格ボード */
    .indicator-box { border: 1px solid #ddd; padding: 10px; text-align: center; background-color: #fff; margin-bottom: 15px; }
    .indicator-label { font-size: 0.75rem; color: #666; font-weight: 700; text-transform: uppercase; }
    .indicator-value { font-size: 1.1rem; font-weight: 800; margin: 2px 0; color: #111; }
    
    /* カレンダー操作ボタン */
    .stButton > button { border-radius: 0px !important; border: 1px solid #ccc !important; width: 100%; height: 38px; font-weight: 700; font-size: 0.85rem; background-color: #fff; color: #333; }
    .stButton > button:hover { border-color: #111 !important; color: #111 !important; }
    
    /* カレンダーテーブル */
    .calendar-table { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 0.9rem; }
    .calendar-table th { font-weight: 800; color: #222; padding-bottom: 10px; }
    .calendar-table tr { height: 40px; }
    .today-marker { background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; }
    
    .price-up { color: #d71920; } /* 経済系らしい深めの赤 */
    .price-down { color: #0050b3; } /* 経済系らしい深めの青 */
    .market-status { font-size: 0.95rem; font-weight: 800; padding: 12px; border: 1px solid #ddd; margin-bottom: 15px; background-color: #fff; }
    
    /* 余白調整 */
    [data-testid="column"] { padding-right: 20px !important; }
</style>
""", unsafe_allow_html=True)

# --- ヘッダー描画 ---
st.markdown(f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; background: white; z-index: 999; padding: 10px 25px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
        <div class="header-logo-title">US/JP MARKET WATCH</div>
        <div id="lang-trigger"></div>
    </div>
""", unsafe_allow_html=True)

with st.container():
    h_col1, h_col2 = st.columns([7, 1])
    with h_col2:
        new_lang = st.segmented_control("Lang", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
        if new_lang and new_lang != st.session_state.lang:
            st.session_state.lang = new_lang; st.rerun()

st.markdown('<div class="main-spacer"></div>', unsafe_allow_html=True)
# 指定のタイトルを大きく太く
st.markdown('<div class="main-big-title">US/Japan Stock Market<br>Real-time Calendar</div>', unsafe_allow_html=True)

# --- 価格データ取得・表示 ---
@st.cache_data(ttl=60)
def get_market_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker); hist = t.history(period="2d")
            curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
            data[name] = {"price": curr, "diff": curr - prev, "pct": ((curr - prev)/prev)*100}
        except: data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

p = get_market_prices()
m_cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c_cls, sym = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with m_cols[i]:
        st.markdown(f'<div class="indicator-box"><div class="indicator-label">{name}</div><div class="indicator-value">{d["price"]:,.1f}</div><div class="{c_cls}" style="font-size:0.75rem; font-weight:700;">{sym}{abs(d["diff"]):.1f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)

# --- 市場ステータスロジック ---
def get_next_open(now, country_code):
    cc, th = ("US", holidays.CountryHoliday("US")) if country_code == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot = time(9, 30) if country_code == "US" else time(9, 0)
    td = now.date()
    if now < datetime.combine(td, ot).replace(tzinfo=now.tzinfo) and td.weekday() < 5 and td not in th: return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)
    while True:
        td += timedelta(days=1)
        if td.weekday() < 5 and td not in th: return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)

def get_market_status_ui(now, market_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if market_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    nx = get_next_open(now, market_type); df = nx - now
    cd = f"{df.days*24 + df.seconds//3600}:{(df.seconds//60)%60:02d}:{df.seconds%60:02d}"
    if not (0 <= now.weekday() <= 4) or is_h: return f"CLOSED ({'HOLIDAY' if is_h else 'WEEKEND'})<br><small>{L['next_open']} {cd}</small>", "#f9f9f9"
    if now < ot: d = ot-now; return f"WAITING... (Opens in {d.seconds//3600:02d}:{(d.seconds//60)%60:02d})", "#fffbe6"
    elif ot <= now < ct: d = ct-now; return f"OPEN (Closes in {d.seconds//3600:02d}:{(d.seconds//60)%60:02d})", "#e6ffed"
    else: return f"CLOSED (DAY END)<br><small>{L['next_open']} {cd}</small>", "#fff1f0"

def draw_cal(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"<div style='font-weight:900; font-size:1.2rem; margin-bottom:10px;'>{view_date.strftime('%Y / %m' if st.session_state.lang == 'JP' else '%B %Y')}</div>", unsafe_allow_html=True)
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    html = f'<table class="calendar-table"><tr><th>SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0: html += '<td></td>'
            else:
                curr = date(view_date.year, view_date.month, day); h = target_holidays.get(curr)
                cls = "holiday-red" if (h or i==0 or i==6) else ""
                cnt = f'<span class="today-marker">{day}</span>' if curr == now_full.date() else str(day)
                html += f'<td><span class="{cls}">{cnt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1: 
        if st.button(L["prev"], key=f"p_{state_key}"):
            m, y = (st.session_state[state_key].month-1, st.session_state[state_key].year) if st.session_state[state_key].month > 1 else (12, st.session_state[state_key].year-1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    with b2:
        if st.button(L["today"], key=f"t_{state_key}"): st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1); st.rerun()
    with b3:
        if st.button(L["next"], key=f"n_{state_key}"):
            m, y = (st.session_state[state_key].month+1, st.session_state[state_key].year) if st.session_state[state_key].month < 12 else (1, st.session_state[state_key].year+1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()

# --- タブ表示 ---
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

tab_us, tab_jp = st.tabs([L["us_market"], L["jp_market"]])
with tab_us:
    st.markdown(f'<div style="font-size:0.9rem; font-weight:800; color:#444;">{now_ny.strftime("%Y/%m/%d %H:%M:%S")} ET</div>', unsafe_allow_html=True)
    status, color = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color}; border-left: 5px solid #333;">{status}</div>', unsafe_allow_html=True)
    draw_cal(now_ny, "US", "v_us", "America/New_York")

with tab_jp:
    st.markdown(f'<div style="font-size:0.9rem; font-weight:800; color:#444;">{now_jp.strftime("%Y/%m/%d %H:%M:%S")} JST</div>', unsafe_allow_html=True)
    status, color = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color}; border-left: 5px solid #333;">{status}</div>', unsafe_allow_html=True)
    draw_cal(now_jp, "JP", "v_jp", "Asia/Tokyo")
