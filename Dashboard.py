import streamlit as st
from PIL import Image

st.title("League of Legends High Elo Dashboard")

tier = st.selectbox("Selecteer tier", ["Challenger", "Master", "Grandmaster"])
role = st.selectbox("Selecteer rol voor counterpick heatmap", ["TOP", "JUNGLE", "MID", "BOT", "SUPPORT"])

# Winrate plot
winrate_img = Image.open(f"plots/winrate_{tier}.png")
st.image(winrate_img, caption=f"Winrate per Champion - {tier}")

# Counterpick heatmap
counter_img_path = f"plots/counterpick_{tier}_{role}.png"
try:
    counter_img = Image.open(counter_img_path)
    st.image(counter_img, caption=f"Counterpick Winrate - {role} - {tier}")
except FileNotFoundError:
    st.warning("Geen counterpick data beschikbaar voor deze selectie")

