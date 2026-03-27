import streamlit as st
from mig_page import render_mig_page

st.set_page_config(
    page_title="MIG / AMMO Content App",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("MIG / AMMO Content App")
st.caption("Tvorba CREATE CSV, promptů a FILLED CSV pro AMMO by MIG.")

render_mig_page()