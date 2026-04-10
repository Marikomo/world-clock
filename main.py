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

# 祝日設定
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

# --- 2. ニュース・イベントの「生データ」 ---
# ここに書いた内容がそのまま枠内に表示されます
AI_NEWS_DATA = {
    "US": [
        "1. NVIDIA: 次世代Blackwellチップの需要が供給を圧倒",
        "2. OpenAI: GPT-5のプレビュー版公開が数ヶ月以内との報道",
        "3. Microsoft: 日本国内AIデータセンターへ4400億円投資",
        "4. Google: Gemini 1.5 Proが100万トークンの入力をサポート",
        "5. Meta: 独自LLM Llama-4 学習用にH100を10万枚確保",
        "6. Apple: WWDCでiPhone向け新AI『Apple Intelligence』発表か",
        "7. Amazon: AIスタートアップAnthropicへ追加出資で攻勢",
        "8. Tesla: 完全自動運転FSDの予測精度が最新AIで劇的向上",
        "9. AMD: AIサーバーシェア獲得に向けMI300を増産体制へ",
        "10. Palantir: 米軍とのAI分析契約更新で株価が安定推移"
    ],
    "JP": [
        "1. ソフトバンクG: 孫会長、AI革命主導へ10兆円投資枠を確保",
        "2. さくらネット: GPUクラウド『高火力』の予約が年内完売",
        "3. NTT: 独自LLM『tsuzumi』の商用導入が50社を突破",
        "4. 富士通: 創薬AIの精度が世界1位を記録、開発期間を短縮",
        "5. NEC: 官公庁向けセキュア生成AIの構築案件を相次ぎ受注",
        "6. LINEヤフー: 検索体験をAI回答型に刷新、国内最大級の導入",
        "7. 三菱UFJ: 全行員へのAIアシスタント導入で業務を大幅効率化",
        "8. トヨタ: 車載AIによる自動運転レベル4の公道試験を本格化",
        "9. 楽天: グループ全体のAI統合戦略『AI-nization』が加速",
        "10. 日本政府: 国産AI計算資源の確保に向けた追加支援を決定"
    ]
}

EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 消費者物価指数(CPI)発表", "2026-04-11": "🇺🇸 米 生産者物価指数(PPI)発表",
    "2026-04-15": "🇺🇸 米 大手金融機関 決算発表開始", "2026-04-27": "🇯🇵 日銀金融政策決定会合(Day1)",
    "2026-04-28": "🇯🇵 日銀結果発表・植田総裁会見", "2026-04-29": "🇺🇸 FOMC政策金利発表(Day1)",
    "2026-04-30": "🇺🇸 FOMC金利発表・パウエル会見", "2026-05-01": "🇺🇸 米 雇用統計発表",
    "2026-05-03": "🇯🇵 憲法記念日(市場休場)", "2026-05-20": "🇺🇸 NVIDIA 決算発表予定(推定)",
    "2026-11-03": "🇺🇸 米国中間選挙 投開票日"
}

# --- 3. 動的計算ロジック ---
def get_next_open_delta(now, market_type):
    open_time = time(9, 30) if market_type == "US" else time(9, 0)
    h_list = us_holidays if market_type == "US" else jp_holidays
    target = datetime.combine(now.date(), open_time).replace(tzinfo=now.tzinfo)
    if now >= target or now.date() in h_list or now.weekday() >= 5:
        while True:
            target += timedelta(days=1)
            if target.weekday() < 5 and target.date() not in h_list: break
    delta = target - now
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600); minutes, seconds = divmod(rem, 60)
    if days > 0: return f"あと{days}日 {hours:02d}:{minutes:02d}"
    return f"あと{hours}時間{minutes}分"

# --- 4. CSS (デザイン復元) ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #111; border-bottom: 2px solid #111; padding-bottom: 10px; margin-bottom: 20px; }}
    .price-box {{ border: 1px solid #ddd; padding: 15px 5px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .price-val {{ font-size: 1.65rem; font-weight: 900; line-height: 1.1; color: #111; }} 
    .status-line {{ font-size: 1.2rem; font-weight: 900; padding: 12px; border: 1px solid #ddd; border-left: 10px solid #111; background-color: #fff; margin-bottom: 15px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px; table-layout: fixed; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; font-weight: 800; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #333; border-bottom: 1px dotted #ccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #111; padding-bottom: 8px; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# --- 5. UI構築 ---
st.markdown(f'<div class="logo-text">{L["logo"]}</div>', unsafe_allow_html=True)
col_l, col_r = st.columns([8, 2])
with col_r:
    new_lang = st.segmented_control("LANG", ["JP", "EN"], default=st.session_state.lang, label_visibility="collapsed")
    if new_lang and new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()

@st.cache_data(ttl=60)
def get_prices():
    tickers = { "S&P 500": "^GSPC", "Gold": "GC=F", "USD/JPY": "JPY=X" }
    res = {}
    for k, v in tickers.items():
        try:
            t = yf.Ticker(v); h = t.history(period="2d")
            c = h['Close'].iloc[-1]; p = h['Close'].iloc[-2]
            res[k] = {"val": c, "diff": c - p}
        except: res[k] = {"val": 0, "diff": 0}
    return res
prices = get_prices()

# 価格
p_cols = st.columns(3)
for i, (k, v) in enumerate(prices.items()):
    with p_cols[i]:
        st.markdown(f'<div class="price-box"><div style="font-size:0.8rem; color:#666; font-weight:700;">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.85rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# 市場
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        h_list = us_holidays if cc=="US" else jp_holidays
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        st_txt = L["open"] if is_op else L["closed"]
        st_info = "" if is_op else f'<span style="float:right; font-size:0.8rem; color:#666;">{L["next_prefix"]}{get_next_open_delta(now, cc)}</span>'
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} {st_info}</div>', unsafe_allow_html=True)
        
        dst = f' <span style="color:#d71920; font-size:0.85rem; font-weight:900;">({L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]})</span>' if cc == "US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.2rem; margin-bottom:15px;">{now.strftime("%Y/%m/%d")} {now.strftime("%H:%M:%S")}{dst}</div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th style="color:#888; font-size:0.8rem;">{d}</th>' for d in [L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]]) + '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    ev = EVENTS_DATA.get(curr_d.strftime("%Y-%m-%d"), "")
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    h += f'<td><span class="{"event-mark" if ev else ""}" style="color:{"#d71920" if i==0 or i==6 or curr_d in h_list else "#111"};">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        # 操作ボタン
        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=state_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=state_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        # 【枠：イベント】カレンダー月と完全連動
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 {L["event_title"]}</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:250px; overflow-y:auto;">' + ("".join(m_ev) if m_ev else "なし") + '</div>', unsafe_allow_html=True)

        # 【枠：ニュース】生データを直接流し込み
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            news_items = "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]])
            st.markdown(f'<div style="height:250px; overflow-y:auto;">{news_items}</div>', unsafe_allow_html=True)
