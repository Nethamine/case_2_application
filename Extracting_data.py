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
                  'physicalDamageDealt', 'physicalDamageDealtToChampions', 'physicalDamageTaken',
                  'profileIcon', 'sightWardsBoughtInGame', 'teamId', 'teamPosition',
                  'totalDamageDealt', 'totalDamageDealtToChampions', 'totalMinionsKilled',
                  'trueDamageDealt', 'trueDamageDealtToChampions', 'turretsLost',
                  'visionScore', 'wardsKilled', 'wardsPlaced', 'win']

def rate_limit_sleep():
    global requests_counter, start_time_2min
    requests_counter += 1
    elapsed_2min = time.time() - start_time_2min
    if requests_counter >= REQUESTS_PER_2_MIN:
        sleep_time = max(0, 120 - elapsed_2min)
        if sleep_time > 0:
            time.sleep(sleep_time)
        requests_counter = 0
        start_time_2min = time.time()
    time.sleep(1 / REQUESTS_PER_SECOND)

def get_league_puuids(api_key, region, tier, queue='RANKED_SOLO_5x5', max_puuids=None):
    url = f"https://{region}.api.riotgames.com/lol/league/v4/{tier}/by-queue/{queue}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            puuids = [entry['puuid'] for entry in data['entries']]
            if max_puuids:
                puuids = puuids[:max_puuids]
            return puuids
        elif resp.status_code == 429:
            time.sleep(10)
        else:
            return []

def get_match_ids(puuid, api_key, region='europe', count=20):
    rate_limit_sleep()
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            time.sleep(10)
        else:
            return []

def get_match_details(match_id, api_key):
    rate_limit_sleep()
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            time.sleep(10)
        else:
            return None

def collect_tier_data(tier_name, tier_endpoint):
    puuids = get_league_puuids(API_KEY, REGION, tier_endpoint, max_puuids=MAX_PUUIDS)
    all_participants = []
    seen_matches = set()

    for puuid in puuids:
        match_ids = get_match_ids(puuid, API_KEY, count=MATCHS_PER_PUUID)
        for mid in match_ids:
            if mid in seen_matches:
                continue
            seen_matches.add(mid)
            match_data = get_match_details(mid, API_KEY)
            if match_data:
                participants = match_data.get('info', {}).get('participants', [])
                for p in participants:
                    p_flat = pd.json_normalize(p)
                    p_flat['match_id'] = mid
                    p_flat['tier'] = tier_name
                    p_flat = p_flat[[c for c in useful_columns if c in p_flat.columns] + ['match_id', 'tier']]
                    all_participants.append(p_flat)

    df = pd.concat(all_participants, ignore_index=True) if all_participants else pd.DataFrame()
    filename = f"{tier_name.lower()}_matches_useful.csv"
    df.to_csv(filename, index=False)
    return df

df_challenger = collect_tier_data("Challenger", "challengerleagues")
df_master = collect_tier_data("Master", "masterleagues")
df_grandmaster = collect_tier_data("Grandmaster", "grandmasterleagues")