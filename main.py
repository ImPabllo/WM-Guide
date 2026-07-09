import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai

app = FastAPI(title="WM-Tipp-Analysator Live 2026")

# Erlaube dem Frontend den Zugriff (Browser-sicher konfiguriert)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ TRAGE HIER WIEDER DEINE ECHTEN SCHLÜSSEL EIN
OPENAI_API_KEY = "dae0dec90dc68e23baf56e3d09afd0b6"
FOOTBALL_API_KEY = "a0c04b4f55ae47e585acb706a3e6a1a1"

openai.api_key = OPENAI_API_KEY

# DEINE WUNSCH-SPIELE ALS SICHERHEITS-NETZ UND DEMO
WUNSCH_SPIELE = [
    {"match_id": "wm_live_1", "home": "Spanien", "away": "Belgien", "date": "Heute, 18:00 Uhr"},
    {"match_id": "wm_live_2", "home": "Schweiz", "away": "Argentinien", "date": "Heute, 21:00 Uhr"},
    {"match_id": "wm_live_3", "home": "England", "away": "Norwegen", "date": "Morgen, 20:45 Uhr"}
]

@app.get("/")
def read_root():
    return {"status": "Backend läuft fehlerfrei!"}

@app.get("/api/matches")
def get_upcoming_matches():
    """ Holt die aktuellen WM-Spiele live aus dem Internet oder zeigt deine Wunsch-Spiele """
    
    # Falls kein echter Key da ist, direkt deine Wunsch-Spiele anzeigen
    if FOOTBALL_API_KEY == "DEIN_API_FOOTBALL_KEY" or FOOTBALL_API_KEY == "x":
        return WUNSCH_SPIELE

    url = "https://v3.football.api-sports.io/fixtures?next=5" 
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": FOOTBALL_API_KEY
    }
    try:
        response = requests.get(url, headers=headers).json()
        matches = []
        for item in response.get("response", []):
            matches.append({
                "match_id": str(item["fixture"]["id"]),
                "home": item["teams"]["home"]["name"],
                "away": item["teams"]["away"]["name"],
                "date": item["fixture"]["date"]
            })
        
        # Falls die API leer zurückkommt, weichen wir auf deine Wunsch-Spiele aus
        if not matches:
            return WUNSCH_SPIELE
            
        return matches
    except Exception as e:
        return WUNSCH_SPIELE

@app.get("/api/analysis/{match_id}")
def get_match_analysis(match_id: str):
    """ Holt Spieldaten für ein spezifisches Spiel und analysiert es """
    
    # Falls es eines deiner Wunsch-Spiele (Demo) ist ODER der OpenAI-Key fehlt:
    if OPENAI_API_KEY == "DEIN_OPENAI_API_KEY" or OPENAI_API_KEY == "x" or match_id.startswith("wm_live"):
        if "1" in match_id or "spanien" in match_id.lower():
            return {
                "match_info": {"home": "Spanien", "away": "Belgien"},
                "kader": {
                    "home": ["Lamine Yamal", "Nico Williams", "Pedri", "Rodri", "Dani Olmo"], 
                    "away": ["De Bruyne", "Lukaku", "Doku", "Tielemans", "Faes"]
                },
                "quoten": {"bet365": {"1": "1.70", "X": "3.80", "2": "4.50"}},
                "analyse": "🤖 KI-EXPERTEN-PROGNOSE (Spanien vs. Belgien):\n\nSpanien geht mit seiner spielerischen Dominanz und den brandgefährlichen Flügeln um Yamal und Williams als Favorit ins Spiel. Belgien besitzt mit Kevin De Bruyne jedoch enorme Umschaltqualität.\n\nTendenz für Tippspieler: Spanien kontrolliert das Mittelfeld. Ein spielerisch starkes 2:1 oder 3:1 für Spanien."
            }
        elif "2" in match_id or "schweiz" in match_id.lower():
            return {
                "match_info": {"home": "Schweiz", "away": "Argentinien"},
                "kader": {
                    "home": ["Xhaka", "Akanji", "Embolo", "Freuler", "Kobel"], 
                    "away": ["Messi", "Alvarez", "Mac Allister", "De Paul", "Martinez"]
                },
                "quoten": {"bet365": {"1": "3.90", "X": "3.40", "2": "1.95"}},
                "analyse": "🤖 KI-EXPERTEN-PROGNOSE (Schweiz vs. Argentinien):\n\nDie Schweiz hat sich als extrem unangenehmer Turniergegner mit toller Defensivorganisation um Akanji bewiesen. Argentinien vertraut auf die Genialität von Lionel Messi und die Ballsicherheit im Zentrum.\n\nTendenz für Tippspieler: Ein zähes Geduldsspiel für den Weltmeister. Tipp: Ein knappes 1:0 für Argentinien oder ein heroisches 1:1-Unentschieden."
            }
        else:
            return {
                "match_info": {"home": "England", "away": "Norwegen"},
                "kader": {
                    "home": ["Bellingham", "Kane", "Saka", "Foden", "Rice"], 
                    "away": ["Haaland", "Ødegaard", "Nusa", "Berge", "Ryerson"]
                },
                "quoten": {"bet365": {"1": "1.60", "X": "4.00", "2": "5.25"}},
                "analyse": "🤖 KI-EXPERTEN-PROGNOSE (England vs. Norwegen):\n\nEin absolutes Offensiv-Spektakel! Bellingham und Kane auf der einen Seite, Erling Haaland und Martin Ødegaard auf der anderen Seite. England hat den breiteren Kader, Norwegen die Urgewalt im Sturm.\n\nTendenz für Tippspieler: Beide Teams treffen. England setzt sich am Ende aufgrund der individuellen Klasse knapp mit 2:1 oder 3:2 durch."
            }

    # 2. ECHTE KI-ANALYSE (Falls die Live-API doch Daten für eine ID liefert)
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": FOOTBALL_API_KEY
    }
    try:
        fixture_url = f"https://v3.football.api-sports.io/fixtures?id={match_id}"
        fixture_res = requests.get(fixture_url, headers=headers).json()
        spiel = fixture_res["response"][0]
        home_team = spiel["teams"]["home"]["name"]
        away_team = spiel["teams"]["away"]["name"]
        
        lineup_url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={match_id}"
        lineup_res = requests.get(lineup_url, headers=headers).json()
        home_kader = [p["player"]["name"] for p in lineup_res.get("response", [{}, {}])[0].get("startXI", [])]
        away_kader = [p["player"]["name"] for p in lineup_res.get("response", [{}, {}])[1].get("startXI", [])]
        
        if not home_kader: home_kader = ["Kader wird live geladen"]
        if not away_kader: away_kader = ["Kader wird live geladen"]
    except Exception as e:
        return {
            "match_info": {"home": "Spanien", "away": "Belgien"},
            "kader": {"home": ["Yamal"], "away": ["De Bruyne"]},
            "quoten": {"bet365": {"1": "1.70", "X": "3.80", "2": "4.50"}},
            "analyse": "Live-Kader konnten nicht geladen werden, Spanien gewinnt!"
        }

    prompt = f"Analysiere das Spiel {home_team} gegen {away_team}."
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        ki_text = response.choices[0].message.content
    except Exception as e:
        ki_text = f"KI-Analyse fehlgeschlagen."

    return {
        "match_info": {"home": home_team, "away": away_team},
        "kader": {"home": home_kader, "away": away_kader},
        "quoten": {"bet365": {"1": "Live", "X": "Live", "2": "Live"}},
        "analyse": ki_text
    }
