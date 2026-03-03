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
            print(f"Rate limit bereikt. Wachten {int(sleep_time)} seconden...")
            time.sleep(sleep_time)
        requests_counter = 0
        start_time_2min = time.time()
    time.sleep(1 / REQUESTS_PER_SECOND)

def get_league_puuids(api_key, region, tier, queue='RANKED_SOLO_5x5', max_puuids=None):
    print(f"\nOphalen van {tier} spelers...")
    url = f"https://{region}.api.riotgames.com/lol/league/v4/{tier}/by-queue/{queue}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            puuids = [entry['puuid'] for entry in data['entries']]
            if max_puuids:
                puuids = puuids[:max_puuids]
            print(f"{len(puuids)} spelers opgehaald uit {tier}")
            return puuids
        elif resp.status_code == 429:
            print("Rate limit bij league endpoint. Wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Fout bij ophalen {tier}: {resp.status_code}")
            return []

def get_match_ids(puuid, api_key, region='europe', count=20):
    rate_limit_sleep()
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": api_key}
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            match_ids = resp.json()
            print(f"{len(match_ids)} matches gevonden voor speler {puuid[:6]}...")
            return match_ids
        elif resp.status_code == 429:
            print("Rate limit bij match ID endpoint. Wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Fout bij ophalen matches voor {puuid[:6]}: {resp.status_code}")
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
            print("Rate limit bij match details. Wachten 10 seconden...")
            time.sleep(10)
        else:
            print(f"Fout bij match {match_id}: {resp.status_code}")
            return None

def collect_tier_data(tier_name, tier_endpoint):
    print(f"\n========== START {tier_name.upper()} ==========")
    puuids = get_league_puuids(API_KEY, REGION, tier_endpoint, max_puuids=MAX_PUUIDS)
    all_participants = []
    seen_matches = set()
    total_matches = 0

    for i, puuid in enumerate(puuids, 1):
        print(f"\n{tier_name} speler {i}/{len(puuids)} ({puuid[:6]}...)")
        match_ids = get_match_ids(puuid, API_KEY, count=MATCHS_PER_PUUID)

        for j, mid in enumerate(match_ids, 1):
            if mid in seen_matches:
                print(f"Match {mid} al verwerkt, overslaan.")
                continue

            print(f"Verwerken match {j}/{len(match_ids)} voor speler {puuid[:6]}...")
            seen_matches.add(mid)
            match_data = get_match_details(mid, API_KEY)

            if match_data:
                total_matches += 1
                participants = match_data.get('info', {}).get('participants', [])
                print(f"{len(participants)} participants toegevoegd uit match {mid}")

                for p in participants:
                    p_flat = pd.json_normalize(p)
                    p_flat['match_id'] = mid
                    p_flat['tier'] = tier_name
                    p_flat = p_flat[[c for c in useful_columns if c in p_flat.columns] + ['match_id', 'tier']]
                    all_participants.append(p_flat)

    df = pd.concat(all_participants, ignore_index=True) if all_participants else pd.DataFrame()
    filename = f"{tier_name.lower()}_matches_useful.csv"
    df.to_csv(filename, index=False)

    print(f"\n{tier_name} klaar.")
    print(f"Totaal unieke matches: {total_matches}")
    print(f"Totaal rows in dataset: {len(df)}")
    print(f"Bestand opgeslagen als: {filename}")

    return df

df_challenger = collect_tier_data("Challenger", "challengerleagues")
df_master = collect_tier_data("Master", "masterleagues")
df_grandmaster = collect_tier_data("Grandmaster", "grandmasterleagues")

print("\nAlle tiers succesvol verwerkt.")
