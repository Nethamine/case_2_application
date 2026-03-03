import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.title("League of Legends High Elo Dashboard")

# Kies tier
tier = st.selectbox("Selecteer een tier", ["Challenger", "Grandmaster", "Master"])
df = pd.read_csv(f"{tier.lower()}_matches_useful.csv")

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

# Tabs maken
tab1, tab2, tab3 = st.tabs(["Winrate per champion", "Counterpick winrate", "Extra statistieken"])

# ---- TAB 1: Winrate per champion ----
with tab1:
    st.header("Winrate per champion")
    winrate_per_champ = df.groupby('championName')['win'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8,6))
    sns.barplot(x=winrate_per_champ.values, y=winrate_per_champ.index, ax=ax)
    ax.set_xlabel("Winrate")
    ax.set_ylabel("Champion")
    st.pyplot(fig)

# ---- TAB 2: Counterpick winrate ----
with tab2:
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
    st.plotly_chart(fig2)

# ---- TAB 3: Extra statistieken ----
with tab3:
    st.header("Extra statistieken")
    st.write("Hier kun je bijvoorbeeld gemiddelde K/D/A, damage stats of vision scores toevoegen.")
    st.dataframe(df[['championName','kills','deaths','assists','goldEarned']].head(10))