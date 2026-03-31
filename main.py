import streamlit as st
from datetime import datetime
import pytz

st.title("🌍 My First App")
now_tx = datetime.now(pytz.timezone('US/Central')).strftime('%H:%M:%S')
st.metric("Texas Time", now_tx)
