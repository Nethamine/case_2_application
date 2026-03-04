import os
import matplotlib.pyplot as plt
import seaborn as sns

def save_winrate_plot(df, tier_name):
    winrate = (
        df.groupby('championName')['win']
        .mean()
        .sort_values(ascending=False)
        .head(15)
    )

    fig, ax = plt.subplots(figsize=(8,6))
    sns.barplot(x=winrate.values, y=winrate.index, ax=ax)

    ax.set_xlabel("Winrate")
    ax.set_ylabel("Champion")
    ax.set_title(f"Winrate per Champion — {tier_name}")

    os.makedirs("plots", exist_ok=True)
    path = f"plots/winrate_{tier_name.lower()}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)

def save_counterpick_heatmap(df, tier_name, role):
    counter_data = []

    for match_id, match_group in df.groupby('match_id'):
        role_group = match_group[match_group['teamPosition'] == role]

        if len(role_group['teamId'].unique()) != 2:
            continue

        teams = role_group.groupby('teamId')
        team_ids = list(teams.groups.keys())

        p1 = teams.get_group(team_ids[0]).iloc[0]
        p2 = teams.get_group(team_ids[1]).iloc[0]

        counter_data.append({
            'champion': p1['championName'],
            'vs': p2['championName'],
            'win': p1['win']
        })
        counter_data.append({
            'champion': p2['championName'],
            'vs': p1['championName'],
            'win': p2['win']
        })

    counter_df = pd.DataFrame(counter_data)

    if counter_df.empty:
        return

    pivot_df = (
        counter_df
        .groupby(['champion', 'vs'])['win']
        .mean()
        .reset_index()
        .pivot(index='champion', columns='vs', values='win')
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(10,8))
    sns.heatmap(
        pivot_df,
        cmap="RdBu_r",
        center=0.5,
        ax=ax
    )

    ax.set_title(f"Counterpick Winrate — {role} — {tier_name}")

    os.makedirs("plots", exist_ok=True)
    path = f"plots/counterpick_{tier_name.lower()}_{role}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)

import pandas as pd

# laad per tier
df_chal = pd.read_csv("challenger_matches_useful.csv")
df_master = pd.read_csv("master_matches_useful.csv")
df_gm = pd.read_csv("grandmaster_matches_useful.csv")

# winrate plots
save_winrate_plot(df_chal, "Challenger")
save_winrate_plot(df_master, "Master")
save_winrate_plot(df_gm, "Grandmaster")

# counterpicks (voorbeeld MID)
for role in ["TOP", "JUNGLE", "MID", "BOTTOM", "UTILITY"]:
    save_counterpick_heatmap(df_chal, "Challenger", role)