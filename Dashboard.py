import streamlit as st
import pandas as pd
import numpy as np

st.title("League data vergeijking")

tab1, tab2, tab3 = st.tabs(["Tab 1, Tab 2, Tab 3"])

st.slider(min_value='0', max_value='2', step=1)