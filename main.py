from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend läuft!"}

@app.get("/api/matches")
def get_matches():
    return [
        {"match_id": "wm_live_1", "home": "Frankreich", "away": "Marokko", "date": "Heute"},
        {"match_id": "wm_live_2", "home": "Argentinien", "away": "Deutschland", "date": "Morgen"}
    ]
