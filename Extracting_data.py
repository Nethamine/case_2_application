import os
import time
import csv
import requests

# -----------------------
# Config
# -----------------------
API_KEY = "Input eigen API key"

PLATFORM_REGION = "euw1"   # league-v4
MATCH_REGION = "europe"    # match-v5

MAX_PUUIDS = 100
MATCHES_PER_PUUID = 10

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# extra safety naast 429 handling
REQUESTS_PER_SECOND = 20
REQUESTS_PER_2_MIN = 100

TIMEOUT_SECONDS = 15
MAX_RETRIES = 3

useful_columns = [
    "assists", "champLevel", "championName", "deaths", "detectorWardsPlaced",
    "gameEndedInEarlySurrender", "gameEndedInSurrender", "goldEarned", "inhibitorsLost",
    "kills", "magicDamageDealt", "magicDamageDealtToChampions", "neutralMinionsKilled",
    "physicalDamageDealt", "physicalDamageDealtToChampions", "physicalDamageTaken",
    "profileIcon", "sightWardsBoughtInGame", "teamId", "teamPosition",
    "totalDamageDealt", "totalDamageDealtToChampions", "totalMinionsKilled",
    "trueDamageDealt", "trueDamageDealtToChampions", "turretsLost",
    "visionScore", "wardsKilled", "wardsPlaced", "win",
]
CSV_COLUMNS = useful_columns + ["match_id", "tier"]

# Throttle state
requests_counter = 0
start_time_2min = time.time()
last_request_time = 0.0

session = requests.Session()
headers = {"X-Riot-Token": API_KEY}


def rate_limit_sleep():
    """Best-effort throttling: max req/s + max req/2min."""
    global requests_counter, start_time_2min, last_request_time

    # req/s pacing
    min_interval = 1.0 / REQUESTS_PER_SECOND
    now = time.time()
    since_last = now - last_request_time
    if since_last < min_interval:
        time.sleep(min_interval - since_last)
    last_request_time = time.time()

    # req/2min window
    requests_counter += 1
    elapsed_2min = last_request_time - start_time_2min
    if requests_counter >= REQUESTS_PER_2_MIN:
        sleep_time = max(0, 120 - elapsed_2min)
        if sleep_time > 0:
            print(f"Rate limit {REQUESTS_PER_2_MIN}/2min bereikt, wachten {int(sleep_time)} seconden...")
            time.sleep(sleep_time)
        requests_counter = 0
        start_time_2min = time.time()


def riot_get_json(url: str, max_retries: int = MAX_RETRIES):
    """
    Centrale request wrapper:
    - throttling
    - retries
    - 429 handling met Retry-After
    - timeout
    """
    for attempt in range(1, max_retries + 1):
        rate_limit_sleep()

        try:
            resp = session.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as e:
            print(f"[ERROR] Request exception ({attempt}/{max_retries}): {e}")
            time.sleep(2 * attempt)
            continue

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            wait_s = int(retry_after) if retry_after and retry_after.isdigit() else 10
            print(f"[429] Too Many Requests. Wachten {wait_s}s (attempt {attempt}/{max_retries})...")
            time.sleep(wait_s)
            continue

        print(f"[ERROR] Status {resp.status_code} voor URL: {url}")
        time.sleep(2 * attempt)

    return None


def get_league_puuids(tier_endpoint: str, queue: str = "RANKED_SOLO_5x5", max_puuids: int | None = None):
    print(f"\nOphalen van {tier_endpoint} spelers...")
    url = f"https://{PLATFORM_REGION}.api.riotgames.com/lol/league/v4/{tier_endpoint}/by-queue/{queue}"
    data = riot_get_json(url)
    if not data:
        return []

    puuids = [entry.get("puuid") for entry in data.get("entries", []) if entry.get("puuid")]
    if max_puuids:
        puuids = puuids[:max_puuids]

    print(f"{len(puuids)} spelers opgehaald uit {tier_endpoint}")
    return puuids


def get_match_ids(puuid: str, count: int):
    url = (
        f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/"
        f"{puuid}/ids?start=0&count={count}"
    )
    data = riot_get_json(url)
    if not data:
        return []
    return data


def get_match_details(match_id: str):
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return riot_get_json(url)


def participant_to_row(p: dict, match_id: str, tier_name: str) -> dict:
    """Participant JSON -> 1 dict row met alleen desired columns + match_id/tier."""
    row = {col: p.get(col, None) for col in useful_columns}
    row["match_id"] = match_id
    row["tier"] = tier_name
    return row


def collect_tier_data_streaming(tier_name: str, tier_endpoint: str, seen_matches: set[str]):
    print(f"\n========== START {tier_name.upper()} ==========")

    puuids = get_league_puuids(tier_endpoint, max_puuids=MAX_PUUIDS)

    out_path = os.path.join(OUTPUT_DIR, f"{tier_name.lower()}_matches_useful.csv")
    total_unique_matches = 0
    total_rows = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for i, puuid in enumerate(puuids, 1):
            match_ids = get_match_ids(puuid, count=MATCHES_PER_PUUID)
            print(f"{tier_name} speler {i}/{len(puuids)} ({puuid[:6]}...) -> {len(match_ids)} matches")

            for mid in match_ids:
                if mid in seen_matches:
                    continue

                seen_matches.add(mid)
                match_data = get_match_details(mid)
                if not match_data:
                    continue

                total_unique_matches += 1
                participants = match_data.get("info", {}).get("participants", [])

                for p in participants:
                    writer.writerow(participant_to_row(p, match_id=mid, tier_name=tier_name))
                    total_rows += 1

    print(f"\n{tier_name} klaar.")
    print(f"Totaal unieke matches (in deze tier-run): {total_unique_matches}")
    print(f"Totaal rows in dataset: {total_rows}")
    print(f"Bestand opgeslagen als: {out_path}")


# Run pipeline
seen_matches_global = set()

collect_tier_data_streaming("Challenger", "challengerleagues", seen_matches_global)
collect_tier_data_streaming("Master", "masterleagues", seen_matches_global)
collect_tier_data_streaming("Grandmaster", "grandmasterleagues", seen_matches_global)

print("\nAlle tiers succesvol verwerkt.")