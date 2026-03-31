import streamlit as st
from datetime import datetime, timedelta, date
import pytz
import calendar
import holidays
from streamlit_autorefresh import st_autorefresh

# 1秒ごとに更新（時計の秒数と、日付が変わった際の自動更新を担保）
st_autorefresh(interval=1000, key="datetimereload")

st.set_page_config(page_title="日/米 株式市場リアルタイムカレンダー", layout="wide")

# --- セッション状態の初期化 ---
if 'view_date_us' not in st.session_state:
    st.session_state.view_date_us = datetime.now(pytz.timezone('America/New_York')).date().replace(day=1)
if 'view_date_jp' not in st.session_state:
    st.session_state.view_date_jp = datetime.now(pytz.timezone('Asia/Tokyo')).date().replace(day=1)

# --- スタイル設定 ---
st.markdown("""
<style>
    body { color: #444; }
    header a { display: none !important; } 
    .stHeaderActionElements { display: none !important; }

    /* カレンダーテーブル */
    .calendar-table {
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        margin-bottom: 20px;
        color: #444;
    }
    .calendar-table tr { height: 40px; }
    .calendar-table td, .calendar-table th { vertical-align: middle; padding: 0; position: relative; }
    
    .today-marker {
        background-color: #ff4b4b;
        color: white;
        border-radius: 0%; 
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px; height: 32px; font-weight: bold;
    }
    
    .holiday-red { color: #ff4b4b; font-weight: bold; }
    .calendar-table th:first-child, .calendar-table th:last-child { color: #ff4b4b; }
    
    /* ニュースボックス（左右の高さを統一） */
    .news-box {
        border: 1px solid #ddd;
        padding: 15px;
        margin-top: 20px;
        color: #444;
        background-color: #fff;
        min-height: 280px;
        display: flex;
        flex-direction: column;
    }
    .news-title {
        font-weight: bold;
        font-size: 1.0rem;
        margin-bottom: 5px;
        line-height: 1.4;
    }
    .news-update-time {
        font-size: 0.75rem;
        color: #888;
        margin-bottom: 12px;
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
    }
    .news-list {
        margin: 0;
        padding-left: 20px;
        font-size: 0.9rem;
        line-height: 1.8;
    }

    .market-status {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 10px;
        border-radius: 0px !important;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        color: #444;
    }
    
    .date-time-row {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex; gap: 10px; align-items: center; color: #444;
    }
    .tz-label { font-size: 0.8rem; color: #666; font-weight: normal; margin-left: 5px; }

    .stButton > button {
        border-radius: 0px !important;
        border: 1px solid #ddd !important;
        background-color: white; color: #444; font-weight: bold;
        width: 100%; height: 40px;
    }
    [data-testid="stHorizontalBlock"] div:nth-child(1) button { text-align: left; padding-left: 10px; }
    [data-testid="stHorizontalBlock"] div:nth-child(5) button { text-align: right; padding-right: 10px; }

    [data-testid="column"]:first-of-type { padding-right: 60px !important; }
    [data-testid="column"]:last-of-type { padding-left: 60px !important; }
</style>
""", unsafe_allow_html=True)

# 毎日AM5:00に更新される想定のニュース生成ロジック
def get_daily_news(market, current_datetime):
    # market: "US" or "JP"
    # 現在の日付に基づいたダミーニュース（実際はAPI等で最新情報を取得する箇所）
    day_str = current_datetime.strftime("%Y/%m/%d")
    
    if market == "US":
        return [
            f"【米株】FRB議長、インフレ抑制への自信を強調（{day_str}）",
            "【米株】大手テック企業のAI投資が利益率に与える影響を精査",
            "【政治】米議会、新たな経済支援策の枠組みで基本合意",
            "【経済】製造業景況指数が予想を上回り、景気の底堅さを証明",
            "【雇用】失業率の微増が利下げ期待を再燃させる展開へ"
        ]
    else:
        return [
            f"【日本株】円安進行に伴う製造業の収益改善期待（{day_str}）",
            "【日本株】日銀審議委員による金融緩和修正の是非を巡る発言",
            "【経済】消費支出の回復鈍化が内需株の重しとなる可能性",
            "【政治】政府によるスタートアップ支援策の拡充が市場の刺激に",
            "【東証】資本効率の改善を表明した銘柄への選別買いが継続"
        ]

def draw_calendar_area(now_full, country_code, state_key, country_tz):
    view_date = st.session_state[state_key]
    st.markdown(f"### {view_date.strftime('%Y年 %m月')}")
    target_holidays = holidays.CountryHoliday(country_code)
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    
    html = '<table class="calendar-table"><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr>'
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                html += '<td></td>'
            else:
                curr_date = date(view_date.year, view_date.month, day)
                h_name = target_holidays.get(curr_date)
                is_weekend = (i == 0 or i == 6)
                if curr_date == now_full.date():
                    html += f'<td><span class="today-marker">{day}</span></td>'
                elif h_name or is_weekend:
                    html += f'<td><span class="holiday-red">{day}</span></td>'
                else:
                    html += f'<td>{day}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 2, 1.2, 1.2])
    with c1:
        if st.button("◀", key=f"prev_{state_key}"): move_month(state_key, -1)
    with c3:
        if st.button("今月", key=f"today_{state_key}"): reset_month(state_key, country_tz)
    with c5:
        if st.button("▶", key=f"next_{state_key}"): move_month(state_key, 1)

def move_month(key, delta):
    current = st.session_state[key]
    new_month = current.month + delta
    new_year = current.year
    if new_month > 12: new_month = 1; new_year += 1
    elif new_month < 1: new_month = 12; new_year -= 1
    st.session_state[key] = date(new_year, new_month, 1)

def reset_month(key, country_tz):
    st.session_state[key] = datetime.now(pytz.timezone(country_tz)).date().replace(day=1)

def get_market_info(now, market_type):
    cc = "US" if market_type == "US" else "JP"
    th = holidays.CountryHoliday(cc)
    is_h = now.date() in th
    if market_type == "US":
        ot, ct = now.replace(hour=9, minute=30, second=0), now.replace(hour=16, minute=0, second=0)
    else:
        ot, ct = now.replace(hour=9, minute=0, second=0), now.replace(hour=15, minute=0, second=0)
    is_wd = 0 <= now.weekday() <= 4
    if not is_wd or is_h:
        r = "週末休み" if not is_wd else f"祝日休場 ({th.get(now.date())})"
        return f"😴 CLOSED ({r})", "#f5f5f5"
    if now < ot:
        d = ot - now
        return f"⏳ CLOSED (開場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#fffbe6"
    elif ot <= now < ct:
        d = ct - now
        return f"🟢 OPEN (閉場まで: {d.seconds//3600}:{(d.seconds//60)%60:02d}:{d.seconds%60:02d})", "#e6ffed"
    else:
        return "🔴 CLOSED (本日の取引終了)", "#fff1f0"

# メインレイアウト
st.title("📊 日/米 株式市場リアルタイムカレンダー")
col1, col2 = st.columns(2, gap="large")
tz_ny, tz_jp = pytz.timezone('America/New_York'), pytz.timezone('Asia/Tokyo')
now_ny, now_jp = datetime.now(tz_ny), datetime.now(tz_jp)

with col1:
    st.header("🇺🇸 米国株式市場")
    is_dst = now_ny.dst() != timedelta(0)
    dst_label = "（サマータイム中）" if is_dst else "（非サマータイム：標準時）"
    st.markdown(f'<div class="date-time-row"><span>{now_ny.strftime("%Y/%m/%d %H:%M:%S")}</span><span class="tz-label">{dst_label}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_ny, "US")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_ny, "US", "view_date_us", "America/New_York")
    
    # ニュースセクション
    news_list = get_daily_news("US", now_ny)
    st.markdown(f"""
    <div class="news-box">
        <div class="news-title">AIが選ぶ今週の政治経済ニュース10（{now_ny.strftime('%Y年%m月%d日')}）</div>
        <div class="news-update-time">（最終更新：{now_ny.strftime('%Y年%m月%d日 %H時%M分')}）</div>
        <ul class="news-list">
            {''.join([f'<li>{item}</li>' for item in news_list])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.header("🇯🇵 日本株式市場")
    st.markdown(f'<div class="date-time-row"><span>{now_jp.strftime("%Y/%m/%d %H:%M:%S")}</span></div>', unsafe_allow_html=True)
    status, color = get_market_info(now_jp, "JP")
    st.markdown(f'<div class="market-status" style="background-color: {color};">{status}</div>', unsafe_allow_html=True)
    draw_calendar_area(now_jp, "JP", "view_date_jp", "Asia/Tokyo")
    
    # ニュースセクション
    news_list = get_daily_news("JP", now_jp)
    st.markdown(f"""
    <div class="news-box">
        <div class="news-title">AIが選ぶ今週の政治経済ニュース10（{now_jp.strftime('%Y年%m月%d日')}）</div>
        <div class="news-update-time">（最終更新：{now_jp.strftime('%Y年%m月%d日 %H時%M分')}）</div>
        <ul class="news-list">
            {''.join([f'<li>{item}</li>' for item in news_list])}
        </ul>
    </div>
    """, unsafe_allow_html=True)
