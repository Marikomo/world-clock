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

# --- 2. ニュース・イベントデータ ---
AI_NEWS_DATA = {
    "US": [
        "1. NVIDIA: Blackwellチップの本格量産体制を構築完了",
        "2. OpenAI: 次期大型モデルGPT-5の内部テスト段階入りを公式示唆",
        "3. Microsoft: 日本国内AIインフラへ4400億円投資を加速",
        "4. Google: Gemini 1.5 Proの機能を開発者向けに全開放",
        "5. Meta: 独自LLM Llama-4 学習用H100を10万枚確保",
        "6. Apple: WWDCに向けiOSへの独自生成AI搭載を最終調整",
        "7. Amazon: AIスタートアップAnthropicへ追加出資で攻勢",
        "8. Tesla: AI搭載自動運転FSD v12の予測精度が飛躍的向上",
        "9. AMD: AIサーバーシェア獲得に向けMI300を増産",
        "10. Intel: AI PC向け最新チップの生産ラインをフル稼働"
    ],
    "JP": [
        "1. ソフトバンクG: 孫会長、AI革命に向けた10兆円投資枠を確保",
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
    "2026-04-10": "🇺🇸 米 消費者物価指数(CPI) 発表",
    "2026-04-28": "🇯🇵 日銀結果発表・植田総裁会見",
    "2026-04-30": "🇺🇸 FOMC金利発表・パウエル会見",
    "2026-05-01": "🇺🇸 米 雇用統計 発表",
    "2026-05-20": "🇺🇸 NVIDIA 決算発表予定"
}

# --- 3. CSS ---
st.markdown(f"""
<style>
    .stApp, .block-container {{ background-color: #ffffff !important; color: #000000 !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    
    .header-sticky {{
        position: fixed; top: 0; left: 0; width: 100%; background: #ffffff;
        z-index: 9999; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center;
    }}
    .logo-text {{ font-size: 1.4rem; font-weight: 900; color: #000000; }}
    .block-container {{ padding-top: 3.5rem !important; margin-top: -65px !important; }}

    .price-label {{ font-size: 1.15rem; color: #000000 !important; font-weight: 900 !important; margin-bottom: 5px; }}
    .price-box {{ border: 1px solid #cccccc; padding: 15px; background-color: #fff; text-align: center; border-radius: 4px; }}
    .price-val {{ font-size: 1.8rem; font-weight: 900; line-height: 1.1; color: #000000; }}
    
    .status-line {{ font-size: 1.15rem; font-weight: 900; padding: 12px; border: 1px solid #cccccc; border-left: 10px solid #000000; background-color: #fff; margin-bottom: 15px; }}
    
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; border: 1px solid #cccccc; table-layout: fixed; }}
    .calendar-table th, .calendar-table td {{ border: 1px solid #cccccc; padding: 10px 0; }}
    .today-marker {{ background-color: #000000; color: white !important; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    
    div.stButton > button {{ background-color: #ffffff !important; color: #000000 !important; border: 1px solid #cccccc !important; border-radius: 4px; }}
    div[data-testid="stSegmentedControl"] button {{ border: 1px solid #cccccc !important; color: #999999 !important; background-color: #ffffff !important; }}
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {{ background-color: #000000 !important; color: #ffffff !important; border-color: #000000 !important; }}

    [data-testid="stVerticalBlockBorderWrapper"] {{ border: 1px solid #cccccc !important; padding: 15px; border-radius: 8px; }}
    .item-row {{ font-size: 0.88rem; line-height: 1.6; color: #000000 !important; border-bottom: 1px dotted #cccccc; padding: 8px 0; text-align: left; }}
    .box-header {{ font-size: 1.05rem; font-weight: 900; border-bottom: 2px solid #000000; padding-bottom: 8px; margin-bottom: 12px; }}

    /* サマータイム表記のスタイル */
    .dst-label {{ font-size: 0.75rem; color: #888888 !important; font-weight: normal; margin-left: 8px; }}
</style>
""", unsafe_allow_html=True)

# --- 4. ヘッダー & 市場データ ---
st.markdown(f'<div class="header-sticky"><div class="logo-text">{L["logo"]}</div></div>', unsafe_allow_html=True)

_, col_lang = st.columns([8, 2])
with col_lang:
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
        st.markdown(f'<div class="price-box"><div class="price-label">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800; font-size:0.9rem;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>', unsafe_allow_html=True)

# ニューヨーク時間の取得をサマータイム対応に修正
t_ny = pytz.timezone('America/New_York')
t_jp = pytz.timezone('Asia/Tokyo')
n_ny = datetime.now(t_ny)
n_jp = datetime.now(t_jp)

if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

c1, c2 = st.columns(2, gap="medium")
for col, now, cc, s_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        h_list = us_holidays if cc=="US" else jp_holidays
        is_op = (ot <= now.time() < ct and now.weekday() < 5 and now.date() not in h_list)
        
        target = datetime.combine(now.date(), ot).replace(tzinfo=now.tzinfo)
        if now >= target or now.date() in h_list or now.weekday() >= 5:
            while True:
                target += timedelta(days=1)
                if target.weekday() < 5 and target.date() not in h_list: break
        delta = target - now
        h_c, r_c = divmod(delta.seconds, 3600); m_c, _ = divmod(r_c, 60)
        c_down = f"あと{delta.days}日 {h_c:02d}:{m_c:02d}" if delta.days > 0 else f"あと{h_c}時間{m_c}分"
        
        st_info = "" if is_op else f'<span style="float:right; font-size:0.75rem; color:#666;">{L["next_prefix"]}{c_down}</span>'
        st.markdown(f'<div class="status-line" style="background-color:{"#f0fff4" if is_op else "#fff5f5"};">{L["open"] if is_op else L["closed"]} {st_info}</div>', unsafe_allow_html=True)
        
        dst_label = (L["dst_on"] if now.dst() != timedelta(0) else L["dst_off"]) if cc=="US" else ""
        st.markdown(f'<div style="font-weight:900; font-size:1.3rem; margin-bottom:15px; color:#000000;">{now.strftime("%Y/%m/%d %H:%M:%S")}<span class="dst-label">{dst_label}</span></div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[s_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h_table = f'<table class="calendar-table"><tr>'
        for i, d_name in enumerate([L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]):
            color = "#d71920" if i==0 else ("#0050b3" if i==6 else "#000")
            h_table += f'<th style="color:{color} !important; font-size:0.75rem;">{d_name}</th>'
        h_table += '</tr>'
        for w in cal:
            h_table += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h_table += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    d_color = "#d71920" if (i==0 or curr_d in h_list) else ("#0050b3" if i==6 else "#000")
                    d_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    h_table += f'<td><span style="color:{d_color} !important;">{d_ui}</span></td>'
            h_table += '</tr>'
        st.markdown(h_table + '</table>', unsafe_allow_html=True)

        bc = st.columns(3)
        with bc[0]: st.button(L["prev"], key=f"p_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=1) - timedelta(days=1)).replace(day=1)}))
        with bc[1]: st.button(L["today"], key=f"t_{suffix}", on_click=lambda k=s_key: st.session_state.update({k: date.today().replace(day=1)}))
        with bc[2]: st.button(L["next_m"], key=f"n_{suffix}", on_click=lambda k=s_key, v=view: st.session_state.update({k: (v.replace(day=28) + timedelta(days=5)).replace(day=1)}))

        # イベント枠
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{view.month}月 注目の株式イベント</div>', unsafe_allow_html=True)
            m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and (("🇺🇸" in v or "US" in cc) if cc=="US" else ("🇯🇵" in v or "JP" in cc))]
            st.markdown('<div style="height:150px; overflow-y:auto;">' + ("".join(m_ev) if m_ev else "なし") + '</div>', unsafe_allow_html=True)

        # ニュース枠
        with st.container(border=True):
            st.markdown(f'<div class="box-header">{L["news_title"]}</div>', unsafe_allow_html=True)
            n_items = "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]])
            st.markdown(f'<div style="height:250px; overflow-y:auto;">{n_items}</div>', unsafe_allow_html=True)
