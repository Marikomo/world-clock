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
st.set_page_config(page_title="Market Analytics", layout="wide")

L_MAP = {
    "JP": {
        "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場", "open": "開場中", "closed": "閉場中", "holiday": "休場",
        "next": "次回の開場まで: ", "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶", "news_title": "🚀 今週のAI株式ニュース(10)", "event_title": "📅 注目の株式イベント"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY",
        "next": "Next Open in: ", "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶", "news_title": "🚀 Weekly AI News (10)", "event_title": "📅 Monthly Events"
    }
}
L = L_MAP[st.session_state.lang]

# --- 2. 究極のCSS（ロゴ、枠、スクロールを完全固定） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}
    
    /* ヘッダー・ロゴ */
    .header-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 15px; }}
    .logo-text {{ font-size: 1.2rem; font-weight: 900; letter-spacing: -0.02em; color: #111; }}

    /* 価格ボード */
    .absolute-row {{ display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }}
    .price-box {{ border: 1px solid #ddd; padding: 12px 2px; background-color: #fff; text-align: center; flex: 1; }}
    .price-val {{ font-size: 1.6rem; font-weight: 900; line-height: 1.1; color: #111; }} 

    /* ホバーテキスト（最前面固定） */
    .hover-tip {{ position: relative; cursor: pointer; }}
    .hover-text {{
        visibility: hidden; width: 280px; background-color: rgba(17, 17, 17, 0.98); color: #fff;
        text-align: left; border-radius: 8px; padding: 15px; position: absolute;
        z-index: 9999 !important; bottom: 105%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.3s; font-size: 0.85rem; pointer-events: none;
    }}
    .hover-tip:hover .hover-text {{ visibility: visible; opacity: 1; }}

    /* ステータスとカレンダー */
    .status-line {{ font-size: 1.2rem; font-weight: 900; padding: 12px; border: 1px solid #ddd; border-left: 8px solid #111; background-color: #fff; margin-bottom: 10px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; }}
    
    /* リストボックス（確実な表示とスクロール） */
    .list-wrapper {{ 
        border: 1px solid #eee; padding: 15px; margin-top: 15px; 
        border-radius: 6px; background-color: #fdfdfd; height: 350px; 
        overflow-y: auto; display: block !important;
    }}
    .box-header {{ font-size: 1rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 8px; margin-bottom: 12px; }}
    .item-row {{ font-size: 0.82rem; line-height: 1.6; color: #333; margin-bottom: 8px; border-bottom: 1px dotted #ccc; padding-bottom: 4px; text-align: left; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI発表", "2026-04-11": "🇺🇸 米 PPI発表", "2026-04-28": "🇯🇵 日銀結果発表",
    "2026-04-30": "🇺🇸 FOMC金利発表", "2026-05-01": "🇺🇸 米 雇用統計", "2026-05-03": "🇯🇵 憲法記念日",
    "2026-05-04": "🇯🇵 みどりの日", "2026-05-05": "🇯🇵 こどもの日", "2026-11-03": "🇺🇸 米 中間選挙"
}
AI_NEWS_DATA = {
    "US": [f"{i+1}. NVIDIA/OpenAI等 最新AIニュース {i+1}" for i in range(10)],
    "JP": [f"{i+1}. SBG/さくら等 国内AIニュース {i+1}" for i in range(10)]
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

# --- 4. ヘッダー（ロゴと言語スイッチ） ---
col_logo, col_lang = st.columns([7, 3])
with col_logo:
    st.markdown('<div class="logo-text">STOCK MARKET REAL-TIME</div>', unsafe_allow_html=True)
with col_lang:
    new_lang = st.segmented_control("LANG", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード ---
st.markdown('<div class="absolute-row">' + "".join([f'<div class="price-box"><div class="price-label">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>' for k,v in prices.items()]) + '</div>', unsafe_allow_html=True)

# --- 6. レイアウト ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        # 市場ステータス
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5)
        st_txt = L["open"] if is_op else L["closed"]
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} <span style="float:right; font-size:0.8rem; color:#666;">Next: 09:30</span></div>', unsafe_allow_html=True)
        
        # 時計
        dst = f' <span style="color:#d71920; font-size:0.75rem;">DST ON</span>' if now.dst() != timedelta(0) else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem;">{now.strftime("%H:%M:%S")}{dst if cc=="US" else ""} <span style="font-size:0.8rem; color:#666;">({now.strftime("%Y/%m/%d")})</span></div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th>{d}</th>' for d in [L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]]) + '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    curr_s = curr_d.strftime("%Y-%m-%d")
                    ev = EVENTS_DATA.get(curr_s, "")
                    cls = "holiday-red" if (i==0 or i==6) else ""
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    if ev: h += f'<td><div class="hover-tip"><span class="{cls} event-mark">{day_ui}</span><span class="hover-text"><b>{L["event_title"]}</b><br>{ev}</span></div></td>'
                    else: h += f'<td><span class="{cls}">{day_ui}</span></td>'
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

        # イベントリスト（月連動）
        ev_html = f'<div class="list-wrapper"><div class="box-header">{view.month}月 {L["event_title"]}</div>'
        m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and ((cc=="US" and "🇺🇸" in v) or (cc=="JP" and "🇯🇵" in v))]
        st.markdown(ev_html + ("".join(m_ev) if m_ev else '<div class="item-row">なし</div>') + '</div>', unsafe_allow_html=True)

        # ニュースリスト（10件）
        news_html = f'<div class="list-wrapper"><div class="box-header">{L["news_title"]}</div>'
        st.markdown(news_html + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
