import streamlit as st
import pandas as pd
import plotly.express as px

df_chal = pd.read_csv("challenger_matches_useful.csv")
df_gm = pd.read_csv("grandmaster_matches_useful.csv")
df_m = pd.read_csv("master_matches_useful.csv")
df_all = pd.concat([df_chal, df_gm, df_m], ignore_index=True)

# --- SIDEBAR ---
st.title("League Data Dashboard")

with st.sidebar:
    st.header("Filters")
    analyse_opties = {
        "Winrate per Champion": "winrate",
        "Games gespeeld per Champion": "games_played",
        "KDA per Champion": "kda",
    }
    selected_analyse = st.selectbox("Kies analyse", list(analyse_opties.keys()))

    alle_tiers = sorted(df_all['tier'].dropna().unique().tolist())
    selected_tiers = st.multiselect(
        "Kies Tier(s)/Rank(s)",
        options=alle_tiers,
        default=alle_tiers
    )

# Filter df op geselecteerde tiers
df_filtered = df_all[df_all['tier'].isin(selected_tiers)] if selected_tiers else df_all

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["Winrate per Champion", "Games gespeeld per Champion", "KDA per Champion"])

if not selected_tiers:
    st.warning("⚠️ Selecteer minimaal één tier in de sidebar om data te bekijken.")
    st.stop()

with tab1:
    if selected_analyse == "Winrate per Champion":
        st.subheader("Winrate per Champion")
        if 'championName' in df_filtered.columns and 'win' in df_filtered.columns:
            winrate_df = (
                df_filtered.groupby('championName')['win']
                .mean()
                .reset_index()
                .rename(columns={'win': 'winrate'})
                .sort_values('winrate', ascending=False)
            )
            winrate_df['winrate'] = (winrate_df['winrate'] * 100).round(1)
            fig = px.bar(
                winrate_df, x='championName', y='winrate',
                title=f"Winrate per Champion ({', '.join(selected_tiers)})",
                labels={'winrate': 'Winrate (%)', 'championName': 'Champion'},
                color='winrate', color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kolommen 'championName' of 'win' niet gevonden in de data.")
    else:
        st.info("Selecteer 'Winrate per Champion' in de sidebar om deze tab te gebruiken.")

with tab2:
    if selected_analyse == "Games gespeeld per Champion":
        st.subheader("Games gespeeld per Champion")
        if 'championName' in df_filtered.columns:
            games_df = (
                df_filtered.groupby('championName')
                .size()
                .reset_index(name='games_played')
                .sort_values('games_played', ascending=False)
            )
            fig = px.bar(
                games_df, x='championName', y='games_played',
                title=f"Games gespeeld per Champion ({', '.join(selected_tiers)})",
                labels={'games_played': 'Aantal Games', 'championName': 'Champion'},
                color='games_played', color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kolom 'championName' niet gevonden in de data.")
    else:
        st.info("Selecteer 'Games gespeeld per Champion' in de sidebar om deze tab te gebruiken.")

with tab3:
    if selected_analyse == "KDA per Champion":
        st.subheader("KDA per Champion")
        required_cols = {'championName', 'kills', 'deaths', 'assists'}
        if required_cols.issubset(df_filtered.columns):
            kda_df = (
                df_filtered.groupby('championName')[['kills', 'deaths', 'assists']]
                .mean()
                .reset_index()
            )
            # KDA formule: (Kills + Assists) / max(Deaths, 1)
            kda_df['kda'] = (
                (kda_df['kills'] + kda_df['assists']) / kda_df['deaths'].clip(lower=1)
            ).round(2)
            kda_df = kda_df.sort_values('kda', ascending=False)

            # KDA bar chart
            fig = px.bar(
                kda_df, x='championName', y='kda',
                title=f"Gemiddelde KDA per Champion ({', '.join(selected_tiers)})",
                labels={'kda': 'KDA', 'championName': 'Champion'},
                color='kda', color_continuous_scale='Plasma'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Detail tabel: gem. kills / deaths / assists + KDA
            st.subheader("Detail: gem. Kills / Deaths / Assists")
            detail_df = kda_df[['championName', 'kills', 'deaths', 'assists', 'kda']].copy()
            detail_df[['kills', 'deaths', 'assists']] = detail_df[['kills', 'deaths', 'assists']].round(2)
            detail_df = detail_df.rename(columns={
                'championName': 'Champion',
                'kills': 'Gem. Kills',
                'deaths': 'Gem. Deaths',
                'assists': 'Gem. Assists',
                'kda': 'KDA'
            })
            st.dataframe(detail_df, use_container_width=True, hide_index=True)
        else:
            missing = required_cols - set(df_filtered.columns)
            st.warning(f"Ontbrekende kolommen voor KDA berekening: {', '.join(missing)}")
    else:
        st.info("Selecteer 'KDA per Champion' in de sidebar om deze tab te gebruiken.")