import streamlit as st
import pandas as pd
import numpy as np

st.title("League data vergeijking")

tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

st.slider(min_value=0.0, max_value=2.0, step=0.1)

with tab1: 
    st.write('Tab 1')

with tab2:
    st.write('Tab 2')

with tab3:
    st.write('Tab 3')

