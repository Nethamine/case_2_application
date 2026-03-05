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
        "Vision & Winrate Analyse": "vision_winrate",
        "Counterpick Analyse": "counterpick",
    }
    selected_analyse = st.selectbox("Kies analyse", list(analyse_opties.keys()))

    alle_tiers = sorted(df_all['tier'].dropna().unique().tolist())
    selected_tiers = st.multiselect("Kies Tier(s)/Rank(s)", options=alle_tiers, default=alle_tiers)

    if selected_analyse != "Counterpick Analyse":
        alle_roles = sorted(df_all['teamPosition'].dropna().unique().tolist()) if 'teamPosition' in df_all.columns else []
        selected_roles = st.multiselect("Kies Role(s)", options=alle_roles, default=alle_roles)
    else:
        selected_roles = alle_roles = sorted(df_all['teamPosition'].dropna().unique().tolist())

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

elif selected_analyse == "Vision & Winrate Analyse":
    st.subheader("Vision & Winrate Analyse")
    st.info("ℹ️ Vergelijk hoe verschillende vision metrics samenhangen met winrate.")

    # --- CHECKBOXES ---
    st.markdown("**Kies metrics om te vergelijken:**")
    col1, col2 = st.columns(2)
    with col1:
        show_vision = st.checkbox("Vision Score (totaal)", value=True)
        show_wards_placed = st.checkbox("Wards Placed", value=False)
    with col2:
        show_wards_killed = st.checkbox("Wards Killed", value=False)
        show_detector = st.checkbox("Control Wards Placed", value=False)

    selected_metrics = []
    if show_vision:
        selected_metrics.append(('visionScore', 'Vision Score'))
    if show_wards_placed:
        selected_metrics.append(('wardsPlaced', 'Wards Placed'))
    if show_wards_killed:
        selected_metrics.append(('wardsKilled', 'Wards Killed'))
    if show_detector:
        selected_metrics.append(('detectorWardsPlaced', 'Control Wards Placed'))

    if not selected_metrics:
        st.warning("Selecteer minimaal één metric om de grafiek te tonen.")
        st.stop()

    # --- BUCKET GROOTTE ---
    bucket_size = st.select_slider(
        "Bucket grootte (hogere waarde = minder maar stabielere datapunten)",
        options=[1, 2, 3, 5, 10],
        value=3
    )
    min_games = st.slider("Minimaal aantal games per bucket", min_value=5, max_value=50, value=10, step=5)

    # --- DATA BOUWEN ---
    required_cols = {'visionScore', 'wardsPlaced', 'wardsKilled', 'detectorWardsPlaced', 'win'}
    if not required_cols.issubset(df_filtered.columns):
        missing = required_cols - set(df_filtered.columns)
        st.warning(f"Ontbrekende kolommen: {', '.join(missing)}")
        st.stop()

    # Bouw een lijn per metric
    fig = px.line(title=f"Vision Metrics vs Winrate ({', '.join(selected_tiers)})")
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")

    for col, label in selected_metrics:
        df_metric = df_filtered[[col, 'win']].copy()
        df_metric['bucket'] = (df_metric[col] // bucket_size * bucket_size).astype(int)

        bucket_df = (
            df_metric.groupby('bucket')['win']
            .agg(winrate='mean', games='count')
            .reset_index()
        )
        bucket_df = bucket_df[bucket_df['games'] >= min_games]
        bucket_df['winrate'] = (bucket_df['winrate'] * 100).round(1)

        fig.add_scatter(
            x=bucket_df['bucket'],
            y=bucket_df['winrate'],
            mode='lines+markers',
            name=label,
            hovertemplate=f"<b>{label}</b><br>Waarde: %{{x}}<br>Winrate: %{{y}}%<br>Games: %{{customdata}}<extra></extra>",
            customdata=bucket_df['games']
        )

    fig.update_layout(
        xaxis_title="Metric waarde (gebucketed)",
        yaxis_title="Winrate (%)",
        yaxis_range=[30, 70],
        legend_title="Metric",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- DETAIL TABEL ---
    st.subheader("Gemiddelden per metric: Winnaars vs Verliezers")
    detail_rows = []
    for col, label in selected_metrics:
        winners = df_filtered[df_filtered['win'] == 1][col].mean()
        losers = df_filtered[df_filtered['win'] == 0][col].mean()
        detail_rows.append({
            'Metric': label,
            'Gem. Winnaars': round(winners, 2),
            'Gem. Verliezers': round(losers, 2),
            'Verschil': round(winners - losers, 2)
        })

    detail_df = pd.DataFrame(detail_rows).sort_values('Verschil', ascending=False)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    st.caption(f"Gebaseerd op {len(df_filtered):,} games.")rekende kolommen: {', '.join(missing)}")

# --- COUNTERPICK ANALYSE ---
elif selected_analyse == "Counterpick Analyse":
    st.subheader("Counterpick Analyse")
    st.info("ℹ️ Kies een role en een champion om te zien welke champions de hoogste winrate hebben tegen jouw keuze.")

    # Role selector (alleen TOP en MID)
    role_display = st.radio(
        "Kies een role",
        options=["TOP", "MID"],
        horizontal=True
    )
    role_map = {"TOP": "TOP", "MID": "MIDDLE"}
    counterpick_role = role_map[role_display]
    # Bouw counterpick data op
    @st.cache_data
    def build_counterpick_df(df, role):
        counter_data = []
        for match_id, match_group in df.groupby('match_id'):
            role_group = match_group[match_group['teamPosition'] == role]
            if len(role_group['teamId'].unique()) != 2:
                continue
            teams = role_group.groupby('teamId')
            team_ids = list(teams.groups.keys())
            p1 = teams.get_group(team_ids[0]).iloc[0]
            p2 = teams.get_group(team_ids[1]).iloc[0]
            counter_data.append({'champion': p1['championName'], 'vs': p2['championName'], 'win': int(p1['win'])})
            counter_data.append({'champion': p2['championName'], 'vs': p1['championName'], 'win': int(p2['win'])})
        return pd.DataFrame(counter_data)

    df_role = df_filtered[df_filtered['teamPosition'] == counterpick_role]
    counter_df = build_counterpick_df(df_role, counterpick_role)

    if counter_df.empty:
        st.warning("Geen counterpick data beschikbaar voor de huidige selectie.")
    else:
        # Alle champions met genoeg games als "gespeelde champion"
        champ_game_counts = counter_df.groupby('vs')['win'].count()
        beschikbare_champs = sorted(champ_game_counts[champ_game_counts >= 10].index.tolist())

        selected_enemy_champ = st.selectbox(
            f"Kies de champion van de tegenstander ({counterpick_role})",
            options=beschikbare_champs
        )

        # Filter: alle champions die tegen selected_enemy_champ hebben gespeeld
        matchup_df = counter_df[counter_df['vs'] == selected_enemy_champ].copy()

        # Minimale games filter
        min_games_cp = st.slider("Minimaal aantal games per matchup", min_value=1, max_value=20, value=5, step=1)

        matchup_stats = (
            matchup_df.groupby('champion')['win']
            .agg(winrate='mean', games='count')
            .reset_index()
        )
        matchup_stats = matchup_stats[matchup_stats['games'] >= min_games_cp]
        matchup_stats['winrate'] = (matchup_stats['winrate'] * 100).round(1)
        matchup_stats = matchup_stats.sort_values('winrate', ascending=False)

        if matchup_stats.empty:
            st.warning("Niet genoeg data voor de huidige instelling. Verlaag de minimale games filter.")
        else:
            st.markdown(f"### Beste counters tegen **{selected_enemy_champ}** ({counterpick_role})")
            st.caption(f"Gebaseerd op {matchup_df.shape[0]:,} games | minimaal {min_games_cp} games per matchup")

            # Kleur op winrate
            fig = px.bar(
                matchup_stats,
                x='champion',
                y='winrate',
                color='winrate',
                text='winrate',
                hover_data={'games': True},
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=50,
                title=f"Winrate vs {selected_enemy_champ} — {counterpick_role} ({', '.join(selected_tiers)})",
                labels={'champion': 'Jouw Champion', 'winrate': 'Winrate (%)'},
            )
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Tabel eronder
            st.dataframe(
                matchup_stats.rename(columns={
                    'champion': 'Jouw Champion',
                    'winrate': 'Winrate (%)',
                    'games': 'Games gespeeld'
                }),
                use_container_width=True,
                hide_index=True
            )