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

us_holidays = holidays.US()
jp_holidays = holidays.Japan()

T = {
    "JP": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場",
        "open": "開場中", "closed": "閉場中", "next_prefix": "次回開場まで: ",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶",
        "news_title": "🚀 今週のAI株式ニュース (TOP 10)", "event_title": "注目の株式イベント",
        "dst_on": "サマータイム中", "dst_off": "通常時間",
        "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土"
    },
    "EN": {
        "logo": "STOCK MARKET REAL-TIME", "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market",
        "open": "OPEN", "closed": "CLOSED", "next_prefix": "Next Open in: ",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶",
        "news_title": "🚀 Weekly AI Stock News (TOP 10)", "event_title": "Monthly Market Events",
        "dst_on": "Daylight Saving Time", "dst_off": "Standard Time",
        "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT"
    }
}
L = T[st.session_state.lang]

# --- 2. CSS (デザイナー指定配色) ---
st.markdown(f"""
<style>
    /* 全体背景を白に固定 */
    .stApp, .block-container, [data-testid="stAppViewContainer"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}
    
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 1rem !important; margin-top: -65px !important; }}
    
    /* ロゴ */
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; border-bottom: 2px solid #000000; padding-bottom: 10px; margin-bottom: 20px; }}
    h1, h2, h3, span, div, p, th {{ color: #000000 !important; }}

    /* 各種枠をグレー(#cccccc)に統一 */
    .price-box {{ border: 1px solid #cccccc; padding: 15px 5px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background-color: #fff; margin-bottom: 15px; }}
    
    /* カレンダーの枠・文字色設定 */
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; table-layout: fixed; margin-bottom: 10px; border: 1px solid #cccccc; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #ff4b4b; text-underline-offset: 4px; font-weight: 800; }}
    
    /* ボタンのカスタマイズ: 背景白、文字黒、枠グレー */
    div.stButton > button {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        width: 100%;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: #f8f8f8 !important;
        border-color: #000000 !important;
    }}

    /* ニュース・イベント枠(グレー) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        padding: 10px;
    }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. ロジック ---
def get_next_open_delta(now, cc):
    ot = time(9, 30) if cc == "US" else time(9, 0)
    h_list = us_holidays if cc == "US" else jp_holidays
    target = datetime.combine(now.date(), ot).replace(tzinfo=now.tzinfo)
    if now >= target or now.date() in h_list or now.weekday() >= 5:
        while True:
            target += timedelta(days=1)
            if target.weekday() < 5 and target.date() not in h_list: break
    d = target - now
    h, r = divmod(d.seconds, 3600); m, _ = divmod(r, 60)
    return f"あと{d.days}日 {h:02d}:{m:02d}" if d.days > 0 else f"あと{h}時間{m}分"

# --- 4. UI構築 ---
st.markdown(f'<div class="logo-text">{L["logo"]}</div>', unsafe_allow_html=True)
col_l, col_r = st.columns([8, 2])
with col_r:
    new_lang = st.segmented_control("L", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

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
        st.markdown(f'<div class="price-box"><div style="font-size:0.75rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.8rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

AI_NEWS_DATA = {
    "US": ["1. NVIDIA: Blackwell量産で供給不足解消へ", "2. OpenAI: GPT-5 プレビュー期待高まる", "3. Microsoft: 日本国内AI投資加速", "4. Google: Gemini 1.5 アップデート", "5. Meta: Llama-4 学習リソース拡大", "6. Apple: WWDCでのAI発表に注目", "7. Amazon: AIチップ内製化進展", "8. Tesla: FSD予測精度向上", "9. AMD: AIサーバーシェア拡大", "10. Palantir: 米軍AI契約更新"],
    "JP": ["1. SBG: 孫会長 AI革命に10兆円投資枠", "2. さくらネット: GPUクラウド予約完売", "3. NTT: tsuzumi導入企業急増", "4. 富士通: 創薬AI世界1位の精度", "5. NEC: 官公庁AI案件を独占", "6. LINEヤフー: AI検索機能を刷新", "7. 三菱UFJ: 全行員AIアシスタント", "8. トヨタ: レベル4自動運転試験", "9. 楽天: AI統合戦略が加速", "10. 日本政府: 国産AIへの追加支援"]
}
EVENTS_DATA = {"2026-04-10": "🇺🇸 米 CPI発表", "2026-04-11": "🇺🇸 米 PPI発表", "2026-04-15": "🇺🇸 米 大手金融決算", "2026-04-27": "🇯🇵 日銀会合(1)", "2026-04-28": "🇯🇵 日銀発表", "2026-04-29": "🇺🇸 FOMC(1)", "2026-04-30": "🇺🇸 FOMC金利発表", "2026-05-01": "🇺🇸 米 雇用統計", "2026-11-03": "🇺🇸 米国中間選挙"}

c1, c2 = st.columns(2, gap="medium")
for col, now, cc, s_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        h_list = us_holidays if cc=="US" else jp_holidays
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        st_txt = L["open"] if is_op else L["closed"]
        st_info = "" if is_op else f'<span style="float:right; font-size:0.75rem; color:#666;">{L["next_prefix"]}{get_next_open_delta(now, cc)}</span>'
        st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op else "#fff5f5"};">{st_txt} {st_info}</div>', unsafe_allow_html=True)
        
        dst = f' <span style="color:#d71920; font-size:0.8rem; font-weight:900;">({L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]})</span>' if cc == "US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem; margin-bottom:10px;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")}{dst}</div>', unsafe_allow_html=True)
        
        view = st.session_state[s_key]
        cal = calendar.monthcalendar(view.year, view.month)
        
        # カレンダー描画（土曜=青、日曜祝日=赤、枠=グレー）
        h = f'<table class="calendar-table"><tr>'
        for i, d in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
            c = "#d71920" if i==0 else ("#0050b3" if i==6 else "#888")
            h += f'<th style="color:{c} !important; font-size:0.75rem;">{d}</th>'
        h += '</tr>'
        
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    ev = EVENTS_DATA.get(curr_d.strftime("%Y-%m-%d"), "")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    # 土=青、日・祝=赤
                    if i == 0 or curr_d in h_list: color = "#d71920"
                    elif i == 6: color = "#0050b3"
                    else: color = "#111"
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{color} !important;">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=s_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:220px; overflow-y:auto;">' + ("".join(m_ev) if m_ev else "なし") + '</div>', unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:220px; overflow-y:auto;">' + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
