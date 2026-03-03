import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def save_winrate_plot(df, tier):
    winrate_per_champ = df.groupby('championName')['win'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8,6))
    sns.barplot(x=winrate_per_champ.values, y=winrate_per_champ.index, ax=ax)
    ax.set_xlabel("Winrate")
    ax.set_ylabel("Champion")
    ax.set_title(f"Winrate per Champion - {tier}")
    
    # Sla op als afbeelding
    os.makedirs("plots", exist_ok=True)
    path = f"plots/winrate_{tier}.png"
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path

def save_counterpick_heatmap(df, tier, role):
    # Bereken counterpick stats
    counter_data = []
    for match_id, match_group in df.groupby('match_id'):
        for r in match_group['teamPosition'].unique():
            role_group = match_group[match_group['teamPosition'] == r]
            if len(role_group['teamId'].unique()) != 2:
                continue
            teams = role_group.groupby('teamId')
            team1 = teams.get_group(list(teams.groups.keys())[0])
            team2 = teams.get_group(list(teams.groups.keys())[1])
            champ1, champ2 = team1.iloc[0]['championName'], team2.iloc[0]['championName']
            win1, win2 = team1.iloc[0]['win'], team2.iloc[0]['win']
            counter_data.append({'champion': champ1, 'vs': champ2, 'win': win1})
            counter_data.append({'champion': champ2, 'vs': champ1, 'win': win2})

    counter_df = pd.DataFrame(counter_data)
    counter_filtered = counter_df[
        (counter_df['champion'].isin(df[df['teamPosition']==role]['championName'])) &
        (counter_df['vs'].isin(df[df['teamPosition']==role]['championName']))
    ]
    if counter_filtered.empty:
        return None

    pivot_df = counter_filtered.pivot(index='champion', columns='vs', values='win').fillna(0)

    fig, ax = plt.subplots(figsize=(10,8))
    sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0.5,
        linewidths=.5,
        cbar_kws={'label': 'Winrate'},
        ax=ax
    )
    ax.set_xlabel("Versus")
    ax.set_ylabel("Champion")
    ax.set_title(f"Counterpick Winrate - {role} - {tier}")

    os.makedirs("plots", exist_ok=True)
    path = f"plots/counterpick_{tier}_{role}.png"
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path