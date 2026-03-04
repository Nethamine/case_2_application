import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

df_chal = pd.read_csv("challenger_matches_useful.csv")
df_gm = pd.read_csv("grandmaster_matches_useful.csv")
df_m = pd.read_csv("master_matches_useful.csv")

df_all = pd.concat([df_chal,df_gm, df_m], ignore_index=True)

# CODE VANAF HIER



st.title("League data vergeijking")


with st.sidebar:
    st.header("Filters")
    selected_atribute = st.selectbox("Kies Rank/Tier", df_all['tier'].unique())

tab1, tab2, tab3 = st.tabs(["Winrate vs Champ ", "Rank vs Champ gespeelt", "Tab 3"])

with tab1: 
    st.write('Tab 1')

with tab2:
    st.write('Tab 22')

with tab3:
    st.write('Tab 3')

