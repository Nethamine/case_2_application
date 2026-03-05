import streamlit as st
import pandas as pd
import plotly.express as px

df_chal = pd.read_csv("data/challenger_matches_useful.csv")
df_gm = pd.read_csv("data/grandmaster_matches_useful.csv")
df_m = pd.read_csv("data/master_matches_useful.csv")
df_all = pd.concat([df_chal, df_gm, df_m], ignore_index=True)

# --- SIDEBAR ---
role_display_map = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "MIDDLE": "MID",
    "BOTTOM": "BOTTOM",
    "UTILITY": "SUPPORT"
}

with st.sidebar:
    st.header("Filters")
    analyse_opties = {
        "🏠 Home": "home",
        "Champion Tier List": "tier_list",
        "Winrate vs Champion Level": "champ_level_winrate",
        "Vision & Winrate Analyse": "vision_winrate",
        "Counterpick Analyse": "counterpick",
    }
    selected_analyse = st.selectbox("Kies analyse", list(analyse_opties.keys()))

    alle_tiers = sorted(df_all['tier'].dropna().unique().tolist())
    selected_tiers = st.multiselect("Kies Tier(s)/Rank(s)", options=alle_tiers, default=alle_tiers)

    if selected_analyse not in ["Counterpick Analyse", "Vision & Winrate Analyse", "Champion Tier List","Winrate vs Champion Level", "Home"]:
        alle_roles = sorted(df_all['teamPosition'].dropna().unique().tolist()) if 'teamPosition' in df_all.columns else []
        rolle_labels = [role_display_map.get(r, r) for r in alle_roles]
        selected_role_labels = st.multiselect("Kies Role(s)", options=rolle_labels, default=rolle_labels)
    # Vertaal terug naar de echte namen voor filtering
        reverse_map = {v: k for k, v in role_display_map.items()}
        selected_roles = [reverse_map.get(r, r) for r in selected_role_labels]
    else:
        selected_roles = alle_roles = sorted(df_all['teamPosition'].dropna().unique().tolist())
    


if selected_analyse == "🏠 Home":
    st.title("League of Legends Ranked Dashboard")
    st.markdown(f"*Gebaseerd op **{len(df_all):,} games** uit Challenger, Grandmaster en Master (EUW)*")
    
    st.markdown("""
    > Wil jij meer ranked games winnen? Dit dashboard analyseert data van de beste spelers op EUW 
    en vertaalt dat naar inzichten waar jij wat aan hebt. Van champion tier lists, de beste counterpicks, tot hoeveel vision 
    jij nodig hebt om de kans op winst te vergroten!.
    """)

    st.markdown("---")
    st.subheader("Wat kun je hier vinden?")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🏆 **Champion Tier List**")
        st.caption("Ontdek de beste champions voor jouw role op basis van jouw eigen prioriteiten.")
        st.markdown("⚔️ **Counterpick Analyse**")
        st.caption("Welke champion moet je kiezen om jouw tegenstander te kunnen counteren.")
    with col2:
        st.markdown("👁️ **Vision & Winrate Analyse**")
        st.caption("Wards win games. Ontdek hoeveel vision winnende spelers plaatsen in jouw role.")
        st.markdown("📊 **Winrate vs Champion Level**")
        st.caption("Scale, scale, scale! Wie moet je spelen om later unkillable te worden?")
    st.markdown("---")
    st.subheader("Hoe gebruik je dit dashboard?")
    st.markdown("""
    1. Kies een **analyse** in de sidebar links
    2. Gebruik de inzichten om jouw **ranked gameplay te verbeteren**
    """)

    st.info("💡 Tip: Begin met de **Champion Tier List** als je direct wilt weten welke champion je moet picken in je volgende game.")
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

elif selected_analyse == "Champion Tier List":
    st.subheader("Champion Tier List")
    st.info("ℹ️ Ontdek de beste champions voor jouw role op basis van winrate, KDA en populariteit.")

    # --- ROLE SELECTOR ---
    role_map_tierlist = {
        "TOP": "TOP",
        "JUNGLE": "JUNGLE",
        "MID": "MIDDLE",
        "BOTTOM": "BOTTOM",
        "SUPPORT": "UTILITY"
    }
    selected_role_display_tl = st.radio(
        "Kies jouw role",
        options=list(role_map_tierlist.keys()),
        horizontal=True
    )
    selected_role_tl = role_map_tierlist[selected_role_display_tl]
    df_role_tl = df_filtered[df_filtered['teamPosition'] == selected_role_tl]

    if df_role_tl.empty:
        st.warning("Geen data beschikbaar voor deze role en tier selectie.")
        st.stop()

    # --- GEWICHTEN SLIDERS ---
    st.markdown("**Wat is voor jou belangrijk? Stel het hier in:**")
    col1, col2 = st.columns(2)
    with col1:
        gewicht_winrate = st.slider("🏆 Winrate prioriteit (%)", 0, 100, 50, step=5)
        gewicht_kda = st.slider("⚔️ KDA prioriteit (%)", 0, 100 - gewicht_winrate, 25, step=5)
    with col2:
        gewicht_populariteit = 100 - gewicht_winrate - gewicht_kda
        st.metric("🎮 Populariteit prioriteit", f"{gewicht_populariteit}%")
        st.caption("Wordt automatisch berekend op basis van de andere twee sliders.")

    # --- MINIMALE GAMES FILTER ---
    min_games_tl = st.slider("Minimaal aantal games per champion", min_value=10, max_value=50, value=10, step=5)

    # --- SCORE BEREKENING ---
    required_cols = {'championName', 'win', 'kills', 'deaths', 'assists'}
    missing = required_cols - set(df_role_tl.columns)
    if missing:
        st.warning(f"Ontbrekende kolommen: {', '.join(missing)}")
        st.stop()

    # Bereken winrate, kda en populariteit per champion
    champ_df = (
        df_role_tl.groupby('championName')
        .agg(
            winrate=('win', 'mean'),
            games=('win', 'count'),
            kills=('kills', 'mean'),
            deaths=('deaths', 'mean'),
            assists=('assists', 'mean')
        )
        .reset_index()
    )
    champ_df = champ_df[champ_df['games'] >= min_games_tl]
    champ_df['kda'] = ((champ_df['kills'] + champ_df['assists']) / champ_df['deaths'].clip(lower=1)).round(2)
    champ_df['winrate'] = (champ_df['winrate'] * 100).round(1)

    if champ_df.empty:
        st.warning("Niet genoeg data voor de huidige instellingen. Verlaag de minimale games filter.")
        st.stop()

    # Normaliseer alle metrics naar 0-100
    def normalize(series):
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([50] * len(series), index=series.index)
        return ((series - min_val) / (max_val - min_val) * 100).round(1)

    champ_df['winrate_norm'] = normalize(champ_df['winrate'])
    champ_df['kda_norm'] = normalize(champ_df['kda'])
    champ_df['populariteit_norm'] = normalize(champ_df['games'])

    # Gewogen score berekenen
    champ_df['score'] = (
        (champ_df['winrate_norm'] * gewicht_winrate / 100) +
        (champ_df['kda_norm'] * gewicht_kda / 100) +
        (champ_df['populariteit_norm'] * gewicht_populariteit / 100)
    ).round(1)

    # Tier toewijzen op basis van absolute score (optie B)
    def assign_tier(score):
        if score >= 80:
            return 'S'
        elif score >= 60:
            return 'A'
        elif score >= 40:
            return 'B'
        else:
            return 'C'

    champ_df['tier'] = champ_df['score'].apply(assign_tier)

    # --- TIER LIST WEERGAVE ---
    tier_colors = {'S': '🟡', 'A': '🟢', 'B': '🔵', 'C': '🔴'}
    tier_labels = {
        'S': 'S Tier — Dominante picks, hoog in alles',
        'A': 'A Tier — Sterke picks, solide keuze',
        'B': 'B Tier — Gemiddelde picks, situationeel',
        'C': 'C Tier — Zwakke picks, vermijd indien mogelijk'
    }

    for tier in ['S', 'A', 'B', 'C']:
        tier_champs = champ_df[champ_df['tier'] == tier].sort_values('score', ascending=False).head(3)
        if tier_champs.empty:
            continue

        st.markdown(f"### {tier_colors[tier]} {tier_labels[tier]}")
        cols = st.columns(min(len(tier_champs), 5))
        for i, (_, row) in enumerate(tier_champs.iterrows()):
            with cols[i % 5]:
                st.metric(
                    label=row['championName'],
                    value=f"{row['score']}",
                    delta=f"{row['winrate']}% WR"
                )
                st.caption(f"KDA: {row['kda']} | Games: {int(row['games'])}")
        st.markdown("---")

    # --- DETAIL TABEL ---
    st.subheader("Volledige ranking")
    tabel_df = champ_df[['tier', 'championName', 'score', 'winrate', 'kda', 'games']].sort_values('score', ascending=False)
    tabel_df = tabel_df.rename(columns={
        'tier': 'Tier',
        'championName': 'Champion',
        'score': 'Score',
        'winrate': 'Winrate (%)',
        'kda': 'KDA',
        'games': 'Games'
    })
    tabel_df['Games'] = tabel_df['Games'].astype(int)
    st.dataframe(tabel_df, use_container_width=True, hide_index=True)
    st.caption(f"Gebaseerd op {len(df_role_tl):,} games als {selected_role_display_tl} in {', '.join(selected_tiers)}.")

elif selected_analyse == "Winrate vs Champion Level":
    st.subheader("Winrate vs Champion Level")
    st.info("ℹ️ Alleen champions met minimaal **10 gespeelde games** worden getoond.")

    if 'champLevel' in df_filtered.columns and 'win' in df_filtered.columns:

        # --- ROLE SELECTOR ---
        role_map_champlevel = {
            "TOP": "TOP",
            "JUNGLE": "JUNGLE",
            "MID": "MIDDLE",
            "BOTTOM": "BOTTOM",
            "SUPPORT": "UTILITY"
        }
        selected_role_display_cl = st.radio(
            "Kies jouw role",
            options=list(role_map_champlevel.keys()),
            horizontal=True
        )
        selected_role_cl = role_map_champlevel[selected_role_display_cl]
        df_role_cl = df_filtered[df_filtered['teamPosition'] == selected_role_cl]

        # --- CHAMPION FILTER OP DE TAB ---
        champ_counts = df_role_cl['championName'].value_counts()
        alle_champs_cl = sorted(champ_counts[champ_counts >= 10].index.tolist())
        selected_champs = st.multiselect(
            "Filter op Champion(s)",
            options=alle_champs_cl,
            default=[]
        )

        # --- CHAMPION LEVEL SLIDER OP DE TAB ---
        min_dur = int(df_role_cl['champLevel'].min())
        max_dur = 20
        duration_range = st.slider(
            "Filter op Champion Level",
            min_value=min_dur, max_value=max_dur,
            value=(min_dur, max_dur), step=1
        )

        # --- FILTERING ---
        df_dur = df_role_cl[
            (df_role_cl['champLevel'] >= duration_range[0]) &
            (df_role_cl['champLevel'] <= duration_range[1])
        ].copy()

        champ_counts = df_dur['championName'].value_counts()
        uitgesloten1 = df_dur[~df_dur['championName'].isin(champ_counts[champ_counts >= 10].index)]['championName'].nunique()
        df_dur = df_dur[df_dur['championName'].isin(champ_counts[champ_counts >= 10].index)]

        if uitgesloten1 > 0:
            st.caption(f"{uitgesloten1} champion(s) uitgesloten wegens minder dan 10 games gespeeld.")

        if selected_champs:
            df_dur = df_dur[df_dur['championName'].isin(selected_champs)]

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
                    title=f"Winrate per Champion Level — {selected_role_display_cl} ({', '.join(selected_tiers)})",
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
                    title=f"Winrate per Champion Level — {selected_role_display_cl} ({', '.join(selected_tiers)})",
                    labels={'champ_level': 'Champion Level', 'winrate': 'Winrate (%)'},
                    markers=True
                )
                fig.update_traces(line_color='royalblue')

            fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Gebaseerd op {len(df_dur):,} games als {selected_role_display_cl} met champion level tussen {duration_range[0]} en {duration_range[1]}.")
    else:
        st.warning("Kolom 'champLevel' of 'win' niet gevonden in de data.")

elif selected_analyse == "Vision & Winrate Analyse":
    st.subheader("Vision & Winrate Analyse")
    st.info("ℹ️ Ontdek hoeveel vision jij nodig hebt om zo veel mogelijk games te winnen in jouw role.")

    # --- ROLE SELECTOR ---
    role_display_options = ["TOP", "JUNGLE", "MID", "BOTTOM", "SUPPORT"]
    role_map_vision = {
        "TOP": "TOP",
        "JUNGLE": "JUNGLE",
        "MID": "MIDDLE",
        "BOTTOM": "BOTTOM",
        "SUPPORT": "UTILITY"
    }

    selected_role_display = st.radio(
        "Kies jouw role",
        options=role_display_options,
        horizontal=True
    )
    selected_role = role_map_vision[selected_role_display]

    df_role_vision = df_filtered[df_filtered['teamPosition'] == selected_role]

    if df_role_vision.empty:
        st.warning("Geen data beschikbaar voor deze role en tier selectie.")
        st.stop()

    # --- CHECKBOXES ---
    st.markdown("**Kies welke vision metrics je wilt analyseren:**")
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

    # --- BUCKET SLIDER ---
    bucket_size = st.select_slider(
        "Bucket grootte",
        options=[1, 2, 3, 5, 10],
        value=3
    )
    min_games = st.slider("Minimaal aantal games per bucket", min_value=5, max_value=50, value=10, step=5)

    # --- GRAFIEK ---
    fig = px.line(title=f"Vision Metrics vs Winrate — {selected_role_display} ({', '.join(selected_tiers)})")
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")

    for col, label in selected_metrics:
        df_metric = df_role_vision[[col, 'win']].copy()
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

    # --- DETAIL TABEL: winnaars vs verliezers ---
    st.subheader(f"Wat doen winnende {selected_role_display} spelers anders?")
    st.caption("Vergelijking van gemiddelde vision metrics tussen winnaars en verliezers.")

    detail_rows = []
    for col, label in selected_metrics:
        winners = df_role_vision[df_role_vision['win'] == 1][col].mean()
        losers = df_role_vision[df_role_vision['win'] == 0][col].mean()
        verschil = winners - losers
        detail_rows.append({
            'Metric': label,
            'Gem. Winnaars': round(winners, 2),
            'Gem. Verliezers': round(losers, 2),
            'Verschil': round(verschil, 2),
            'Conclusie': f"Winnaars hebben {round(abs(verschil), 2)} {'meer' if verschil > 0 else 'minder'} {label.lower()}"
        })

    detail_df = pd.DataFrame(detail_rows).sort_values('Verschil', ascending=False)
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    st.caption(f"Gebaseerd op {len(df_role_vision):,} games als {selected_role_display} in {', '.join(selected_tiers)}.")
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