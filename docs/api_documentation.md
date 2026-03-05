# Riot Games API – Data Extraction Documentation

Deze documentatie beschrijft hoe wij data ophalen uit de Riot Games API voor ons League of Legends dashboard en welke requests daarbij worden gebruikt.

Het doel van de API calls is om matchdata te verzamelen van spelers in de hoogste ranked tiers en deze te gebruiken voor analyses in ons Streamlit dashboard.

---

# 1. Doel van de data

Wij verzamelen matchdata van spelers uit de volgende ranked tiers:

- Challenger
- Grandmaster
- Master

Van deze spelers halen we een aantal recente matches op. Van elke match slaan we statistieken van alle **10 spelers (participants)** op.

De data wordt opgeslagen in CSV bestanden:

- `challenger_matches_useful.csv`
- `grandmaster_matches_useful.csv`
- `master_matches_useful.csv`

Deze bestanden worden vervolgens ingeladen in ons **Streamlit dashboard**.

---

# 2. Authenticatie

De Riot API vereist een **API key**.

Wij sturen deze mee via een HTTP header:

```
X-Riot-Token: API_KEY
```

In Python:

```python
headers = {"X-Riot-Token": api_key}
requests.get(url, headers=headers)
```

---

# 3. API Requests die wij gebruiken

## 3.1 Spelers ophalen uit een tier

We beginnen met het ophalen van spelers uit een ranked tier.

Endpoint:

```
GET https://euw1.api.riotgames.com/lol/league/v4/{tier}/by-queue/RANKED_SOLO_5x5
```

Waar `{tier}` kan zijn:

- `challengerleagues`
- `grandmasterleagues`
- `masterleagues`

Response bevat een lijst met spelers (`entries`).  
Van elke speler halen we de **PUUID** op.

De **PUUID** is een unieke speler identifier die nodig is om matches op te halen.

---

## 3.2 Match IDs ophalen per speler

Met de PUUID kunnen we de matches van een speler opvragen.

Endpoint:

```
GET https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids
```

Parameters:

- `start=0`
- `count=10` (aantal matches per speler)

Dit endpoint geeft een lijst met **match IDs** terug.

---

## 3.3 Match details ophalen

Voor elke match ID halen we de volledige matchdata op.

Endpoint:

```
GET https://europe.api.riotgames.com/lol/match/v5/matches/{matchId}
```

De response bevat:

```
info.participants
```

Dit is een lijst met **10 spelers in de match**.

Van elke speler halen we statistieken zoals:

- championName
- kills
- deaths
- assists
- goldEarned
- totalMinionsKilled
- visionScore
- win

Deze worden omgezet naar een dataframe met:

```python
pd.json_normalize(participant)
```

---

# 4. Data pipeline (stappen)

Onze data pipeline werkt als volgt:

1. Haal spelers op uit Challenger / Grandmaster / Master.
2. Verzamel de PUUID van elke speler.
3. Haal match IDs op per speler.
4. Haal match details op per match.
5. Extract participant statistieken.
6. Sla alles op in CSV bestanden.

We gebruiken een `seen_matches` set zodat dezelfde match niet meerdere keren wordt verwerkt.

---

# 5. Rate limiting

De Riot API heeft **request limits**.

Daarom hebben we rate limiting in ons script ingebouwd:

```
REQUESTS_PER_SECOND = 20
REQUESTS_PER_2_MIN = 100
```

De functie `rate_limit_sleep()` zorgt ervoor dat:

- we maximaal 20 requests per seconde doen
- we maximaal 100 requests per 2 minuten doen

Als de limiet bereikt wordt:

- wacht het script automatisch totdat er weer requests toegestaan zijn.

Dit voorkomt dat de API onze requests blokkeert.

---

# 6. Gebruik in het dashboard

De CSV bestanden worden ingeladen in het Streamlit dashboard.

Daarmee maken we analyses zoals:

- Winrate per champion
- Games gespeeld per champion
- KDA per champion
- Winrate vs champion level
- Gold en minions vs winrate
- Counterpick analyse

Alle data wordt eerst samengevoegd tot één dataframe:

```python
df_all = pd.concat([df_chal, df_gm, df_m])
```

De sidebar filters bepalen vervolgens welke data wordt weergegeven in de grafieken.

---

# 7. Gebruikte Python libraries

Voor het ophalen en analyseren van de data gebruiken we:

- `requests` → API calls
- `pandas` → data verwerking
- `streamlit` → dashboard
- `plotly` → visualisaties

---

# 8. Referentie notebook

Tijdens de ontwikkeling hebben we een online notebook gebruikt als referentie voor het ophalen van match data:

`Extracting_Match_Data.ipynb`

Dit hielp ons bij het begrijpen van:

- match-v5 endpoints
- match ID retrieval
- structuur van match data

Onze uiteindelijke implementatie is aangepast voor onze eigen data pipeline en dashboard.
