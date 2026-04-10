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

# --- 2. ニュース・イベントデータ ---
AI_NEWS_DATA = {
    "US": [
        "1. NVIDIA: Blackwellチップの本格量産体制を構築完了",
        "2. OpenAI: 次期大型モデルGPT-5の安全評価期間を開始",
        "3. Microsoft: 日本でのAI基盤へ史上最大4400億円投資",
        "4. Google: Gemini 1.5 Proが100万トークン処理を全開放",
        "5. Meta: 独自LLM Llama-4 学習用H100を10万枚確保",
        "6. Apple: WWDCに向けiOSへの独自生成AI搭載を最終調整",
        "7. Amazon: AIスタートアップAnthropicへ追加出資で包囲網",
        "8. Tesla: AI搭載自動運転FSD v12の予測精度が飛躍的向上",
        "9. AMD: AIサーバーシェア獲得に向けMI300を増産",
        "10. Intel: AI PC向け最新チップの生産ラインをフル稼働"
    ],
    "JP": [
        "1. SBG: 孫会長、AI革命に向けた10兆円投資枠を確保",
        "2. さくらネット: GPUクラウド『高火力』の予約が年内満杯",
        "3. NTT: 独自LLM『tsuzumi』の商用導入が50社を突破",
        "4. 富士通: 創薬AIの精度が世界1位を記録、開発期間短縮",
        "5. NEC: 官公庁向け専用AI基盤の構築案件を相次ぎ受注",
        "6. LINEヤフー: 検索体験をAI回答型に刷新、国内最大級導入",
        "7. 三菱UFJ: 全行員へのAIアシスタント導入で業務効率化",
        "8. トヨタ: 車載AIによる自動運転レベル4の公道試験開始",
        "9. 楽天: グループ全体のAI統合戦略『AI-nization』が加速",
        "10. 日本政府: 国産AI計算資源の確保に向けた追加支援決定"
    ]
}
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI発表", "2026-04-11": "🇺🇸 米 PPI発表", "2026-04-15": "🇺🇸 大手金融決算", 
    "2026-04-27": "🇯🇵 日銀会合(1)", "2026-04-28": "🇯🇵 日銀結果発表", 
    "2026-04-29": "🇺🇸 FOMC(1)", "2026-04-30": "🇺🇸 FOMC金利発表", 
    "2026-05-01": "🇺🇸 米 雇用統計", "2026-05-20": "🇺🇸 NVIDIA 決算予定", "2026-11-03": "🇺🇸 米国中間選挙"
}

# --- 3. 動的カウントダウン ---
def get_next_open_delta(now, cc):
    ot = time(9, 30) if cc == "US" else time(9, 0)
    h_list = us_holidays if cc == "US" else jp_holidays
    target = datetime.combine(now.date(), ot).replace(tzinfo=now.tzinfo)
    if now >= target or now.date() in h_list or now.weekday() >= 5:
        while True:
            target += timedelta(days=1)
            if target.weekday() < 5 and target.date() not in h_list: break
    d = target - now
    hours, rem = divmod(d.seconds, 3600); mins, _ = divmod(rem, 60)
    return f"あと{d.days}日 {hours:02d}:{mins:02d}" if d.days > 0 else f"あと{hours}時間{mins}分"

# --- 4. CSS (文字黒・枠グレー・白背景) ---
st.markdown(f"""
<style>
    /* 全体設定 */
    .stApp, .block-container, [data-testid="stAppViewContainer"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}
    
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 1rem !important; margin-top: -60px !important; }}
    
    /* ロゴとテキストカラーを黒に固定 */
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; border-bottom: 2px solid #000000; padding-bottom: 10px; margin-bottom: 20px; }}
    h1, h2, h3, span, div, p {{ color: #000000 !important; }}

    /* 枠線をグレー(#cccccc)に設定 */
    .price-box {{ border: 1px solid #cccccc; padding: 15px 5px; background-color: #fff; text-align: center; border-radius: 8px; }}
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background-color: #fff; margin-bottom: 15px; }}
    
    /* カレンダー */
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; table-layout: fixed; margin-bottom: 10px; }}
    .calendar-table th {{ color: #666666 !important; font-size: 0.75rem; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; font-weight: 800; }}
    
    /* リスト枠（グレー境界線） */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
    }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}
</style>
""", unsafe_allow_html=True)

# --- 5. UI構築 ---
st.markdown(f'<div class="logo-text">{L["logo"]}</div>', unsafe_allow_html=True)
col_l, col_r = st.columns([7, 3])
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
        st.markdown(f'<div class="price-box"><div style="font-size:0.75rem; color:#666666; font-weight:700;">{k}</div><div class="price-val" style="color:#000000;">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.8rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="medium")
for col, now, cc, s_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        h_list = us_holidays if cc=="US" else jp_holidays
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        st_txt = L["open"] if is_op else L["closed"]
        st_info = "" if is_op else f'<span style="float:right; font-size:0.75rem; color:#666666;">{L["next_prefix"]}{get_next_open_delta(now, cc)}</span>'
        st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op else "#fff5f5"}; color:#000000;">{st_txt} {st_info}</div>', unsafe_allow_html=True)
        
        dst = f' <span style="color:#d71920; font-size:0.8rem; font-weight:900;">({L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]})</span>' if cc == "US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.1rem; margin-bottom:10px; color:#000000;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")}{dst}</div>', unsafe_allow_html=True)
        
        view = st.session_state[s_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th style="color:#666666; font-size:0.75rem;">{d}</th>' for d in [L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]]) + '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    ev = EVENTS_DATA.get(curr_d.strftime("%Y-%m-%d"), "")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    color = "#d71920" if i==0 or i==6 or curr_d in h_list else "#000000"
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{color};">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=s_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        # 注目のイベント枠
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:220px; overflow-y:auto; color:#000000;">' + ("".join(m_ev) if m_ev else "なし") + '</div>', unsafe_allow_html=True)

        # AIニュース枠
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:220px; overflow-y:auto; color:#000000;">' + "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]]) + '</div>', unsafe_allow_html=True)
