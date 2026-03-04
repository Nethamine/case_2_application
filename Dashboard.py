import streamlit as st
import pandas as pd
import numpy as np
from plot import save_winrate_plot, save_counterpick_heatmap
st.title("League data vergeijking")
df = pd.read_csv('challenger_matches_useful.csv')
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    path = save_winrate_plot(df, tier)
    st.image(path)

with tab2:
    path = save_counterpick_heatmap(df, tier, role)
    if path:
        st.image(path)

with tab3:
    st.write('Tab 3')

