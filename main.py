import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. 基本設定 ---
if 'lang' not in st.session_state: st.session_state.lang = "JP"
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Market Watch", layout="wide")

L_MAP = {
    "JP": {
        "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場", "open": "開場中", "closed": "閉場中", "holiday": "休場",
        "next": "次回の開場まで: ", "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶", "news": "📢 AI News", "event": "📅 Events"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY",
        "next": "Next Open in: ", "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶", "news": "📢 AI News", "event": "📅 Events"
    }
}
L = L_MAP[st.session_state.lang]

# --- 2. CSS ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}

    .absolute-row {{ display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }}
    .hover-tip {{ position: relative; flex: 1; }}
    .price-box {{ border: 1px solid #ddd; padding: 12px 2px; background-color: #fff; text-align: center; cursor: help; }}
    .price-label {{ font-size: 0.85rem; color: #666; font-weight: 700; }}
    .price-val {{ font-size: 1.6rem; font-weight: 900; line-height: 1.1; color: #111; }} 
    
    .hover-text {{
        visibility: hidden; width: 260px; background-color: rgba(17, 17, 17, 0.95); color: #fff;
        text-align: left; border-radius: 8px; padding: 15px; position: absolute;
        z-index: 9999 !important; bottom: 105%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.3s ease-in-out; font-size: 0.85rem; line-height: 1.5; pointer-events: none;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}
    .hover-tip:hover .hover-text {{ visibility: visible; opacity: 1; transition-delay: 0.6s; }}

    .status-line {{
        font-size: 1.25rem; font-weight: 900; padding: 12px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; display: flex; 
        flex-direction: column; gap: 2px; margin-bottom: 10px;
    }}
    .status-next {{ font-size: 0.8rem; color: #666; font-weight: 700; }}
    .cal-dst {{ font-size: 0.75rem; font-weight: 700; color: #d71920; margin-left: 10px; }}

    .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; text-align: center; margin-top: 10px; }}
    .calendar-table th {{ font-size: 0.8rem; padding-bottom: 5px; color: #888; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; }}
    .holiday-red {{ color: #d71920; font-weight: 800; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; cursor: help; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
AI_NEWS_HTML = "<br>・OpenAI: GPT-5 開発進捗発表<br>・NVIDIA: 株価最高値圏維持<br>・Google: Gemini機能強化"
EVENTS = {"2026-11-03": "🇺🇸 アメリカ中間選挙", "2026-05-03": "🇯🇵 憲法記念日", "2026-05-04": "🇯🇵 みどりの日", "2026-05-05": "🇯🇵 こどもの日"}

@st.cache_data(ttl=60)
def get_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
            res[k] = {"val": c, "diff": c - p}
        except: res[k] = {"val": 0, "diff": 0}
    return res
prices = get_prices()

# --- 4. 市場ステータス計算 ---
def get_market_info(now, m_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if m_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot, ct = (time(9, 30), time(16, 0)) if m_type == "US" else (time(9, 0), time(15, 0))
    td = now.date()
    
    is_open = (ot <= now.time() < ct and td.weekday() < 5 and td not in th)
    st_text = L["open"] if is_open else (L["holiday"] if (td.weekday() >= 5 or td in th) else L["closed"])
    bg = "#e6ffed" if st_text == L["open"] else ("#f9f9f9" if st_text == L["holiday"] else "#fff1f0")
    
    # 次の開場までのカウントダウン
    nx = td
    if now.time() >= ct or td.weekday() >= 5 or td in th:
        while True:
            nx += timedelta(days=1)
            if nx.weekday() < 5 and nx not in th: break
    
    target_dt = datetime.combine(nx, ot)
    if m_type == "US": target_dt = pytz.timezone('America/New_York').localize(target_dt)
    else: target_dt = pytz.timezone('Asia/Tokyo').localize(target_dt)
    
    diff = target_dt - now
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    
    countdown = f"{L['next']} {hours}h {minutes}m" if not is_open else ""
    
    return f'''
    <div class="status-line" style="background-color: {bg};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>{st_text}</span>
            <span class="status-next">{countdown}</span>
        </div>
    </div>'''

# --- 5. レイアウト表示 ---
col_h1, col_h2 = st.columns([7, 3])
with col_h1: st.markdown('<div style="font-size: 1.2rem; font-weight: 900; padding: 10px 0;">Market Dashboard</div>', unsafe_allow_html=True)
with col_h2:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# 価格ボード
p_html = '<div class="absolute-row">'
for name, d in prices.items():
    c_cls = "color: #d71920;" if d['diff'] >= 0 else "color: #0050b3;"
    p_html += f'''
    <div class="hover-tip">
        <div class="price-box">
            <div class="price-label">{name}</div>
            <div class="price-val">{d["val"]:,.1f}</div>
            <div style="{c_cls} font-size:0.8rem; font-weight:800;">{"▲" if d['diff'] >= 0 else "▼"}{abs(d["diff"]):.1f}</div>
        </div>
        <span class="hover-text"><b style="color:#FFD700;">{L['news']}</b><br>{AI_NEWS_HTML}</span>
    </div>'''
st.markdown(p_html + '</div>', unsafe_allow_html=True)

# メイン表示
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        st.markdown(get_market_info(now, cc), unsafe_allow_html=True)
        
        # 時計とサマータイム
        dst_label = f'<span class="cal-dst">DST ON (サマータイム中)</span>' if now.dst() != timedelta(0) else '<span class="cal-dst" style="color:#666;">DST OFF</span>
