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
st.set_page_config(page_title="Market Real-time Dashboard", layout="wide")

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next": "次回の開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "📅 注目の株式イベント",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "📅 Key Market Events",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. CSS ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}
    .absolute-row {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }}
    .price-box {{ border: 1px solid #ddd; padding: 15px 5px; background-color: #fff; text-align: center; flex: 1; border-radius: 4px; cursor: pointer; }}
    .price-val {{ font-size: 1.7rem; font-weight: 900; line-height: 1.1; color: #111; }} 
    .status-line {{ font-size: 1.3rem; font-weight: 900; padding: 15px; border: 1px solid #ddd; border-left: 10px solid #111; background-color: #fff; margin-bottom: 12px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; font-size: 1rem; margin-top: 10px; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 5px; font-weight: 800; cursor: pointer; }}
    
    .list-wrapper {{ 
        border: 1px solid #eee; padding: 18px; margin-top: 15px; 
        border-radius: 8px; background-color: #fdfdfd; height: 380px; 
        overflow-y: auto; text-align: left;
    }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 10px; margin-bottom: 15px; color: #111; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #333; margin-bottom: 10px; border-bottom: 1px dotted #ccc; padding-bottom: 6px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI(消費者物価指数)発表", "2026-04-11": "🇺🇸 米 PPI(生産者物価指数)発表",
    "2026-04-15": "🇺🇸 米 金融大手決算開始(JPM/WFC)", "2026-04-27": "🇯🇵 日銀決定会合(Day1)",
    "2026-04-28": "🇯🇵 日銀結果発表・総裁会見", "2026-04-29": "🇺🇸 FOMC政策金利発表(Day1)",
    "2026-04-30": "🇺🇸 FOMC金利発表・パウエル会見", "2026-05-01": "🇺🇸 米 雇用統計発表",
    "2026-05-03": "🇯🇵 憲法記念日(休場)", "2026-05-04": "🇯🇵 みどりの日(休場)",
    "2026-05-05": "🇯🇵 こどもの日(休場)", "2026-05-20": "🇺🇸 NVIDIA 決算発表予定",
    "2026-11-03": "🇺🇸 米国中間選挙 投開票日"
}
AI_NEWS_DATA = {
    "US": [f"{i+1}. NVIDIA/MSFT 等 米国AI株式ニュース {i+1}" for i in range(10)],
    "JP": [f"{i+1}. SBG/さくらネット 等 日本AI株式ニュース {i+1}" for i in range(10)]
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
st.markdown('<div class="absolute-row">' + "".join([f'<div class="price-box"><div style="font-size:0.85rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.9rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>' for k,v in prices.items()]) + '</div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} <span style="float:right; font-size:0.85rem; color:#666; font-weight:700;">{L["next"]} 09:30</span></div>', unsafe_allow_html=True)
        dst = f' <span style="color:#d71920; font-size:0.8rem; font-weight:900;">DST ON (サマータイム中)</span>' if now.dst() != timedelta(0) else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.2rem; margin-bottom:10px;">{now.strftime("%H:%M:%S")}{dst if cc=="US" else ""} <span style="font-size:0.9rem; color:#666;">({now.strftime("%Y/%m/%d")})</span></div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th style="color:{"#d71920" if i==0 or i==6 else "#888"};">{d}</th>' for i, d in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]])]) + '</tr>'
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

        # 操作ボタン
        bc = st.columns(3)
        with bc[0]: 
            if st.button(L["prev"], key=f"p_{suffix}"):
                m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1); st.session_state[state_key] = date(y, m, 1); st.rerun()
        with bc[1]:
            if st.button(L["today"], key=f"t_{suffix}"): st.session_state[state_key] = now.date().replace(day=1); st.rerun()
        with bc[2]:
            if st.button(L["next_m"], key=f"n_{suffix}"):
                m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1); st.session_state[state_key] = date(y, m, 1); st.rerun()

        # 【連動】イベントリスト
        st.markdown(f'<div class="list-wrapper"><div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
        m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and ((cc=="US" and "🇺🇸" in v) or (cc=="JP" and "🇯🇵" in v))]
        if m_ev: st.markdown("".join(m_ev), unsafe_allow_html=True)
        else: st.markdown('<div class="item-row">特になし</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ニュースリスト
        st.markdown(f'<div class="list-wrapper"><div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
        st.markdown("".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
