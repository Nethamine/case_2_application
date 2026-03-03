import streamlit as st
import pandas as pd
import numpy as np

st.title("League data vergeijking")

tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1: 
    st.write('Tab 1')

with tab2:
    st.write('Tab 2')

with tab3:
    st.write('Tab 3')

