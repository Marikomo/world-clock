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
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶", "news_title": "🚀 今週のAI株式ニュース", "event_title": "📅 注目の株式イベント"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY",
        "next": "Next Open in: ", "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶", "news_title": "🚀 Weekly AI Stock News", "event_title": "📅 Market Events"
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
        visibility: hidden; width: 280px; background-color: rgba(17, 17, 17, 0.98); color: #fff;
        text-align: left; border-radius: 8px; padding: 15px; position: absolute;
        z-index: 9999 !important; bottom: 105%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.3s ease-in-out; font-size: 0.85rem; line-height: 1.5; pointer-events: none;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3); border: 1px solid #444;
    }}
    .hover-tip:hover .hover-text {{ visibility: visible; opacity: 1; transition-delay: 0.6s; }}
    .status-line {{ font-size: 1.2rem; font-weight: 900; padding: 12px; border: 1px solid #ddd; border-left: 8px solid #111; background-color: #fff; margin-bottom: 10px; }}
    .status-next {{ font-size: 0.8rem; color: #666; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; text-align: center; margin-top: 10px; }}
    .calendar-table th {{ font-size: 0.8rem; color: #888; padding-bottom: 5px; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; }}
    .holiday-red {{ color: #d71920; font-weight: 800; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; cursor: help; }}
    .list-box {{ background: #fdfdfd; border: 1px solid #eee; padding: 12px; margin-top: 15px; border-radius: 4px; }}
    .list-title {{ font-size: 0.95rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 4px; margin-bottom: 8px; }}
    .list-item {{ font-size: 0.85rem; line-height: 1.6; color: #333; margin-bottom: 4px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. コンテンツデータ ---
AI_NEWS = {
    "US": ["・NVIDIA: 次世代Blackwellチップの需要が供給を大幅超過", "・OpenAI: 「GPT-5」開発に向けた数兆円規模の投資を準備", "・Microsoft: AIインフラへの投資を倍増、株価反発"],
    "JP": ["・ソフトバンクG: AI革命に向け英Arm株を担保に巨額資金確保", "・サクラエディタ/さくらネット: 政府支援によるAIスパコン増強完了", "・日本企業: 生成AI導入率が前年比2倍、業務効率化が顕著"]
}
EVENTS = {
    "2026-11-03": "🇺🇸 アメリカ中間選挙 (全議席改選)",
    "2026-05-03": "🇯🇵 憲法記念日 (市場休場)",
    "2026-05-04": "🇯🇵 みどりの日 (市場休場)",
    "2026-05-05": "🇯🇵 こどもの日 (市場休場)",
    "2026-04-15": "🇺🇸 大手テック企業決算発表ピーク開始",
    "2026-04-20": "🇯🇵 日銀金融政策決定会合 議事要旨発表"
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
col_h1, col_h2 = st.columns([7, 3])
with col_h1: st.markdown('<div style="font-size: 1.2rem; font-weight: 900; padding: 10px 0;">Market Analytics Dashboard</div>', unsafe_allow_html=True)
with col_h2:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード（ホバーでUS/JP両方のニュースを表示） ---
p_html = '<div class="absolute-row">'
news_combined = "<br>".join(AI_NEWS["US"] + AI_NEWS["JP"])
for name, d in prices.items():
    c_cls = "color: #d71920;" if d['diff'] >= 0 else "color: #0050b3;"
    p_html += f'''
    <div class="hover-tip">
        <div class="price-box">
            <div class="price-label">{name}</div>
            <div class="price-val">{d["val"]:,.1f}</div>
            <div style="{c_cls} font-size:0.8rem; font-weight:800;">{"▲" if d['diff'] >= 0 else "▼"}{abs(d["diff"]):.1f}</div>
        </div>
        <span class="hover-text"><b style="color:#FFD700;">{L['news_title']}</b><br><br>{news_combined}</span>
    </div>'''
st.markdown(p_html + '</div>', unsafe_allow_html=True)

# --- 6. 市場ステータスとカレンダー ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

def get_market_info(now, m_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if m_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot, ct = (time(9, 30), time(16, 0)) if m_type == "US" else (time(9, 0), time(15, 0))
    td = now.date()
    is_open = (ot <= now.time() < ct and td.weekday() < 5 and td not in th)
    st_text = L["open"] if is_open else (L["holiday"] if (td.weekday() >= 5 or td in th) else L["closed"])
    bg = "#e6ffed" if st_text == L["open"] else ("#f9f9f9" if st_text == L["holiday"] else "#fff1f0")
    nx = td
    if now.time() >= ct or td.weekday() >= 5 or td in th:
        while True:
            nx += timedelta(days=1)
            if nx.weekday() < 5 and nx not in th: break
    target_dt = datetime.combine(nx, ot)
    if m_type == "US": target_dt = pytz.timezone('America/New_York').localize(target_dt)
    else: target_dt = pytz.timezone('Asia/Tokyo').localize(target_dt)
    diff = target_dt - now
    h, r = divmod(int(diff.total_seconds()), 3600); m, _ = divmod(r, 60)
    countdown = f"{L['next']} {h}h {m}m" if not is_open else ""
    return f'<div class="status-line" style="background-color: {bg};"><div style="display:flex; justify-content:space-between; align-items:center;"><span>{st_text}</span><span class="status-next">{countdown}</span></div></div>'

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        st.markdown(get_market_info(now, cc), unsafe_allow_html=True)
        dst = f' <span style="color:#d71920; font-size:0.75rem;">DST ON</span>' if now.dst() != timedelta(0) else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem; margin-top:5px;">{now.strftime("%H:%M:%S")}{dst if cc=="US" else ""} <span style="font-size:0.8rem; color:#666;">({now.strftime("%Y/%m/%d")})</span></div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        th = holidays.CountryHoliday(cc, years=view.year)
        cal = calendar.monthcalendar(view.year, view.month)
        html = f'<table class="calendar-table"><tr><th>{L["sun"]}</th><th>{L["mon"]}</th><th>{L["tue"]}</th><th>{L["wed"]}</th><th>{L["thu"]}</th><th>{L["fri"]}</th><th>{L["sat"]}</th></tr>'
        for w in cal:
            html += '<tr>'
            for i, d in enumerate(w):
                if d == 0: html += '<td></td>'
                else:
                    curr = date(view.year, view.month, d)
                    ev_txt = EVENTS.get(curr.strftime("%Y-%m-%d"), "")
                    cls = "holiday-red" if (i==0 or i==6 or curr in th) else ""
                    day_html = f'<span class="today-marker">{d}</span>' if curr == now.date() else str(d)
                    if ev_txt:
                        html += f'<td><div class="hover-tip"><span class="{cls} event-mark">{day_html}</span><span class="hover-text"><b style="color:#FFD700;">{L["event_title"]}</b><br>{ev_txt}</span></div></td>'
                    else: html += f'<td><span class="{cls}">{day_html}</span></td>'
            html += '</tr>'
        st.markdown(html + '</table>', unsafe_allow_html=True)
        
        # カレンダー下：イベント一覧表示
        ev_list = [f'<div class="list-item">{k[5:]:k[10:]}: {v}</div>' for k, v in EVENTS.items() if (cc == "US" and "🇺🇸" in v) or (cc == "JP" and "🇯🇵" in v)]
        if ev_list:
            st.markdown(f'<div class="list-box"><div class="list-title">{L["event_title"]}</div>{"".join(ev_list)}</div>', unsafe_allow_html=True)

        # カレンダー下：AIニュース一覧表示
        news_list = [f'<div class="list-item">{n}</div>' for n in AI_NEWS[cc]]
        st.markdown(f'<div class="list-box"><div class="list-title">{L["news_title"]}</div>{"".join(news_list)}</div>', unsafe_allow_html=True)
        
        # ボタン
        bc = st.columns(3)
        with bc[0]: 
            if st.button(L["prev"], key=f"p_{suffix}"):
                m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1)
                st.session_state[state_key] = date(y, m, 1); st.rerun()
        with bc[1]:
            if st.button(L["today"], key=f"t_{suffix}"): st.session_state[state_key] = now.date().replace(day=1); st.rerun()
        with bc[2]:
            if st.button(L["next_m"], key=f"n_{suffix}"):
                m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1)
                st.session_state[state_key] = date(y, m, 1); st.rerun()
