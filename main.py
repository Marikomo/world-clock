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
st.set_page_config(page_title="Market Dashboard", layout="wide")

us_holidays = holidays.US()
jp_holidays = holidays.Japan()

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next_prefix": "次回開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "dst_on": "サマータイム中", "dst_off": "通常時間",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next_prefix": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Market Events",
        "dst_on": "Daylight Saving Time", "dst_off": "Standard Time",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. CSS (ヘッダー固定・言語切替カスタマイズ) ---
st.markdown(f"""
<style>
    /* 全体背景と文字色 */
    .stApp, .block-container {{ background-color: #ffffff !important; color: #000000 !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    
    /* ロゴヘッダーの固定(Sticky) */
    .header-sticky {{
        position: fixed; top: 0; left: 0; width: 100%; background: #ffffff;
        z-index: 9999; padding: 15px 40px; border-bottom: 2px solid #000000;
        display: flex; justify-content: space-between; align-items: center;
    }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; }}
    .block-container {{ padding-top: 5rem !important; }}

    /* 価格ボード */
    .price-box {{ border: 1px solid #cccccc; padding: 15px 5px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background-color: #fff; margin-bottom: 15px; }}
    
    /* カレンダー枠と線 */
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; border: 1px solid #cccccc; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #ff4b4b; text-underline-offset: 4px; }}
    
    /* ボタン: 白背景、黒文字、グレー枠 */
    div.stButton > button {{
        background-color: #ffffff !important; color: #000000 !important;
        border: 1px solid #cccccc !important; width: 100%; border-radius: 4px;
    }}

    /* ニュース・イベント枠 */
    [data-testid="stVerticalBlockBorderWrapper"] {{ border: 1px solid #cccccc !important; padding: 10px; border-radius: 8px; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}

    /* 言語切り替えスイッチの見た目調整 */
    div[data-testid="stSegmentedControl"] button {{
        border: 1px solid #cccccc !important; color: #999999 !important; background-color: #ffffff !important;
    }}
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {{
        background-color: #000000 !important; color: #ffffff !important; border-color: #000000 !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. ロジック (時刻・カウントダウン) ---
t_ny = pytz.timezone('America/New_York')
t_jp = pytz.timezone('Asia/Tokyo')
n_ny = datetime.now(t_ny)
n_jp = datetime.now(t_jp)

def get_countdown(now, cc):
    ot = time(9, 30) if cc == "US" else time(9, 0)
    h_list = us_holidays if cc == "US" else jp_holidays
    target = datetime.combine(now.date(), ot).replace(tzinfo=now.tzinfo)
    if now >= target or now.date() in h_list or now.weekday() >= 5:
        while True:
            target += timedelta(days=1)
            if target.weekday() < 5 and target.date() not in h_list: break
    d = target - now
    h, r = divmod(d.seconds, 3600); m, _ = divmod(r, 60)
    return f"あと{d.days}日 {h:02d}:{m:02d}" if d.days > 0 else f"あと{h}時間{m}分"

# --- 4. ヘッダー (固定) ---
st.markdown(f"""
<div class="header-sticky">
    <div class="logo-text">{L["logo"]}</div>
</div>
""", unsafe_allow_html=True)

# 言語スイッチ (ヘッダーの右側に配置するため空カラム利用)
_, col_lang = st.columns([8, 2])
with col_lang:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

# --- 5. メイン表示 ---
@st.cache_data(ttl=60)
def get_prices():
    tickers = {"S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X"}
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            res[k] = {"val": h['Close'].iloc[-1], "diff": h['Close'].iloc[-1] - h['Close'].iloc[-2]}
        except: res[k] = {"val": 0, "diff": 0}
    return res
prices = get_prices()

p_cols = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with p_cols[i]:
        st.markdown(f'<div class="price-box"><div style="font-size:0.75rem; color:#666;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.8rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="medium")
for col, now, cc, s_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        h_list = us_holidays if cc=="US" else jp_holidays
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        
        st_info = "" if is_op else f'<span style="float:right; font-size:0.75rem; color:#666;">{L["next_prefix"]}{get_countdown(now, cc)}</span>'
        st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op else "#fff5f5"};">{L["open"] if is_op else L["closed"]} {st_info}</div>', unsafe_allow_html=True)
        
        # 表示順: 日付 時間 サマータイム
        dst_txt = (L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]) if cc=="US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem; margin-bottom:10px;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")} <span style="color:#d71920;">{dst_txt}</span></div>', unsafe_allow_html=True)
        
        # カレンダー描画
        view = st.session_state[s_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>'
        for i, d in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
            color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
            h += f'<th style="color:{color} !important; font-size:0.75rem;">{d}</th>'
        h += '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    day_color = "#d71920" if (i==0 or curr_d in h_list) else ("#0050b3" if i==6 else "#000")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    ev = {"2026-04-10":"米CPI", "2026-04-30":"FOMC"}.get(curr_d.strftime("%Y-%m-%d"), "")
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{day_color} !important;">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=s_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            # 月間連動フィルタ
            ev_list = ["・4/10 米CPI発表", "・4/15 大手金融決算", "・4/30 FOMC金利発表"]
            st.markdown('<div style="height:150px; overflow-y:auto;">' + "".join([f'<div class="item-row">{e}</div>' for e in ev_list]) + '</div>', unsafe_allow_html=True)
