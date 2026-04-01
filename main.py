import streamlit as st
from datetime import datetime, timedelta, date, time
import pytz
import calendar
import holidays
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. 言語設定の初期化 ---
if 'lang' not in st.session_state:
    st.session_state.lang = "JP"

# --- 2. 基本設定 ---
calendar.setfirstweekday(calendar.SUNDAY)
st_autorefresh(interval=60000, key="data_refresh")
st_autorefresh(interval=1000, key="clock_refresh")
st.set_page_config(page_title="Stock Market Calendar", layout="wide")

# テキスト辞書（ステータスの日本語化を追加）
T = {
    "JP": {
        "us_market": "🇺🇸 米国市場", "jp_market": "🇯🇵 日本市場",
        "next_open": "次回の開場まで: ", "prev": "◀ 前月", "next": "次月 ▶", "today": "今月",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "waiting": "開場待ち (あと ", "open": "開場中 (閉場まで ", "closed_end": "本日終了",
        "weekend": "週末", "holiday": "祝日"
    },
    "EN": {
        "us_market": "🇺🇸 US Market", "jp_market": "🇯🇵 JP Market",
        "next_open": "Next Open: ", "prev": "◀ Prev", "next": "Next ▶", "today": "Current",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "waiting": "WAITING... (Opens in ", "open": "OPEN (Closes in ", "closed_end": "CLOSED (DAY END)",
        "weekend": "WEEKEND", "holiday": "HOLIDAY"
    }
}
L = T[st.session_state.lang]

# --- 3. スタイル設定（土日の赤色を復元） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: -60px !important; }}

    .header-logo-title {{
        font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 900; color: #111; letter-spacing: -0.04em;
    }}

    /* カレンダーテーブル */
    .calendar-table {{ font-family: sans-serif; text-align: center; width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 0.9rem; }}
    .calendar-table th {{ font-weight: 800; color: #222; padding-bottom: 5px; }}
    .calendar-table th:first-child, .calendar-table th:last-child {{ color: #d71920; }} /* 曜日の土日を赤に */
    
    .calendar-table tr {{ height: 40px; }}
    
    /* 今日のマーカー */
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; }}
    
    /* 土日・祝日の数字を赤に */
    .holiday-red {{ color: #d71920 !important; font-weight: 800; }}
    
    .price-up {{ color: #d71920; }} .price-down {{ color: #0050b3; }}
    .market-status {{ font-size: 0.95rem; font-weight: 800; padding: 12px; border: 1px solid #ddd; margin-bottom: 15px; background-color: #fff; border-left: 5px solid #333; }}
    
    /* PC・スマホ出し分け */
    @media (max-width: 800px) {{ .header-logo-title {{ font-size: 1.1rem; }} .desktop-view {{ display: none !important; }} .mobile-view {{ display: block !important; }} }}
    @media (min-width: 801px) {{ .mobile-view {{ display: none !important; }} .desktop-view {{ display: block !important; }} }}
</style>
""", unsafe_allow_html=True)

# --- 4. ヘッダー描画 ---
h_col1, h_col2 = st.columns([8, 1.5])
with h_col1:
    st.markdown('<div class="header-logo-title">Stock Market Real-time</div>', unsafe_allow_html=True)
with h_col2:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()

st.markdown('<hr style="margin: 10px 0 20px 0; border: 0; border-top: 1px solid #eee;">', unsafe_allow_html=True)

# --- 5. 市場データ取得 ---
@st.cache_data(ttl=60)
def get_market_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker); h = t.history(period="2d")
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            data[name] = {"price": curr, "diff": curr - prev, "pct": ((curr-prev)/prev)*100}
        except: data[name] = {"price": 0, "diff": 0, "pct": 0}
    return data

p = get_market_prices()
m_cols = st.columns(3)
for i, (name, d) in enumerate(p.items()):
    c, s = ("price-up", "▲") if d['diff'] >= 0 else ("price-down", "▼")
    with m_cols[i]:
        st.markdown(f'<div style="border: 1px solid #ddd; padding: 10px; text-align: center; background-color: #fff; margin-bottom: 15px;"><div style="font-size: 0.75rem; color: #666; font-weight: 700;">{name}</div><div style="font-size: 1.1rem; font-weight: 800; color: #111;">{d["price"]:,.1f}</div><div class="{c}" style="font-size:0.75rem; font-weight:700;">{s}{abs(d["diff"]):.1f} ({d["pct"]:.2f}%)</div></div>', unsafe_allow_html=True)

# --- 6. ロジック関数 ---
def get_next_open_dt(now, country_code):
    cc, th = ("US", holidays.CountryHoliday("US")) if country_code == "US" else ("JP", holidays.CountryHoliday("JP"))
    ot = time(9, 30) if country_code == "US" else time(9, 0)
    td = now.date()
    # 今日が営業日かつ開場前なら今日
    if td.weekday() < 5 and td not in th and now.time() < ot:
        return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)
    # それ以外は翌日以降の営業日を探す
    while True:
        td += timedelta(days=1)
        if td.weekday() < 5 and td not in th:
            return datetime.combine(td, ot).replace(tzinfo=now.tzinfo)

def get_market_status_ui(now, market_type):
    cc, th = ("US", holidays.CountryHoliday("US")) if market_type == "US" else ("JP", holidays.CountryHoliday("JP"))
    is_h = now.date() in th
    ot, ct = (now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)) if market_type == "US" else (now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0))
    
    nx = get_next_open_dt(now, market_type)
    cd = f"{L['next_open']} {nx.strftime('%m/%d %H:%M')}"
    
    if not (0 <= now.weekday() <= 4) or is_h:
        reason = L["holiday"] if is_h else L["weekend"]
        return f"CLOSED ({reason})<br><small>{cd}</small>", "#f9f9f9"
    if now < ot:
        rem = ot - now
        return f"{L['waiting']}{rem.seconds//3600:02d}:{(rem.seconds//60)%60:02d})", "#fffbe6"
    elif ot <= now < ct:
        rem = ct - now
        return f"{L['open']}{rem.seconds//3600:02d}:{(rem.seconds//60)%60:02d})", "#e6ffed"
    else:
        return f"{L['closed_end']}<br><small>{cd}</small>", "#fff1f0"

def draw_cal_ui(now_full, country_code, state_key, country_tz, suffix=""):
    view_date = st.session_state[state_key]
    date_label = view_date.strftime('%Y / %m') if st.session_state.lang == "JP" else view_date.strftime('%B %Y')
    st.markdown(f"<div style='font-weight:900; font-size:1.1rem; margin-bottom:5px;'>{date_label}</div>", unsafe_allow_html=True)
    
    # 祝日の取得（表示中の年月に基づく）
    target_holidays = holidays.CountryHoliday(country_code, years=view_date.year)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    
    html = f'<table class="calendar-table"><tr><th>{L["sun"]}</th><th>{L["mon"]}</th><th>{L["tue"]}</th><th>{L["wed"]}</th><th>{L["thu"]}</th><th>{L["fri"]}</th><th>{L["sat"]}</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0: html += '<td></td>'
            else:
                curr = date(view_date.year, view_date.month, day)
                h_name = target_holidays.get(curr)
                # 土日、または祝日なら赤クラスを適用
                is_red = (i == 0 or i == 6 or h_name is not None)
                cls = "holiday-red" if is_red else ""
                
                content = f'<span class="today-marker">{day}</span>' if curr == now_full.date() else str(day)
                # 祝日名がある場合はツールチップ（簡易版）
                if h_name:
                    html += f'<td><span class="{cls}" title="{h_name}">{content}</span></td>'
                else:
                    html += f'<td><span class="{cls}">{content}</span></td>'
        html += '</tr>'
    st.markdown(html + '</table>', unsafe_allow_html=True)
    
    b1, b2, b3 = st.columns([1, 1, 1])
    if b1.button(L["prev"], key=f"p_{state_key}_{suffix}"):
        m, y = (view_date.month-1, view_date.year) if view_date.month > 1 else (12, view_date.year-1)
        st.session_state[state_key] = date(y, m, 1); st.rerun()
    if b2.button(L["today"], key=f"t_{state_key}_{suffix}"):
        st.session_state[state_key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1); st.rerun()
    if b3.button(L["next"], key=f"n_{state_key}_{suffix}"):
        m, y = (view_date.month+1, view_date.year) if view_date.month < 12 else (1, view_date.year+1)
        st.session_state[state_key] = date(y, m, 1); st.rerun()

# --- 7. レイアウト処理 ---
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = now_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = now_jp.date().replace(day=1)

# デスクトップ表示
st.markdown('<div class="desktop-view">', unsafe_allow_html=True)
d_col_us, d_col_jp = st.columns(2, gap="large")
with d_col_us:
    st.header(L["us_market"])
    s_us, c_us = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {c_us};">{s_us}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_ny, "US", "v_us", "America/New_York", suffix="d")
with d_col_jp:
    st.header(L["jp_market"])
    s_jp, c_jp = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {c_jp};">{s_jp}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_jp, "JP", "v_jp", "Asia/Tokyo", suffix="d")
st.markdown('</div>', unsafe_allow_html=True)

# モバイル表示
st.markdown('<div class="mobile-view">', unsafe_allow_html=True)
m_tab_us, m_tab_jp = st.tabs([L["us_market"], L["jp_market"]])
with m_tab_us:
    s_m_us, c_m_us = get_market_status_ui(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {c_m_us};">{s_m_us}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_ny, "US", "v_us", "America/New_York", suffix="m")
with m_tab_jp:
    s_m_jp, c_m_jp = get_market_status_ui(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {c_m_jp};">{s_m_jp}</div>', unsafe_allow_html=True)
    draw_cal_ui(now_jp, "JP", "v_jp", "Asia/Tokyo", suffix="m")
st.markdown('</div>', unsafe_allow_html=True)
