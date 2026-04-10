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
st.set_page_config(page_title="Market Analytics Dashboard", layout="wide")

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next": "次回の開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Market Events",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. CSS ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; letter-spacing: -0.03em; color: #111; margin-bottom: 20px; }}
    .price-box {{ border: 1px solid #ddd; padding: 15px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .price-val {{ font-size: 1.7rem; font-weight: 900; line-height: 1.1; color: #111; }} 
    .status-line {{ font-size: 1.25rem; font-weight: 900; padding: 12px; border: 1px solid #ddd; border-left: 10px solid #111; background-color: #fff; margin-bottom: 10px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 5px; font-weight: 800; cursor: pointer; }}
    /* リストボックス用 */
    .st-box {{ border: 1px solid #eee; padding: 15px; border-radius: 8px; background-color: #fdfdfd; height: 350px; overflow-y: auto; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #333; border-bottom: 1px dotted #ccc; padding: 6px 0; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI発表", "2026-04-11": "🇺🇸 米 PPI発表", "2026-04-15": "🇺🇸 大手金融決算開始",
    "2026-04-27": "🇯🇵 日銀決定会合(Day1)", "2026-04-28": "🇯🇵 日銀発表・会見",
    "2026-04-29": "🇺🇸 FOMC発表(Day1)", "2026-04-30": "🇺🇸 FOMC金利発表",
    "2026-05-01": "🇺🇸 米 雇用統計発表", "2026-05-03": "🇯🇵 憲法記念日", "2026-05-04": "🇯🇵 みどりの日",
    "2026-05-05": "🇯🇵 こどもの日", "2026-05-20": "🇺🇸 NVIDIA 決算予定", "2026-11-03": "🇺🇸 米 中間選挙"
}
AI_NEWS_DATA = {
    "US": [f"・米国ニュース {i+1}: NVIDIA/OpenAI 最新動向 {i+1}" for i in range(10)],
    "JP": [f"・日本ニュース {i+1}: SBG/さくら 最新AI動向 {i+1}" for i in range(10)]
}

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

# --- 4. ヘッダー ---
col_logo, col_lang = st.columns([7, 3])
with col_logo: st.markdown(f'<div class="logo-text">{L["logo"]}</div>', unsafe_allow_html=True)
with col_lang:
    new_lang = st.segmented_control("LANG", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード ---
cols_p = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with cols_p[i]:
        st.markdown(f'<div class="price-box"><div style="font-size:0.85rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# --- 6. 市場レイアウト ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        # ステータス
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5)
        st_txt = L["open"] if is_op else L["closed"]
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} <span style="float:right; font-size:0.8rem; color:#666;">Next: 09:30</span></div>', unsafe_allow_html=True)
        dst = f' <span style="color:#d71920; font-size:0.8rem;">DST ON</span>' if now.dst() != timedelta(0) else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem;">{now.strftime("%H:%M:%S")}{dst if cc=="US" else ""} ({now.strftime("%Y/%m/%d")})</div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th style="color:{"#d71920" if i==0 or i==6 else "#888"}; font-size:0.8rem;">{d}</th>' for i, d in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]])]) + '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    ev = EVENTS_DATA.get(curr_d.strftime("%Y-%m-%d"), "")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{"#d71920" if i==0 or i==6 else "#111"};" title="{ev}">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        # カレンダー操作ボタン
        bc = st.columns(3)
        with bc[0]: 
            if st.button(L["prev"], key=f"p_{suffix}"):
                m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1); st.session_state[state_key] = date(y, m, 1); st.rerun()
        with bc[1]:
            if st.button(L["today"], key=f"t_{suffix}"): st.session_state[state_key] = now.date().replace(day=1); st.rerun()
        with bc[2]:
            if st.button(L["next_m"], key=f"n_{suffix}"):
                m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1); st.session_state[state_key] = date(y, m, 1); st.rerun()

        # 【枠：イベント】
        st.subheader(f"{view.month}月 {L['event_title']}")
        with st.container(border=True):
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and ((cc=="US" and "🇺🇸" in v) or (cc=="JP" and "🇯🇵" in v))]
            if m_ev: st.markdown('<div style="height:250px; overflow-y:auto;">' + "".join(m_ev) + '</div>', unsafe_allow_html=True)
            else: st.write("今月の重要イベントはありません")

        # 【枠：ニュース】
        st.subheader(L["news_title"])
        with st.container(border=True):
            st.markdown('<div style="height:250px; overflow-y:auto;">' + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
