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
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶", "news": "📢 AI News", "event": "📅 Events"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶", "news": "📢 AI News", "event": "📅 Events"
    }
}
L = L_MAP[st.session_state.lang]

# --- 2. 究極のCSS（文字サイズアップとホバー機能） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}

    /* 価格ボード：文字をさらに大きく */
    .absolute-row {{ display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }}
    .price-box {{ border: 1px solid #ddd; padding: 12px 5px; background-color: #fff; flex: 1; text-align: center; }}
    .price-label {{ font-size: 0.8rem; color: #666; font-weight: 700; }}
    .price-val {{ font-size: 1.4rem; font-weight: 900; line-height: 1.1; }} /* 大きくしました */
    
    /* ホバーで詳細を出す魔法（Tooltips） */
    .hover-tip {{ position: relative; display: inline-block; cursor: pointer; width: 100%; }}
    .hover-text {{
        visibility: hidden; width: 220px; background-color: #111; color: #fff;
        text-align: left; border-radius: 4px; padding: 10px; position: absolute;
        z-index: 100; bottom: 110%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.5s ease-in-out; /* 1秒弱でふわっと出る */
        font-size: 0.75rem; font-weight: normal; line-height: 1.4; pointer-events: none;
    }}
    .hover-tip:hover .hover-text {{ visibility: visible; opacity: 1; transition-delay: 0.5s; }}

    /* 市場ステータス */
    .status-line {{
        font-size: 1.35rem; font-weight: 900; padding: 12px; border: 1px solid #ddd;
        border-left: 8px solid #111; background-color: #fff; display: flex; justify-content: space-between;
    }}

    .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; text-align: center; }}
    .calendar-table th {{ font-size: 0.85rem; padding-bottom: 5px; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; }}
    .holiday-red {{ color: #d71920; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# --- 3. データ（ニュースとイベント） ---
AI_NEWS = "・OpenAI: GPT-5の開発示唆\n・Google: Gemini 1.5 Proアップデート\n・NVIDIA: 新型チップ供給加速"
EVENTS = {
    "2026-11-03": "🇺🇸 アメリカ中間選挙 (Midterm Election)",
    "2026-05-01": "🇯🇵 日本: ゴールデンウィーク",
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
with col_h1: st.markdown('<div style="font-size: 1.1rem; font-weight: 900; padding: 10px 0;">Stock Market Real-time</div>', unsafe_allow_html=True)
with col_h2:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

# --- 5. 価格ボード（ホバーでニュース表示） ---
p_html = '<div class="absolute-row">'
for name, d in prices.items():
    c_cls = "color: #d71920;" if d['diff'] >= 0 else "color: #0050b3;"
    sym = "▲" if d['diff'] >= 0 else "▼"
    # ホバーテキストの内容（AIニュースをここに埋め込む）
    hover_content = f"<b>{L['news']}</b><br>{AI_NEWS.replace(chr(10), '<br>')}"
    
    p_html += f'''
    <div class="hover-tip flex-item">
        <div class="price-box">
            <div class="price-label">{name}</div>
            <div class="price-val">{d["val"]:,.0f}</div>
            <div style="{c_cls} font-size:0.7rem; font-weight:700;">{sym}{abs(d["diff"]):.0f}</div>
        </div>
        <span class="hover-text">{hover_content}</span>
    </div>'''
p_html += '</div>'
st.markdown(p_html, unsafe_allow_html=True)

# --- 6. カレンダー & イベント ---
def draw_cal(now, cc, state_key, suffix):
    view = st.session_state[state_key]
    st.markdown(f'<div style="font-weight:900; font-size:1.1rem;">{now.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)
    
    th = holidays.CountryHoliday(cc, years=view.year)
    cal = calendar.monthcalendar(view.year, view.month)
    
    html = f'<table class="calendar-table"><tr>'
    for day in [L["sun"], L["mon"], L["tue"], L["wed"], L["thu"], L["fri"], L["sat"]]:
        html += f'<th>{day}</th>'
    html += '</tr>'

    for w in cal:
        html += '<tr>'
        for i, d in enumerate(w):
            if d == 0: html += '<td></td>'
            else:
                curr = date(view.year, view.month, d)
                curr_str = curr.strftime("%Y-%m-%d")
                
                # イベントがある日の処理（ホバー対応）
                event_txt = EVENTS.get(curr_str, "")
                cls = "holiday-red" if (i==0 or i==6 or curr in th or event_txt) else ""
                
                cell_content = f'<span class="today-marker">{d}</span>' if curr == now.date() else str(d)
                
                if event_txt:
                    html += f'''<td><div class="hover-tip">
                        <span class="{cls}" style="text-decoration: underline;">{cell_content}</span>
                        <span class="hover-text"><b>{L['event']}</b><br>{event_txt}</span>
                    </div></td>'''
                else:
                    html += f'<td><span class="{cls}">{cell_content}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    # ボタン
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

# --- 7. メインレイアウト ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="large")
with c1:
    st.header(L["us_m"])
    draw_cal(n_ny, "US", "v_us", "us")
with c2:
    st.header(L["jp_m"])
    draw_cal(n_jp, "JP", "v_jp", "jp")
