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
        "dst_on": "サマータイム中", "dst_off": "通常時間",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Market Events",
        "dst_on": "Daylight Saving Time", "dst_off": "Standard Time",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. CSS（崩れを直し、程よい余白を維持） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    /* 全体のパディングを標準より少し広めに設定 */
    .block-container {{ padding: 2rem 3rem !important; margin-top: -65px !important; }}
    
    .logo-text {{ font-size: 1.5rem; font-weight: 900; letter-spacing: -0.03em; color: #111; margin-bottom: 20px; border-bottom: 2px solid #111; padding-bottom: 10px; }}
    
    /* 価格ボードの余白 */
    .price-box {{ border: 1px solid #ddd; padding: 20px 10px; background-color: #fff; text-align: center; border-radius: 8px; }}
    .price-val {{ font-size: 1.7rem; font-weight: 900; line-height: 1.1; color: #111; margin: 5px 0; }} 

    /* ステータスライン */
    .status-line {{ font-size: 1.25rem; font-weight: 900; padding: 15px; border: 1px solid #ddd; border-left: 10px solid #111; background-color: #fff; margin-bottom: 20px; }}
    
    /* カレンダー（セルの高さを出して余裕を持たせる） */
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px; table-layout: fixed; }}
    .calendar-table th {{ padding-bottom: 10px; color: #888; font-size: 0.85rem; }}
    .calendar-table td {{ padding: 12px 0; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 5px; font-weight: 800; }}
    
    /* リストボックス（高さと余白のバランス） */
    .item-row {{ font-size: 0.9rem; line-height: 1.7; color: #333; border-bottom: 1px dotted #ccc; padding: 10px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 10px; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI(消費者物価指数)", "2026-04-11": "🇺🇸 米 PPI(生産者物価指数)", "2026-04-15": "🇺🇸 大手金融機関 決算発表開始",
    "2026-04-27": "🇯🇵 日銀決定会合(Day 1)", "2026-04-28": "🇯🇵 日銀発表・植田総裁会見",
    "2026-04-29": "🇺🇸 FOMC政策金利発表(Day 1)", "2026-04-30": "🇺🇸 FOMC金利発表・会見",
    "2026-05-01": "🇺🇸 米 雇用統計発表", "2026-05-03": "🇯🇵 憲法記念日(休場)", "2026-05-04": "🇯🇵 みどりの日(休場)",
    "2026-05-05": "🇯🇵 こどもの日(休場)", "2026-05-20": "🇺🇸 NVIDIA 決算発表(推定)", "2026-11-03": "🇺🇸 米国中間選挙 投開票"
}
AI_NEWS_DATA = {
    "US": [f"{i+1}. 米国AIニュース: 市場牽引銘柄の最新動向 {i+1}" for i in range(10)],
    "JP": [f"{i+1}. 日本AIニュース: 国内テック企業のAI戦略 {i+1}" for i in range(10)]
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
st.markdown(f'<div class="logo-text">{L["logo"]}</div>', unsafe_allow_html=True)
col_l, col_r = st.columns([8, 2])
with col_r:
    new_lang = st.segmented_control("LANG", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード ---
cols_p = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with cols_p[i]:
        st.markdown(f'<div class="price-box"><div style="font-size:0.85rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

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
        
        # 時計：日付、時間、サマータイム表記
        dst_status = L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]
        dst_ui = f' <span style="color:#d71920; font-size:0.85rem; font-weight:900;">({dst_status})</span>' if cc == "US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.25rem; margin-bottom:15px;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")}{dst_ui}</div>', unsafe_allow_html=True)
        
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
                    ev = EVENTS_DATA.get(curr_d.strftime("%Y-%m-%d"), "")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{"#d71920" if i==0 or i==6 else "#111"};" title="{ev}">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        # ボタン
        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=state_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        # 【連動：株式イベント】
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:280px; overflow-y:auto;">' + ("".join(m_ev) if m_ev else '<div class="item-row">なし</div>') + '</div>', unsafe_allow_html=True)

        # 【固定：今週のAIニュース】
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:280px; overflow-y:auto;">' + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
