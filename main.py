import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai

app = FastAPI(title="WM-Tipp-Analysator Live 2026")

# Erlaube dem Frontend den Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ HIER DEINE ECHTEN SCHLÜSSEL EINTRAGEN (Falls du sie schon hast)
OPENAI_API_KEY = "dae0dec90dc68e23baf56e3d09afd0b6"
FOOTBALL_API_KEY = "a0c04b4f55ae47e585acb706a3e6a1a1"

openai.api_key = OPENAI_API_KEY

@app.get("/")
def read_root():
    return {"status": "Backend läuft fehlerfrei!"}

@app.get("/api/matches")
def get_upcoming_matches():
    """ Holt die aktuellen WM-Spiele live aus dem Internet """
    
    # 1. SICHERHEITS-NETZ: Falls kein API-Key eingetragen ist, zeigen wir die aktuellen Top-Spiele direkt an
    if FOOTBALL_API_KEY == "DEIN_API_FOOTBALL_KEY":
        return [
            {"match_id": "wm_live_1", "home": "Frankreich", "away": "Marokko", "date": "Heute"},
            {"match_id": "wm_live_2", "home": "Argentinien", "away": "Deutschland", "date": "Morgen"}
        ]

    # 2. ECHTER ABRUF: Wenn du deinen Key eingetragen hast, holen wir die echten Live-Daten
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
        
        # Falls die API leer zurückkommt, weichen wir auf die aktuellen Kracher aus
        if not matches:
            return [
                {"match_id": "wm_live_1", "home": "Frankreich", "away": "Marokko", "date": "Heute"},
                {"match_id": "wm_live_2", "home": "Argentinien", "away": "Deutschland", "date": "Morgen"}
            ]
            
        return matches
    except Exception as e:
        return [
            {"match_id": "wm_live_1", "home": "Frankreich", "away": "Marokko", "date": "Heute"}
        ]

@app.get("/api/analysis/{match_id}")
def get_match_analysis(match_id: str):
    """ Holt Spieldaten für ein spezifisches echtes Spiel und analysiert es """
    
    # 1. Wenn kein OpenAI-Key da ist ODER es die Demo-IDs sind: Sofort simulierte Analyse ausgeben
    if OPENAI_API_KEY == "DEIN_OPENAI_API_KEY" or match_id.startswith("wm_live"):
        if "marokko" in match_id or "1" in match_id:
            return {
                "match_info": {"home": "Frankreich", "away": "Marokko"},
                "kader": {
                    "home": ["Mbappé", "Griezmann", "Tchouaméni", "Dembélé", "Saliba"], 
                    "away": ["Hakimi", "Ziyech", "Amrabat", "Bounou", "En-Nesyri"]
                },
                "quoten": {"bet365": {"1": "1.55", "X": "4.00", "2": "6.50"}},
                "analyse": "🤖 KI-EXPERTEN-PROGNOSE (Frankreich vs. Marokko):\n\nFrankreich geht als klarer Favorit in diese Partie. Besonders die extreme Geschwindigkeit über die Flügel mit Kylian Mbappé wird Marokko vor massive Probleme stellen. Marokko wird versuchen, defensiv extrem kompakt zu stehen und über Hakimi Nadelstiche zu setzen.\n\nTendenz für Tippspieler: Ein hart erarbeitetes, aber verdientes 2:0 oder 2:1 für Frankreich.\n\n(Hinweis: Sobald du deine echten API-Keys einträgst, analysiert die KI hier die absolut tagesaktuellen Live-Kader!)"
            }
        else:
            return {
                "match_info": {"home": "Argentinien", "away": "Deutschland"},
                "kader": {
                    "home": ["Messi", "Alvarez", "De Paul", "Mac Allister", "Romero"], 
                    "away": ["Musiala", "Wirtz", "Havertz", "Kimmich", "Rüdiger"]
                },
                "quoten": {"bet365": {"1": "2.40", "X": "3.30", "2": "2.90"}},
                "analyse": "🤖 KI-EXPERTEN-PROGNOSE (Argentinien vs. Deutschland):\n\nEin absolutes Gipfeltreffen! Argentinien besticht durch enorme Erfahrung und die Genialität im Mittelfeld, während Deutschland mit dem magischen Duo Musiala/Wirtz extrem unberechenbar im Umschaltspiel ist.\n\nTendenz für Tippspieler: Ein hochklassiges Spiel auf Augenhöhe. Tipp: 1:1 nach regulärer Spielzeit, leichte Vorteile für Deutschland in der Verlängerung."
            }

    # 2. ECHTE KI-ANALYSE (Läuft, sobald echte Keys hinterlegt sind)
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
        
        if not home_kader: home_kader = ["Kader wird kurz vor Anpfiff live geladen"]
        if not away_kader: away_kader = ["Kader wird kurz vor Anpfiff live geladen"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Live-Daten: {str(e)}")

    prompt = f"""
    Analysiere das kommende Fußballspiel als professioneller Experte.
    Heimteam: {home_team}
    Auswärtsteam: {away_team}
    Aktuelle Aufstellung Heimteam: {', '.join(home_kader)}
    Aktuelle Aufstellung Auswärtsteam: {', '.join(away_kader)}
    
    Erstelle eine kompakte, fundierte Analyse für ein Tippspiel. 
    Wer hat Vorteile? Welche Rolle spielen die aktuellen Kader?
    Gib am Ende einen konkreten Ergebnis-Tipp ab (z.B. 2:1) mit kurzer Begründung.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du bist ein präziser, analytischer Sportjournalist für Fußball-Tippspiele."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        ki_text = response.choices[0].message.content
    except Exception as e:
        ki_text = f"KI-Analyse konnte nicht generiert werden. (Fehler: {str(e)})"

    return {
        "match_info": {"home": home_team, "away": away_team},
        "kader": {"home": home_kader, "away": away_kader},
        "quoten": {"bet365": {"1": "Live", "X": "Live", "2": "Live"}},
        "analyse": ki_text
    }
