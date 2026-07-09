# -*- coding: utf-8 -*-
"""
⚠️ 注意：当前项目已统一通过 app.py 启动，本文件仅保留兼容用途。
请在终端中运行以下指令启动系统：
streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="AIZS｜兼容入口",
    page_icon="🏫",
    layout="wide"
)

st.warning("⚠️ **当前项目已统一通过 app.py 启动。本文件仅保留兼容用途。**")
st.info("💡 请在终端中运行以下指令重新启动系统：\n`streamlit run app.py`")
