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
        "Winrate vs Champion Level": "champ_level_winrate",
        "Gold & Minions vs Winrate": "gold_minions_winrate",
    }
    selected_analyse = st.selectbox("Kies analyse", list(analyse_opties.keys()))

    alle_tiers = sorted(df_all['tier'].dropna().unique().tolist())
    selected_tiers = st.multiselect("Kies Tier(s)/Rank(s)", options=alle_tiers, default=alle_tiers)

    alle_roles = sorted(df_all['teamPosition'].dropna().unique().tolist()) if 'teamPosition' in df_all.columns else []
    selected_roles = st.multiselect("Kies Role(s)", options=alle_roles, default=alle_roles)

    if selected_analyse == "Winrate vs Champion Level" and 'champLevel' in df_all.columns:
        min_dur = int(df_all['champLevel'].min())
        max_dur = 20
        duration_range = st.slider(
            "Filter op Champion Level",
            min_value=min_dur, max_value=max_dur,
            value=(min_dur, max_dur), step=1
        )
        df_role_filtered = df_all[df_all['tier'].isin(selected_tiers)] if selected_tiers else df_all
        if selected_roles:
            df_role_filtered = df_role_filtered[df_role_filtered['teamPosition'].isin(selected_roles)]
        champ_counts = df_role_filtered['championName'].value_counts()
        alle_champs = sorted(champ_counts[champ_counts >= 10].index.tolist())
        selected_champs = st.multiselect("Filter op Champion(s)", options=alle_champs, default=[])
    else:
        duration_range = None
        selected_champs = []

# --- FILTERING ---
df_filtered = df_all[df_all['tier'].isin(selected_tiers)] if selected_tiers else df_all
if selected_roles and 'teamPosition' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['teamPosition'].isin(selected_roles)]

if not selected_tiers:
    st.warning("Selecteer minimaal een tier in de sidebar om data te bekijken.")
    st.stop()

if 'teamPosition' in df_all.columns and not selected_roles:
    st.warning("Selecteer minimaal een role in de sidebar om data te bekijken.")
    st.stop()

# --- WINRATE ---
if selected_analyse == "Winrate per Champion":
    st.subheader("Winrate per Champion")
    st.info("ℹ️ Alleen champions met minimaal **10 gespeelde games** worden getoond.")
    if 'championName' in df_filtered.columns and 'win' in df_filtered.columns:
        winrate_df = (
            df_filtered.groupby('championName')['win']
            .agg(winrate='mean', games='count')
            .reset_index()
        )
        uitgesloten = winrate_df[winrate_df['games'] < 10].shape[0]
        winrate_df = winrate_df[winrate_df['games'] >= 10]
        winrate_df['winrate'] = (winrate_df['winrate'] * 100).round(1)
        winrate_df = winrate_df.sort_values('winrate', ascending=False)

        if uitgesloten > 0:
            st.caption(f"{uitgesloten} champion(s) uitgesloten wegens minder dan 10 games gespeeld.")

        fig = px.bar(
            winrate_df, x='championName', y='winrate',
            title=f"Winrate per Champion ({', '.join(selected_tiers)})",
            labels={'winrate': 'Winrate (%)', 'championName': 'Champion'},
            color='winrate', color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Kolommen 'championName' of 'win' niet gevonden in de data.")

# --- GAMES GESPEELD ---
elif selected_analyse == "Games gespeeld per Champion":
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

# --- KDA ---
elif selected_analyse == "KDA per Champion":
    st.subheader("KDA per Champion")
    required_cols = {'championName', 'kills', 'deaths', 'assists'}
    if required_cols.issubset(df_filtered.columns):
        kda_df = (
            df_filtered.groupby('championName')[['kills', 'deaths', 'assists']]
            .mean()
            .reset_index()
        )
        kda_df['kda'] = (
            (kda_df['kills'] + kda_df['assists']) / kda_df['deaths'].clip(lower=1)
        ).round(2)
        kda_df = kda_df.sort_values('kda', ascending=False)

        fig = px.bar(
            kda_df, x='championName', y='kda',
            title=f"Gemiddelde KDA per Champion ({', '.join(selected_tiers)})",
            labels={'kda': 'KDA', 'championName': 'Champion'},
            color='kda', color_continuous_scale='Plasma'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detail: gem. Kills / Deaths / Assists")
        detail_df = kda_df[['championName', 'kills', 'deaths', 'assists', 'kda']].copy()
        detail_df[['kills', 'deaths', 'assists']] = detail_df[['kills', 'deaths', 'assists']].round(2)
        detail_df = detail_df.rename(columns={
            'championName': 'Champion', 'kills': 'Gem. Kills',
            'deaths': 'Gem. Deaths', 'assists': 'Gem. Assists', 'kda': 'KDA'
        })
        st.dataframe(detail_df.sort_values('KDA', ascending=False), use_container_width=True, hide_index=True)
    else:
        missing = required_cols - set(df_filtered.columns)
        st.warning(f"Ontbrekende kolommen voor KDA berekening: {', '.join(missing)}")

# --- WINRATE VS CHAMPION LEVEL ---
elif selected_analyse == "Winrate vs Champion Level":
    st.subheader("Winrate vs Champion Level")
    st.info("ℹ️ Alleen champions met minimaal **10 gespeelde games** worden getoond.")
    if 'champLevel' in df_filtered.columns and 'win' in df_filtered.columns:
        df_dur = df_filtered[
            (df_filtered['champLevel'] >= duration_range[0]) &
            (df_filtered['champLevel'] <= duration_range[1])
        ].copy()

        # Altijd: excludeer champions met < 10 games
        champ_counts = df_dur['championName'].value_counts()
        uitgesloten1 = df_dur[~df_dur['championName'].isin(champ_counts[champ_counts >= 10].index)]['championName'].nunique()
        df_dur = df_dur[df_dur['championName'].isin(champ_counts[champ_counts >= 10].index)]

        if uitgesloten1 > 0:
            st.caption(f"{uitgesloten1} champion(s) uitgesloten wegens minder dan 10 games gespeeld.")

        # Filter op geselecteerde champions
        if selected_champs:
            df_dur = df_dur[df_dur['championName'].isin(selected_champs)]

        # Hernoem kolom
        df_dur = df_dur.rename(columns={'champLevel': 'champ_level'})

        if df_dur.empty:
            st.warning("Geen data beschikbaar voor de huidige selectie.")
        else:
            if selected_champs:
                dur_df = (
                    df_dur.groupby(['champ_level', 'championName'])
                    .agg(winrate=('win', 'mean'), games=('win', 'count'))
                    .reset_index()
                )
                dur_df['winrate'] = (dur_df['winrate'] * 100).round(1)
                fig = px.line(
                    dur_df, x='champ_level', y='winrate',
                    color='championName',
                    title="Winrate per Champion Level per Champion",
                    labels={'champ_level': 'Champion Level', 'winrate': 'Winrate (%)', 'championName': 'Champion'},
                    markers=True
                )
            else:
                dur_df = (
                    df_dur.groupby('champ_level')
                    .agg(winrate=('win', 'mean'), games=('win', 'count'))
                    .reset_index()
                )
                dur_df['winrate'] = (dur_df['winrate'] * 100).round(1)
                fig = px.line(
                    dur_df, x='champ_level', y='winrate',
                    title=f"Winrate per Champion Level ({', '.join(selected_tiers)})",
                    labels={'champ_level': 'Champion Level', 'winrate': 'Winrate (%)'},
                    markers=True
                )
                fig.update_traces(line_color='royalblue')

            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Gebaseerd op {len(df_dur):,} games met champion level tussen {duration_range[0]} en {duration_range[1]}.")
    else:
        st.warning("Kolom 'champLevel' of 'win' niet gevonden in de data.")

# --- GOLD & MINIONS VS WINRATE ---
elif selected_analyse == "Gold & Minions vs Winrate":
    st.subheader("Gold & Minions vs Winrate per Champion")
    required_cols = {'championName', 'goldEarned', 'totalMinionsKilled', 'win'}
    if required_cols.issubset(df_filtered.columns):

        # Maak gold buckets
        bucket_size = st.select_slider(
            "Gold bucket grootte",
            options=[500, 1000, 2000, 3000],
            value=1000
        )

        # Champion filter
        champ_counts_gold = df_filtered['championName'].value_counts()
        champs_gold = sorted(champ_counts_gold[champ_counts_gold >= 10].index.tolist())
        selected_champs_gold = st.multiselect(
            "Filter op Champion(s)",
            options=champs_gold,
            default=[]
        )

        df_gold = df_filtered.copy()
        if selected_champs_gold:
            df_gold = df_gold[df_gold['championName'].isin(selected_champs_gold)]

        df_gold['gold_bucket'] = (df_gold['goldEarned'] // bucket_size * bucket_size).astype(int)
        df_gold['gold_bucket_label'] = df_gold['gold_bucket'].apply(
            lambda x: f"{x//1000}k-{(x+bucket_size)//1000}k"
        )

        if selected_champs_gold:
            bucket_df = (
                df_gold.groupby(['gold_bucket', 'championName'])
                .agg(
                    winrate=('win', 'mean'),
                    games=('win', 'count'),
                    gold_label=('gold_bucket_label', 'first')
                )
                .reset_index()
                .sort_values('gold_bucket')
            )
            bucket_df['winrate'] = (bucket_df['winrate'] * 100).round(1)
            uitgesloten2 = bucket_df[bucket_df['games'] < 10].shape[0]
            bucket_df = bucket_df[bucket_df['games'] >= 10]

            if uitgesloten2 > 0:
                st.caption(f"{uitgesloten2} gold bucket(s) uitgesloten wegens minder dan 10 games.")

            fig = px.line(
                bucket_df, x='gold_label', y='winrate',
                color='championName',
                hover_data={'games': True},
                title=f"Winrate per Gold Bucket per Champion ({', '.join(selected_tiers)})",
                labels={'gold_label': 'Gold Earned', 'winrate': 'Winrate (%)', 'championName': 'Champion'},
                markers=True
            )
        else:
            bucket_df = (
                df_gold.groupby('gold_bucket')
                .agg(
                    winrate=('win', 'mean'),
                    games=('win', 'count'),
                    minions=('totalMinionsKilled', 'mean'),
                    gold_label=('gold_bucket_label', 'first')
                )
                .reset_index()
                .sort_values('gold_bucket')
            )
            bucket_df['winrate'] = (bucket_df['winrate'] * 100).round(1)
            bucket_df['minions'] = bucket_df['minions'].round(1)
            uitgesloten2 = bucket_df[bucket_df['games'] < 10].shape[0]
            bucket_df = bucket_df[bucket_df['games'] >= 10]

            if uitgesloten2 > 0:
                st.caption(f"{uitgesloten2} gold bucket(s) uitgesloten wegens minder dan 10 games.")

            fig = px.bar(
                bucket_df, x='gold_label', y='winrate',
                color='winrate',
                hover_data={'games': True, 'minions': True},
                title=f"Winrate per Gold Bucket ({', '.join(selected_tiers)})",
                labels={'gold_label': 'Gold Earned', 'winrate': 'Winrate (%)'},
                color_continuous_scale='RdYlGn'
            )

        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
        st.plotly_chart(fig, use_container_width=True)
        st.info("ℹ️ Hover over een bucket om het aantal games en gemiddeld aantal minions te zien.")

    else:
        missing = required_cols - set(df_filtered.columns)
        st.warning(f"Ontbrekende kolommen: {', '.join(missing)}")