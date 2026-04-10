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

# 祝日データの取得
us_holidays = holidays.US()
jp_holidays = holidays.Japan()

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

# --- 2. 時刻計算 (UTC基準で1秒の狂いもなく算出) ---
utc_now = datetime.now(pytz.utc)
# 米国東部時間 (サマータイム中 UTC-4)
now_ny = (utc_now - timedelta(hours=4)).replace(tzinfo=None)
# 日本時間 (UTC+9)
now_jp = (utc_now + timedelta(hours=9)).replace(tzinfo=None)

# --- 3. CSS (デザイナー仕様: 正確な配色) ---
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
    
    /* カレンダーテーブル設定 */
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; border: 1px solid #cccccc; table-layout: fixed; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}
    .dst-label {{ font-size: 0.75rem; color: #888888 !important; font-weight: normal; margin-left: 8px; }}
</style>
""", unsafe_allow_html=True)

# --- 4. データ・UI構築 ---
st.markdown(f'<div class="header-sticky"><div class="logo-text">{L["logo"]}</div></div>', unsafe_allow_html=True)

# イベントデータ
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米CPI発表",
    "2026-04-28": "🇯🇵 日銀政策決定会合",
    "2026-04-30": "🇺🇸 FOMC政策金利発表",
    "2026-05-01": "🇺🇸 米雇用統計",
    "2026-05-15": "🇺🇸 主要ハイテク決算発表"
}

# 言語切り替え
_, col_lang = st.columns([8, 2])
with col_lang:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

# --- 市場価格 ---
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
        st.markdown(f'<div class="price-box"><div style="font-weight:900;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# --- メインコンテンツ ---
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

AI_NEWS = {
    "US": [f"{i+1}. NVIDIA/OpenAI 最新動向レポート {i+1}" for i in range(10)],
    "JP": [f"{i+1}. 国内AI・半導体 注目ニュース {i+1}" for i in range(10)]
}

c1, c2 = st.columns(2, gap="medium")
for col, now, cc, s_key, suffix, title in [(c1, now_ny, "US", "v_us", "us", L["us_m"]), (c2, now_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        h_list = us_holidays if cc=="US" else jp_holidays
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        
        # 次回開場計算
        target = datetime.combine(now.date(), ot)
        if now.time() >= ot or now.date() in h_list or now.weekday() >= 5:
            while True:
                target += timedelta(days=1)
                if target.weekday() < 5 and target.date() not in h_list: break
        delta = target - now
        h_c, r_c = divmod(delta.seconds, 3600); m_c, _ = divmod(r_c, 60)
        c_down = f"あと{delta.days}日 {h_c:02d}:{m_c:02d}" if delta.days > 0 else f"あと{h_c}時間{m_c}分"
        
        st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op else "#fff5f5"};">{L["open"] if is_op else L["closed"]} <span style="float:right; font-size:0.75rem; color:#666;">{"" if is_op else L["next_prefix"]+c_down}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-weight:900; font-size:1.35rem; margin-bottom:15px;">{now.strftime("%Y/%m/%d %H:%M:%S")}<span class="dst-label">{L["dst_on"] if cc=="US" else ""}</span></div>', unsafe_allow_html=True)
        
        # --- カレンダー表示 (配色修正) ---
        view = st.session_state[s_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h_table = f'<table class="calendar-table"><tr>'
        for i, d_n in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
            # ヘッダー配色: 日=赤、土=青
            header_color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
            h_table += f'<th style="color:{header_color} !important;">{d_n}</th>'
        h_table += '</tr>'
        for w in cal:
            h_table += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h_table += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    # 判定ロジック:
                    # 1. 日曜 (i==0) または 祝日 (curr_d in h_list) は 赤
                    # 2. 土曜 (i==6) は 青
                    if i == 0 or curr_d in h_list:
                        d_c = "#d71920"
                    elif i == 6:
                        d_c = "#0050b3"
                    else:
                        d_c = "#000000"
                    
                    d_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    h_table += f'<td><span style="color:{d_c} !important; font-weight:800;">{d_ui}</span></td>'
            h_table += '</tr>'
        st.markdown(h_table + '</table>', unsafe_allow_html=True)

        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=1)-timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=s_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=28)+timedelta(days=5)).replace(day=1)}))

        # --- イベント表示 (復活と表示月連動) ---
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            v_str = view.strftime("%Y-%m")
            # 表示中の月と一致するイベントのみ抽出
            monthly_events = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(v_str)]
            
            if monthly_events:
                st.markdown('<div style="height:150px; overflow-y:auto;">' + "".join(monthly_events) + '</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="height:150px; color:#999; font-size:0.8rem;">予定なし</div>', unsafe_allow_html=True)

        # --- ニュース ---
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            n_items = "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS[cc]])
            st.markdown(f'<div style="height:250px; overflow-y:auto;">{n_items}</div>', unsafe_allow_html=True)
