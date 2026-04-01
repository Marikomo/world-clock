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

T = {
    "JP": {
        "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場", "next": "次回の開場: ",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "open": "開場中", "closed": "閉場中", "holiday": "休場", "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "next": "Next Open: ",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY", "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶"
    }
}
L = T[st.session_state.lang]

# --- 2. 究極のCSS（何があっても一行を死守する命令） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}

    /* 強制一行化のための共通クラス */
    .absolute-row {{
        display: flex !important; flex-direction: row !important;
        justify-content: space-between !important; align-items: center !important;
        width: 100% !important; gap: 8px !important; margin-bottom: 15px;
    }}
    .flex-item {{ flex: 1 !important; text-align: center; }}

    /* ヘッダー */
    .header-logo-title {{ font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 900; color: #111; letter-spacing: -0.04em; }}

    /* 価格ボード */
    .price-box {{ border: 1px solid #ddd; padding: 8px 2px; background-color: #fff; }}
    .price-label {{ font-size: 0.65rem; color: #666; font-weight: 700; }}
    .price-val {{ font-size: 0.95rem; font-weight: 900; }}

    /* 市場ステータス */
    .status-line {{
        font-size: 1.35rem; font-weight: 900; padding: 12px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
    }}
    .status-next {{ font-size: 0.85rem; color: #666; font-weight: 700; }}

    /* 日付・時計（フォント統一・背景なし） */
    .cal-header {{ font-family: 'Inter', sans-serif; display: flex; align-items: baseline; gap: 8px; margin-bottom: 5px; flex-wrap: nowrap; }}
    .cal-date, .cal-time {{ font-weight: 900; font-size: 1.1rem; color: #111; }}
    .cal-dst {{ font-size: 0.75rem; font-weight: 700; color: #666; }}

    /* ボタン（強制一行化） */
    .btn-row {{ display: flex !important; width: 100% !important; gap: 5px !important; margin-top: 5px; }}
    .btn-row > div {{ flex: 1 !important; }}
    .stButton > button {{
        border-radius: 0px !important; border: 1px solid #ccc !important;
        width: 100% !important; height: 38px; font-weight: 700; font-size: 0.75rem; padding: 0 !important;
    }}

    .calendar-table {{ font-family: sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .calendar-table th {{ font-weight: 800; padding-bottom: 5px; font-size: 0.85rem; }}
    .calendar-table th:first-child, .calendar-table th:last-child {{ color: #d71920; }}
    .holiday-red {{ color: #d71920 !important; font-weight: 800; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; font-weight: 800; }}
    
    .price-up {{ color: #d71920; }} .price-down {{ color: #0050b3; }}
    .market-section {{ margin-bottom: 30px; padding-bottom: 15px; border-bottom: 1px solid #eee; }}

    @media (max-width: 600px) {{
        .header-logo-title {{ font-size: 0.9rem; }}
        .status-line {{ font-size: 1.1rem; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ取得 ---
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

# --- 4. ヘッダー（絶対一行：HTMLとStreamlitの融合） ---
st.markdown('<div class="absolute-row" style="border-bottom: 1px solid #eee; padding: 10px 0; margin-bottom: 10px;">', unsafe_allow_html=True)
# 左側タイトル
st.markdown('<div class="header-logo-title">Stock Market Real-time</div>', unsafe_allow_html=True)
# 右側スイッチ（スイッチだけStreamlitの機能を使う）
new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
if new_lang and new_lang != st.session_state.lang:
    st.session_state.lang = new_lang; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 価格ボード（HTMLで一行を完全固定） ---
p_html = '<div class="absolute-row">'
for name, d in prices.items():
    c_cls = "price-up" if d['diff'] >= 0 else "price-down"
    sym = "▲" if d['diff'] >= 0 else "▼"
    p_html += f'''
    <div class="flex-item price-box">
        <div class="price-label">{name}</div>
        <div class="price-val">{d["val"]:,.0f}</div>
        <div class="{c_cls}" style="font-size:0.55rem; font-weight:700;">{sym}{abs(d["diff"]):.0f}</div>
    </div>'''
p_html += '</div>'
st.markdown(p_html, unsafe_allow_html=True)

# --- 6. 共通ロジック ---
def get_market_status(now, m_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if m_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot, ct = (time(9, 30), time(16, 0)) if m_type == "US" else (time(9, 0), time(15, 0))
    td = now.date()
    nx = td
    if now.time() >= ct or td.weekday() >= 5 or td in th:
        while True:
            nx += timedelta(days=1)
            if nx.weekday() < 5 and nx not in th: break
    st_text = L["open"] if (ot <= now.time() < ct and td.weekday() < 5 and td not in th) else (L["holiday"] if (td.weekday() >= 5 or td in th) else L["closed"])
    bg = "#e6ffed" if st_text == L["open"] else ("#f9f9f9" if st_text == L["holiday"] else "#fff1f0")
    return f'<div class="status-line" style="background-color: {bg};"><span>{st_text}</span><span class="status-next">{L["next"]}{nx.strftime("%m/%d %H:%M")}</span></div>'

def draw_cal(now, cc, state_key, suffix):
    view = st.session_state[state_key]
    dst_txt = f'DST: {"サマータイム中" if now.dst() != timedelta(0) else "非サマータイム中"}' if cc == "US" else ""
    # 時計のフォントを日付(Inter)と同じに設定
    st.markdown(f'''<div class="cal-header"><span class="cal-date">{now.strftime("%Y/%m/%d")}</span><span class="cal-time">{now.strftime("%H:%M:%S")}</span><span class="cal-dst">{dst_txt}</span></div>''', unsafe_allow_html=True)
    
    th = holidays.CountryHoliday(cc, years=view.year)
    cal = calendar.monthcalendar(view.year, view.month)
    html = f'<table class="calendar-table"><tr><th>{L["sun"]}</th><th>{L["mon"]}</th><th>{L["tue"]}</th><th>{L["wed"]}</th><th>{L["thu"]}</th><th>{L["fri"]}</th><th>{L["sat"]}</th></tr>'
    for w in cal:
        html += '<tr>'
        for i, d in enumerate(w):
            if d == 0: html += '<td></td>'
            else:
                curr = date(view.year, view.month, d)
                cls = "holiday-red" if (i==0 or i==6 or curr in th) else ""
                txt = f'<span class="today-marker">{d}</span>' if curr == now.date() else str(d)
                html += f'<td><span class="{cls}">{txt}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    # ボタン：Streamlitのカラムを使わず、独自のボタン行（HTMLラッパー）で包む
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)
    b_cols = st.columns(3)
    with b_cols[0]:
        if st.button(L["prev"], key=f"p_{suffix}"):
            m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    with b_cols[1]:
        if st.button(L["today"], key=f"t_{suffix}"):
            st.session_state[state_key] = now.date().replace(day=1); st.rerun()
    with b_cols[2]:
        if st.button(L["next_m"], key=f"n_{suffix}"):
            m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1)
            st.session_state[state_key] = date(y, m, 1); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. レイアウト実行（デスクトップ2列 / モバイル縦並び） ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

# PCでは左右並び、モバイルでは自動縦積みを活かす大枠のカラム
c_main1, c_main2 = st.columns(2, gap="large")
with c_main1:
    st.header(L["us_m"])
    st.markdown(get_market_status(n_ny, "US"), unsafe_allow_html=True)
    draw_cal(n_ny, "US", "v_us", "us")
with c_main2:
    st.header(L["jp_m"])
    st.markdown(get_market_status(n_jp, "JP"), unsafe_allow_html=True)
    draw_cal(n_jp, "JP", "v_jp", "jp")
