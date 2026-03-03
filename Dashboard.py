import streamlit as st
import pandas as pd
import numpy as np
tier = st.selectbox("Selecteer een tier", ["Challenger", "Grandmaster", "Master"])
df = pd.read_csv(f"{tier.lower()}_matches_useful.csv")
st.title("League data vergeijking")
# Functie voor counterpick stats
def get_counterpick_stats(df):
    counter_data = []
    for match_id, match_group in df.groupby('match_id'):
        for role in match_group['teamPosition'].unique():
            role_group = match_group[match_group['teamPosition'] == role]
            if len(role_group['teamId'].unique()) != 2:
                continue
            teams = role_group.groupby('teamId')
            team1 = teams.get_group(list(teams.groups.keys())[0])
            team2 = teams.get_group(list(teams.groups.keys())[1])

            champ1 = team1.iloc[0]['championName']
            champ2 = team2.iloc[0]['championName']
            win1 = team1.iloc[0]['win']
            win2 = team2.iloc[0]['win']

            counter_data.append({'champion': champ1, 'vs': champ2, 'win': win1})
            counter_data.append({'champion': champ2, 'vs': champ1, 'win': win2})

    counter_df = pd.DataFrame(counter_data)
    counter_stats = counter_df.groupby(['champion', 'vs'])['win'].mean().reset_index()
    return counter_stats
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1: 
    st.write('Tab 1')
    st.header("Counterpick winrate per role")
    counter_stats = get_counterpick_stats(df)
    roles = df['teamPosition'].unique()
    selected_role = st.selectbox("Selecteer rol", roles)
    
    # Filter champions in deze rol
    champs_in_role = df[df['teamPosition'] == selected_role]['championName'].unique()
    counter_filtered = counter_stats[
        counter_stats['champion'].isin(champs_in_role) & counter_stats['vs'].isin(champs_in_role)
    ]
    
    # Pivot voor heatmap
    pivot_df = counter_filtered.pivot(index='champion', columns='vs', values='win').fillna(0)
    fig2 = px.imshow(
        pivot_df,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        title=f'Counterpick winrate - {selected_role}'
    )
    st.plotly_chart(fig)

with tab2:
    st.write('Tab 2')

with tab3:
    st.write('Tab 3')

