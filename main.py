import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai

app = FastAPI(title="WM-Tipp-Analysator")

# Erlaube dem Frontend, auf das Backend zuzugreifen (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-Keys (Sollten später über Umgebungsvariablen geladen werden)
OPENAI_API_KEY = "DEIN_OPENAI_API_KEY"
FOOTBALL_API_KEY = "DEIN_FOOTBALL_DATA_API_KEY"
ODDS_API_KEY = "DEIN_THE_ODDS_API_KEY"

openai.api_key = OPENAI_API_KEY

# Cache, um Kosten zu sparen (Simpelt im Arbeitsspeicher geloggt)
analysis_cache = {}

def fetch_match_data(match_id: str):
    """
    Simuliert den Abruf von Echtzeitdaten von einer Fußball-API (z.B. API-Football).
    Hier würden Kader, letzte Spiele und News geladen.
    """
    # In der Praxis: requests.get(f"https://v3.football.api-sports.io/fixtures?id={match_id}", headers=...)
    demo_daten = {
        "team_home": "Deutschland",
        "team_away": "Argentinien",
        "home_kader": ["Musiala", "Wirtz", "Havertz", "Kimmich", "Rüdiger"],
        "away_kader": ["Messi", "Alvarez", "Mac Allister", "De Paul", "Romero"],
        "home_last_5": ["Sieg gegen Spanien (2:1)", "Sieg gegen Schottland (3:0)", "Unentschieden gegen Schweiz (1:1)"],
        "away_last_5": ["Sieg gegen Brasilien (1:0)", "Sieg gegen Chile (2:0)", "Niederlage gegen Kolumbien (1:2)"],
        "news": "Deutschland tritt mit voller Offensivkraft an. Bei Argentinien steht der Einsatz von De Paul wegen einer leichten Blessur noch auf der Kippe."
    }
    return demo_daten

def fetch_odds(team_home: str, team_away: str):
    """ Holt aktuelle Wettquoten """
    # In der Praxis: API-Abruf von The Odds API
    return {"bwin": {"1": 2.10, "X": 3.40, "2": 3.10}, "bet365": {"1": 2.15, "X": 3.45, "2": 3.00}}

@app.get("/api/analysis/{match_id}")
def get_match_analysis(match_id: str):
    # 1. Prüfen, ob Analyse bereits im Cache ist
    if match_id in analysis_cache:
        return analysis_cache[match_id]
    
    # 2. Daten von APIs abrufen
    try:
        match_data = fetch_match_data(match_id)
        odds_data = fetch_odds(match_data["team_home"], match_data["team_away"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Fußballdaten: {str(e)}")

    # 3. Prompt für die KI vorbereiten
    prompt = f"""
    Analysiere das kommende WM-Spiel als professioneller Fußball-Experte und Buchmacher.
    
    Beide Teams: {match_data['team_home']} vs. {match_data['team_away']}
    
    Aktueller Kader Heimteam: {', '.join(match_data['home_kader'])}
    Aktueller Kader Auswärtsteam: {', '.join(match_data['away_kader'])}
    
    Letzte Spiele Heimteam: {', '.join(match_data['home_last_5'])}
    Letzte Spiele Auswärtsteam: {', '.join(match_data['away_last_5'])}
    
    Aktuelle News: {match_data['news']}
    Aktuelle Wettquoten (Schnitt): Sieg Heim: {odds_data['bet365']['1']}, Unentschieden: {odds_data['bet365']['X']}, Sieg Auswärts: {odds_data['bet365']['2']}
    
    Erstelle eine fundierte Analyse. Setze die Formkurve, die Kader-Verfügbarkeit und die Quoten in den Kontext.
    Gib am Ende einen konkreten Ergebnis-Tipp ab (z.B. 2:1) und eine kurze Begründung für Tippspieler.
    """

    # 4. KI-Analyse via OpenAI generieren
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du bist ein präziser, analytischer Sportjournalist und Daten-Analyst für Fußball-Weltmeisterschaften."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        ki_text = response.choices[0].message.content
    except Exception as e:
        ki_text = f"KI-Analyse temporär nicht verfügbar. (Fehler: {str(e)})"

    # 5. Gesamtes Ergebnis zusammenbauen
    ergebnis = {
        "match_info": {
            "home": match_data["team_home"],
            "away": match_data["team_away"],
        },
        "kader": {
            "home": match_data["home_kader"],
            "away": match_data["away_kader"]
        },
        "quoten": odds_data,
        "analyse": ki_text
    }

    # Im Cache speichern
    analysis_cache[match_id] = ergebnis
    return ergebnis

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
