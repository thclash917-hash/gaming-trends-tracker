import json

def update_games():
    try:
        with open("games.json", "r", encoding="utf-8") as f:
            games = json.load(f)
    except FileNotFoundError:
        games = []

    # Exemple de logique automatique : active les drops pour certains jeux clés
    for game in games:
        name = game.get("name", "").lower()
        
        if "valorant" in name or "rust" in name or "brawl stars" in name:
            game["drops_enabled"] = True
            # Ajoute un badge s'il n'est pas déjà présent
            if not any(b.get("name") == "Drops officiels" for b in game.get("badges", [])):
                if "badges" not in game:
                    game["badges"] = []
                game["badges"].append({"name": "Drops officiels", "icon": "🔥"})

    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)
    
    print("Mise à jour réussie de games.json")

if __name__ == "__main__":
    update_games()
