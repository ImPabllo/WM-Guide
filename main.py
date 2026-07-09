import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import openai

app = FastAPI(title="WM-Tipp-Analysator Live")

# Erlaube dem Frontend den Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ HIER DEINE ECHTEN SCHLÜSSEL EINTRAGEN 
OPENAI_API_KEY = dae0dec90dc68e23baf56e3d09afd0b6
FOOTBALL_API_KEY = a0c04b4f55ae47e585acb706a3e6a1a1

openai.api_key = OPENAI_API_KEY

@app.get("/api/matches")
def get_upcoming_matches():
    """ Holt die nächsten echten Spiele live aus dem Internet """
    # Liga 1 ist in API-Football oft die Weltmeisterschaft
    url = "https://v3.football.api-sports.io/fixtures?league=1&next=5" 
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
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail="Fehler beim Laden der echten Spiele")

@app.get("/api/analysis/{match_id}")
def get_match_analysis(match_id: str):
    """ Holt Spieldaten für ein spezifisches echtes Spiel und analysiert es """
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": FOOTBALL_API_KEY
    }
    
    try:
        # 1. Echte Spieldaten abrufen (Letzte Ergebnisse & Status)
        fixture_url = f"https://v3.football.api-sports.io/fixtures?id={match_id}"
        fixture_res = requests.get(fixture_url, headers=headers).json()
        
        if not fixture_res.get("response"):
            raise HTTPException(status_code=404, detail="Spiel nicht gefunden")
            
        spiel = fixture_res["response"][0]
        home_team = spiel["teams"]["home"]["name"]
        away_team = spiel["teams"]["away"]["name"]
        
        # 2. Aktuelle Kader/Aufstellungen abrufen
        lineup_url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={match_id}"
        lineup_res = requests.get(lineup_url, headers=headers).json()
        
        # Kader auslesen (falls schon verfügbar, sonst leer)
        home_kader = [p["player"]["name"] for p in lineup_res.get("response", [{}, {}])[0].get("startXI", [])]
        away_kader = [p["player"]["name"] for p in lineup_res.get("response", [{}, {}])[1].get("startXI", [])]
        
        if not home_kader: home_kader = ["Kader wird kurz vor Anpfiff bekanntgegeben"]
        if not away_kader: away_kader = ["Kader wird kurz vor Anpfiff bekanntgegeben"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Live-Daten: {str(e)}")

    # 3. KI-Prompt mit echten Daten füttern
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

    # 4. OpenAI nach der Analyse fragen
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
        "quoten": {"Hinweis": "Echte Quoten-API optional verfügbar"},
        "analyse": ki_text
    }
