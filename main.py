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

# 祝日データの完全分離定義
US_HOLIDAYS_DB = holidays.US()
JP_HOLIDAYS_DB = holidays.Japan()

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next_prefix": "次回開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "dst_on": "（東海岸時間・サマータイム中）", "dst_off": "（東海岸時間・通常時間）",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next_prefix": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Market Events",
        "dst_on": "(ET / Daylight Saving Time)", "dst_off": "(ET / Standard Time)",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. 時刻取得 (JSTから正確に13時間戻して米国時間を生成) ---
now_jst = datetime.now(pytz.timezone('Asia/Tokyo')).replace(tzinfo=None)
now_edt = now_jst - timedelta(hours=13)

# --- 3. CSS (デザイナー仕様: 配色、余白) ---
st.markdown(f"""
<style>
    .stApp, .block-container {{ background-color: #ffffff !important; color: #000000 !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .header-sticky {{
        position: fixed; top: 0; left: 0; width: 100%; background: #ffffff;
        z-index: 9999; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center;
    }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; letter-spacing: -0.02em; }}
    .block-container {{ padding-top: 3.5rem !important; margin-top: -65px !important; }}
    .price-box {{ border: 1px solid #cccccc; padding: 15px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .price-val {{ font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #000000; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background-color: #fff; margin-bottom: 15px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; border: 1px solid #cccccc; table-layout: fixed; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="header-sticky"><div class="logo-text">{L["logo"]}</div></div>', unsafe_allow_html=True)

# 言語切替
_, col_lang = st.columns([8, 2])
with col_lang:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# --- 4. 市場データ取得 ---
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
prices_data = get_prices()
pc = st.columns(3)
for i, (k, v) in enumerate(prices_data.items()):
    with pc[i]:
        st.markdown(f'<div class="price-box"><div style="font-weight:900;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# セッション状態
if 'v_us' not in st.session_state: st.session_state.v_us = now_edt.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jst.date().replace(day=1)

# --- 5. メインレイアウト (物理的にコードを分離) ---
c_us, c_jp = st.columns(2, gap="medium")

# ==========================================
# 🇺🇸 米国市場
# ==========================================
with c_us:
    st.header(L["us_m"])
    ot_u, ct_u = (time(9, 30), time(16, 0))
    is_op_u = (ot_u <= now_edt.time() < ct_u and now_edt.weekday() < 5 and now_edt.date() not in US_HOLIDAYS_DB)
    st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op_u else "#fff5f5"};">{L["open"] if is_op_u else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem; margin-bottom:15px;">{now_edt.strftime("%Y/%m/%d %H:%M:%S")}<span style="font-size:0.75rem; color:#888; font-weight:normal; margin-left:8px;">{L["dst_on"]}</span></div>', unsafe_allow_html=True)

    # カレンダー
    v_u = st.session_state.v_us
    cal_u = calendar.monthcalendar(v_u.year, v_u.month)
    h_tab_u = f'<table class="calendar-table"><tr>'
    for i, d_n in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        h_tab_u += f'<th style="color:{color} !important;">{d_n}</th>'
    h_tab_u += '</tr>'
    for row in cal_u:
        h_tab_u += '<tr>'
        for i, d in enumerate(row):
            if d == 0: h_tab_u += '<td></td>'
            else:
                curr = date(v_u.year, v_u.month, d)
                # 土曜は青、日曜・米国祝日は赤
                d_color = "#d71920" if (i==0 or curr in US_HOLIDAYS_DB) else ("#0050b3" if i==6 else "#000000")
                d_ui = f'<span class="today-marker">{d}</span>' if curr == now_edt.date() else str(d)
                h_tab_u += f'<td><span style="color:{d_color} !important; font-weight:800;">{d_ui}</span></td>'
    st.markdown(h_tab_u + "</table>", unsafe_allow_html=True)
    
    bu = st.columns(3)
    with bu[0]: st.button(L["prev"], key="p_us_btn", on_click=lambda: st.session_state.update({"v_us": (v_u.replace(day=1)-timedelta(days=1)).replace(day=1)}))
    with bu[1]: st.button(L["today"], key="t_us_btn", on_click=lambda: st.session_state.update({"v_us": date.today().replace(day=1)}))
    with bu[2]: st.button(L["next_m"], key="n_us_btn", on_click=lambda: st.session_state.update({"v_us": (v_u.replace(day=28)+timedelta(days=5)).replace(day=1)}))

    with st.container(border=True):
        st.markdown(f'<div class="box-header">{v_u.month}月 米国市場イベント</div>', unsafe_allow_html=True)
        ev_u_dict = {"2026-04-10": "🇺🇸 米CPI発表", "2026-04-30": "🇺🇸 FOMC発表", "2026-05-01": "🇺🇸 米雇用統計"}
        m_ev_u = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(ev_u_dict.items()) if k.startswith(v_u.strftime("%Y-%m"))]
        st.markdown('<div style="height:150px; overflow-y:auto;">' + ("".join(m_ev_u) if m_ev_u else "予定なし") + '</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:250px; overflow-y:auto;">' + "".join([f'<div class="item-row">{i+1}. 米国テック・金融ニュース {i+1}</div>' for i in range(10)]) + '</div>', unsafe_allow_html=True)

# ==========================================
# 🇯🇵 日本市場
# ==========================================
with c_jp:
    st.header(L["jp_m"])
    ot_j, ct_j = (time(9, 0), time(15, 0))
    is_op_j = (ot_j <= now_jst.time() < ct_j and now_jst.weekday() < 5 and now_jst.date() not in JP_HOLIDAYS_DB)
    st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op_j else "#fff5f5"};">{L["open"] if is_op_j else L["closed"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:900; font-size:1.35rem; margin-bottom:15px;">{now_jst.strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)

    # 日本カレンダー
    v_j = st.session_state.v_jp
    cal_j = calendar.monthcalendar(v_j.year, v_j.month)
    h_tab_j = f'<table class="calendar-table"><tr>'
    for i, d_n in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
        color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
        h_tab_j += f'<th style="color:{color} !important;">{d_n}</th>'
    h_tab_j += '</tr>'
    for row in cal_j:
        h_tab_j += '<tr>'
        for i, d in enumerate(row):
            if d == 0: h_tab_j += '<td></td>'
            else:
                curr = date(v_j.year, v_j.month, d)
                # 土曜は青、日曜・日本祝日は赤
                d_color = "#d71920" if (i==0 or curr in JP_HOLIDAYS_DB) else ("#0050b3" if i==6 else "#000000")
                d_ui = f'<span class="today-marker">{d}</span>' if curr == now_jst.date() else str(d)
                h_tab_j += f'<td><span style="color:{d_color} !important; font-weight:800;">{d_ui}</span></td>'
    st.markdown(h_tab_j + "</table>", unsafe_allow_html=True)

    bj = st.columns(3)
    with bj[0]: st.button(L["prev"], key="p_jp_btn", on_click=lambda: st.session_state.update({"v_jp": (v_j.replace(day=1)-timedelta(days=1)).replace(day=1)}))
    with bj[1]: st.button(L["today"], key="t_jp_btn", on_click=lambda: st.session_state.update({"v_jp": date.today().replace(day=1)}))
    with bj[2]: st.button(L["next_m"], key="n_jp_btn", on_click=lambda: st.session_state.update({"v_jp": (v_j.replace(day=28)+timedelta(days=5)).replace(day=1)}))

    with st.container(border=True):
        st.markdown(f'<div class="box-header">{v_j.month}月 日本市場イベント</div>', unsafe_allow_html=True)
        ev_j_dict = {"2026-04-28": "🇯🇵 日銀発表", "2026-04-29": "🇯🇵 昭和の日", "2026-05-03": "🇯🇵 憲法記念日"}
        m_ev_j = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(ev_j_dict.items()) if k.startswith(v_j.strftime("%Y-%m"))]
        st.markdown('<div style="height:150px; overflow-y:auto;">' + ("".join(m_ev_j) if m_ev_j else "予定なし") + '</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:250px; overflow-y:auto;">' + "".join([f'<div class="item-row">{i+1}. 日本国内AI関連ニュース {i+1}</div>' for i in range(10)]) + '</div>', unsafe_allow_html=True)
