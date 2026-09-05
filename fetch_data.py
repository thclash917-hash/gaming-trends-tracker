import json
import urllib.request

def get_steam_top_games():
    # URL de l'API publique Steam pour les jeux les plus populaires
    url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=730" # Exemple avec CS2, ou utiliser une source globale
    # Alternative plus simple : utiliser un fichier JSON structuré ou l'API Steam Spy / Steam Store
    
    # Pour l'instant, structurons un format de données propre que votre site affichera :
    games_data = [
        {"id": 1, "name": "Counter-Strike 2", "players": 1250000, "platform": "Steam", "trend": "+5%"},
        {"id": 2, "name": "Dota 2", "players": 680000, "platform": "Steam", "trend": "-2%"},
        {"id": 3, "name": "Grand Theft Auto V", "players": 180000, "platform": "Steam", "trend": "+1%"}
    ]
    
    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(games_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    get_steam_top_games()
