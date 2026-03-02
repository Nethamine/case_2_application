import requests
import pandas as pd
import time

API_KEY = 'Jouw API key'
REGION = 'euw1'

MAX_PUUIDS = 5
MATCHS_PER_PUUID = 10

REQUESTS_PER_SECOND = 20
REQUESTS_PER_2_MIN = 100
requests_counter = 0
start_time_2min = time.time()

useful_columns = ['assists', 'champLevel', 'championName', 'deaths', 'detectorWardsPlaced',
                  'gameEndedInEarlySurrender', 'gameEndedInSurrender', 'goldEarned', 'inhibitorsLost',
                  'kills', 'magicDamageDealt', 'magicDamageDealtToChampions', 'neutralMinionsKilled',
                  'physicalDamageDealt', 'physicalDamageDealtToChampions', 'physicalDamageTaken', 'profileIcon',
                  'sightWardsBoughtInGame', 'teamId', 'teamPosition', 'totalDamageDealt',
                  'totalDamageDealtToChampions', 'totalMinionsKilled', 'trueDamageDealt',
                  'trueDamageDealtToChampions', 'turretsLost', 'visionScore', 'wardsKilled',
                  'wardsPlaced', 'win']

def rate_limit_sleep():
    global requests_counter, start_time_2min
    requests_counter += 1
    elapsed_2min = time.time() - start_time_2min
    if requests_counter >= REQUESTS_PER_2_MIN:
        sleep_time = max(0, 120 - elapsed_2min)
        if sleep_time > 0:
            print(f"Rate limit 100/2min bereikt, wachten {int(sleep_time)}s...")
            time.sleep(sleep_time)
        requests_counter = 0
        start_time_2min = time.time()
    time.sleep(1 / REQUESTS_PER_SECOND)

def get_challenger_puuids(api_key, region='euw1', queue='RANKED_SOLO_5x5', max_puuids=None):
    url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/{queue}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            puuids = [entry['puuid'] for entry in data['entries']]
            if max_puuids:
                puuids = puuids[:max_puuids]
            print(f"{len(puuids)} spelers geselecteerd uit de Challenger-league")
            return puuids
        elif resp.status_code == 429:
            print("Rate limit — wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Error fetching challenger league: {resp.status_code}")
            return []

def get_match_ids(puuid, api_key, region='europe', count=20):
    rate_limit_sleep()
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            print(f"{len(resp.json())} match IDs opgehaald voor PUUID {puuid[:6]}...")
            return resp.json()
        elif resp.status_code == 429:
            print("Rate limit — wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Error fetching matches for PUUID {puuid[:6]}: {resp.status_code}")
            return []

def get_match_details(match_id, api_key):
    rate_limit_sleep()
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            print(f"Match data opgehaald: {match_id}")
            return resp.json()
        elif resp.status_code == 429:
            print("Rate limit — wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Error fetching match {match_id}: {resp.status_code}")
            return None

challenger_puuids = get_challenger_puuids(API_KEY, REGION, max_puuids=MAX_PUUIDS)

all_participants = []
for i, puuid in enumerate(challenger_puuids, 1):
    print(f"Verwerken van speler {i}/{len(challenger_puuids)} (PUUID: {puuid[:6]}...)")
    match_ids = get_match_ids(puuid, API_KEY, count=MATCHS_PER_PUUID)
    for mid in match_ids:
        match_data = get_match_details(mid, API_KEY)
        if match_data:
            participants = match_data.get('info', {}).get('participants', [])
            for p in participants:
                p_flat = pd.json_normalize(p)
                p_flat['match_id'] = mid
                # Filter alleen de kolommen die nuttig zijn
                p_flat = p_flat[[c for c in useful_columns if c in p_flat.columns] + ['match_id']]
                all_participants.append(p_flat)

df_participants = pd.concat(all_participants, ignore_index=True) if all_participants else pd.DataFrame()
df_participants.to_csv("challenger_matches_usefull.csv", index=False)
print("Participant dataset opgeslagen als challenger_participants_useful.csv")
print(df_participants.head())
