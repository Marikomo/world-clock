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

# --- 2. CSS（余白を大幅に強化） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    /* 全体の余白調整 */
    .block-container {{ padding: 2rem 5rem !important; margin-top: -30px !important; }}
    
    .logo-text {{ font-size: 1.6rem; font-weight: 900; letter-spacing: -0.03em; color: #111; margin-bottom: 30px; }}
    
    /* セクション間の余白 */
    .stHorizontalBlock {{ gap: 3rem !important; }}
    
    /* 価格ボードの余白 */
    .absolute-row {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 40px; }}
    .price-box {{ border: 1px solid #eee; padding: 25px 15px; background-color: #fff; text-align: center; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }}
    .price-val {{ font-size: 1.8rem; font-weight: 900; line-height: 1.2; color: #111; margin: 8px 0; }} 

    /* ステータスラインの余白 */
    .status-line {{ font-size: 1.3rem; font-weight: 900; padding: 20px; border: 1px solid #ddd; border-left: 12px solid #111; background-color: #fff; margin-bottom: 25px; }}
    
    /* カレンダーの余白 */
    .calendar-table {{ width: 100%; border-collapse: separate; border-spacing: 0 10px; text-align: center; margin-top: 15px; }}
    .calendar-table th {{ padding-bottom: 15px; }}
    .calendar-table td {{ padding: 8px 0; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; font-weight: 800; border-radius: 6px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 6px; font-weight: 800; }}
    
    /* リストボックス内の余白 */
    .item-row {{ font-size: 0.9rem; line-height: 1.8; color: #333; border-bottom: 1px dotted #ddd; padding: 12px 0; text-align: left; }}
    .box-header {{ font-size: 1.1rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 12px; margin-bottom: 20px; }}
    
    /* コンテナ外枠の余白 */
    [data-testid="stExpander"], .st-emotion-cache-12w0qpk {{ margin-top: 20px; padding: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI発表", "2026-04-11": "🇺🇸 米 PPI発表", "2026-04-15": "🇺🇸 大手金融決算開始",
    "2026-04-27": "🇯🇵 日銀決定会合(Day 1)", "2026-04-28": "🇯🇵 日銀発表・会見",
    "2026-04-29": "🇺🇸 FOMC政策金利発表(Day 1)", "2026-04-30": "🇺🇸 FOMC金利発表",
    "2026-05-01": "🇺🇸 米 雇用統計発表", "2026-05-03": "🇯🇵 憲法記念日", "2026-05-04": "🇯🇵 みどりの日",
    "2026-05-05": "🇯🇵 こどもの日", "2026-05-20": "🇺🇸 NVIDIA 決算予定", "2026-11-03": "🇺🇸 米国中間選挙"
}
AI_NEWS_DATA = {
    "US": [f"・米国AIニュース {i+1}: NVIDIA / OpenAI の最新市場動向 {i+1}" for i in range(10)],
    "JP": [f"・日本AIニュース {i+1}: ソフトバンク / さくらネット 最新動向 {i+1}" for i in range(10)]
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
col_lang_left, col_lang_right = st.columns([8, 2])
with col_lang_right:
    new_lang = st.segmented_control("LANG", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード ---
cols_p = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with cols_p[i]:
        st.markdown(f'<div class="price-box"><div style="font-size:0.95rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:1rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# --- 6. 市場レイアウト ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2)
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.markdown(f"### {title}")
        # ステータス
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5)
        st_txt = L["open"] if is_op else L["closed"]
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} <span style="float:right; font-size:0.9rem; color:#666;">Next: 09:30</span></div>', unsafe_allow_html=True)
        
        # 時計
        dst_status = L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]
        dst_ui = f' <span style="color:#d71920; font-size:0.9rem; font-weight:900;">({dst_status})</span>' if cc == "US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.3rem; margin-bottom:20px;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")}{dst_ui}</div>', unsafe_allow_html=True)
        
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

        # ボタン
        st.markdown("<br>", unsafe_allow_html=True)
        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=state_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        # 【枠：イベント】
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:300px; overflow-y:auto;">' + ("".join(m_ev) if m_ev else '<div class="item-row">なし</div>') + '</div>', unsafe_allow_html=True)

        # 【枠：ニュース】
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:300px; overflow-y:auto;">' + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
