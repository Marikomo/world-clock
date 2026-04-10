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
st.set_page_config(page_title="Market Analytics", layout="wide")

L_MAP = {
    "JP": {
        "us_m": "🇺🇸 米国市場", "jp_m": "🇯🇵 日本市場", "open": "開場中", "closed": "閉場中", "holiday": "休場",
        "next": "次回の開場まで: ", "sun": "日", "mon": "月", "tue": "火", "wed": "水", "thu": "木", "fri": "金", "sat": "土",
        "prev": "◀ 前月", "today": "今月", "next_m": "次月 ▶", "news_title": "🚀 今週のAI株式ニュース(10)", "event_title": "📅 注目の株式イベント"
    },
    "EN": {
        "us_m": "🇺🇸 US Market", "jp_m": "🇯🇵 JP Market", "open": "OPEN", "closed": "CLOSED", "holiday": "HOLIDAY",
        "next": "Next Open in: ", "sun": "SUN", "mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI", "sat": "SAT",
        "prev": "◀ Prev", "today": "Now", "next_m": "Next ▶", "news_title": "🚀 Weekly AI News (10)", "event_title": "📅 Monthly Events"
    }
}
L = L_MAP[st.session_state.lang]

# --- 2. CSS（枠の中身を確実に出し、スクロールさせる） ---
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 0rem !important; margin-top: -65px !important; }}
    .absolute-row {{ display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }}
    .hover-tip {{ position: relative; flex: 1; cursor: pointer; }}
    .price-box {{ border: 1px solid #ddd; padding: 12px 2px; background-color: #fff; text-align: center; }}
    .price-val {{ font-size: 1.6rem; font-weight: 900; line-height: 1.1; color: #111; }} 
    .hover-text {{
        visibility: hidden; width: 300px; background-color: rgba(17, 17, 17, 0.98); color: #fff;
        text-align: left; border-radius: 8px; padding: 15px; position: absolute;
        z-index: 9999 !important; bottom: 110%; left: 50%; transform: translateX(-50%);
        opacity: 0; transition: opacity 0.3s ease-in-out; font-size: 0.85rem; pointer-events: none;
    }}
    .hover-tip:hover .hover-text {{ visibility: visible; opacity: 1; }}
    .status-line {{ font-size: 1.2rem; font-weight: 900; padding: 12px; border: 1px solid #ddd; border-left: 8px solid #111; background-color: #fff; margin-bottom: 10px; }}
    .calendar-table {{ width: 100%; border-collapse: collapse; text-align: center; margin-top: 5px; }}
    .today-marker {{ background-color: #111; color: white; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; font-weight: 800; border-radius: 4px; }}
    .event-mark {{ text-decoration: underline wavy #d71920; text-underline-offset: 4px; }}
    
    /* リストボックスのデザイン改善 */
    .list-wrapper {{ 
        border: 1px solid #eee; padding: 15px; margin-top: 15px; 
        border-radius: 6px; background-color: #fdfdfd; height: 350px; 
        overflow-y: auto; display: block !important;
    }}
    .box-header {{ 
        font-size: 1rem; font-weight: 900; border-bottom: 2px solid #111; 
        padding-bottom: 8px; margin-bottom: 12px; color: #111;
        position: sticky; top: -15px; background: #fdfdfd; z-index: 10;
    }}
    .item-row {{ font-size: 0.85rem; line-height: 1.6; color: #333; margin-bottom: 8px; border-bottom: 1px dotted #ccc; padding-bottom: 4px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. イベント・ニュースデータ（各10件） ---
EVENTS_DATA = {
    "2026-04-10": "🇺🇸 米 CPI(消費者物価指数)", "2026-04-11": "🇺🇸 米 PPI(生産者物価指数)",
    "2026-04-15": "🇺🇸 大手金融機関決算発表開始", "2026-04-20": "🇺🇸 半導体セクター主要決算",
    "2026-04-27": "🇯🇵 日銀決定会合(Day1)", "2026-04-28": "🇯🇵 日銀発表・植田総裁会見",
    "2026-04-29": "🇺🇸 FOMC(Day1)", "2026-04-30": "🇺🇸 FOMC金利発表・パウエル会見",
    "2026-05-01": "🇺🇸 米 雇用統計発表", "2026-05-03": "🇯🇵 憲法記念日(休場)",
    "2026-05-04": "🇯🇵 みどりの日(休場)", "2026-05-05": "🇯🇵 こどもの日(休場)",
    "2026-05-10": "🇺🇸 CPI発表予定", "2026-05-15": "🇺🇸 米 小売売上高",
    "2026-05-20": "🇺🇸 NVIDIA 決算発表予定(推定)", "2026-11-03": "🇺🇸 米 中間選挙(投開票)"
}

AI_NEWS_DATA = {
    "US": [
        "1. NVIDIA: Blackwell量産で供給不足継続見通し", "2. OpenAI: 次期大型モデルのテスト段階入りか", 
        "3. Microsoft: 日本国内AIインフラに4400億円投資", "4. Google: Gemini 1.5 Pro 全ユーザーに公開", 
        "5. Meta: Llama-4 学習用にH100を10万枚確保", "6. Apple: WWDCでiPhone向け新AI発表の噂",
        "7. Amazon: 自社製AIチップTrainium 2の評価向上", "8. Tesla: AI搭載人型ロボット最新映像を公開",
        "9. AMD: AIチップ市場シェア20%獲得に向け加速", "10. Palantir: 米軍とのAI分析契約を大型更新"
    ],
    "JP": [
        "1. SBG: 孫会長 AI革命に10兆円投資を示唆", "2. さくらネット: GPUクラウド予約が年内完売", 
        "3. NTT: 軽量LLM『tsuzumi』導入が50社突破", "4. 富士通: 創薬AI分野で世界トップ級精度達成", 
        "5. NEC: 官公庁向け専用AI基盤の受注を拡大", "6. LINEヤフー: 検索体験にAI生成回答を導入",
        "7. 三菱UFJ: 行員1万人規模でAI活用を本格化", "8. トヨタ: AI活用のレベル4自動運転公道試験",
        "9. 楽天: 楽天モバイルにAI応対システムを全導入", "10. 日本政府: AI計算資源確保へ追加の巨額支援"
    ]
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

# --- 4. メイン ---
t_ny, t_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
n_ny, n_jp = datetime.now(t_ny), datetime.now(t_jp)
if 'v_us' not in st.session_state: st.session_state.v_us = n_ny.date().replace(day=1)
if 'v_jp' not in st.session_state: st.session_state.v_jp = n_jp.date().replace(day=1)

# 価格
st.markdown('<div class="absolute-row">' + "".join([f'<div class="price-box" style="flex:1;"><div class="price-label">{k}</div><div class="price-val">{v["val"]:,.1f}</div><div style="color:{"#d71920" if v["diff"]>=0 else "#0050b3"}; font-weight:800;">{"▲" if v["diff"]>=0 else "▼"}{abs(v["diff"]):.1f}</div></div>' for k,v in prices.items()]) + '</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2, gap="large")
for col, now, cc, state_key, suffix, title in [(c1, n_ny, "US", "v_us", "us", L["us_m"]), (c2, n_jp, "JP", "v_jp", "jp", L["jp_m"])]:
    with col:
        st.header(title)
        # ステータス表示
        ot, ct = (time(9, 30), time(16, 0)) if cc=="US" else (time(9, 0), time(15, 0))
        is_op = (ot <= now.time() < ct and now.weekday() < 5)
        st_txt = L["open"] if is_op else L["closed"]
        st.markdown(f'<div class="status-line" style="background-color:{"#e6ffed" if is_op else "#fff1f0"};">{st_txt} <span style="float:right; font-size:0.8rem; color:#666;">Next Open: 09:30</span></div>', unsafe_allow_html=True)
        dst = f' <span style="color:#d71920; font-size:0.75rem;">DST ON</span>' if now.dst() != timedelta(0) else ""
        st.markdown(f'<div style="font-weight:900;">{now.strftime("%H:%M:%S")}{dst if cc=="US" else ""} ({now.strftime("%Y/%m/%d")})</div>', unsafe_allow_html=True)
        
        # カレンダー
        view = st.session_state[state_key]
        cal = calendar.monthcalendar(view.year, view.month)
        h = f'<table class="calendar-table"><tr>' + "".join([f'<th>{d}</th>' for d in [L["sun"],L["mon"],L["tue"],L["wed"],L["thu"],L["fri"],L["sat"]]]) + '</tr>'
        for w in cal:
            h += '<tr>'
            for i, d in enumerate(w):
                if d == 0: h += '<td></td>'
                else:
                    curr_d = date(view.year, view.month, d)
                    curr_s = curr_d.strftime("%Y-%m-%d")
                    ev = EVENTS_DATA.get(curr_s, "")
                    cls = "holiday-red" if (i==0 or i==6) else ""
                    day_ui = f'<span class="today-marker">{d}</span>' if curr_d == now.date() else str(d)
                    if ev: h += f'<td><div class="hover-tip"><span class="{cls} event-mark">{day_ui}</span><span class="hover-text"><b>{L["event_title"]}</b><br>{ev}</span></div></td>'
                    else: h += f'<td><span class="{cls}">{day_ui}</span></td>'
            h += '</tr>'
        st.markdown(h + '</table>', unsafe_allow_html=True)

        # カレンダー操作（下に移動）
        bc = st.columns(3)
        with bc[0]: 
            if st.button(L["prev"], key=f"p_{suffix}"):
                m, y = (view.month-1, view.year) if view.month > 1 else (12, view.year-1); st.session_state[state_key] = date(y, m, 1); st.rerun()
        with bc[1]:
            if st.button(L["today"], key=f"t_{suffix}"): st.session_state[state_key] = now.date().replace(day=1); st.rerun()
        with bc[2]:
            if st.button(L["next_m"], key=f"n_{suffix}"):
                m, y = (view.month+1, view.year) if view.month < 12 else (1, view.year+1); st.session_state[state_key] = date(y, m, 1); st.rerun()

        # 月間イベント（カレンダー月連動・10件）
        ev_box = f'<div class="list-wrapper"><div class="box-header">{view.month}月 {L["event_title"]}</div>'
        m_ev = [f'<div class="item-row"><b>{k[8:]}日</b>: {v}</div>' for k,v in sorted(EVENTS_DATA.items()) if k.startswith(view.strftime("%Y-%m")) and ((cc=="US" and "🇺🇸" in v) or (cc=="JP" and "🇯🇵" in v))]
        ev_box += "".join(m_ev) if m_ev else '<div class="item-row">なし</div>'
        st.markdown(ev_box + '</div>', unsafe_allow_html=True)

        # 今週のAIニュース（10件）
        news_box = f'<div class="list-wrapper"><div class="box-header">{L["news_title"]}</div>'
        news_box += "".join([f'<div class="item-row">{n}</div>' for n in AI_NEWS_DATA[cc]])
        st.markdown(news_box + '</div>', unsafe_allow_html=True)
