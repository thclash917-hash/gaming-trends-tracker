import json
import os
import requests

def get_twitch_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def fetch_live_games():
    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Clés API Twitch manquantes, arrêt du script.")
        return

    token = get_twitch_token(client_id, client_secret)
    if not token:
        print("Impossible d'obtenir le token d'authentification Twitch.")
        return

    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }

    url = "https://api.twitch.tv/helix/games/top?first=30"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Erreur lors de la récupération des jeux Twitch.")
        return

    twitch_games = response.json().get("data", [])
    
    streams_url = "https://api.twitch.tv/helix/streams?first=100"
    streams_response = requests.get(streams_url, headers=headers)
    viewer_counts = {}
    
    if streams_response.status_code == 200:
        for stream in streams_response.json().get("data", []):
            game_id = stream.get("game_id")
            viewers = stream.get("viewer_count", 0)
            viewer_counts[game_id] = viewer_counts.get(game_id, 0) + viewers

    # Liste des jeux qui proposent des drops (tu pourras l'ajuster ou l'enrichir)
    games_with_drops = ["valorant", "rust", "brawl stars", "minecraft", "counter-strike"]

    formatted_games = []
    for index, game in enumerate(twitch_games, start=1):
        game_id = game.get("id")
        name = game.get("name")
        box_art_url = game.get("box_art_url", "").replace("{width}", "300").replace("{height}", "400")
        
        spectators = viewer_counts.get(game_id, 0)
        
        badges = []
        if spectators > 50000:
            badges.append({"name": "Tendance", "icon": "🔥"})
            
        # Activation automatique des drops selon les jeux ciblés
        drops_enabled = False
        name_lower = name.lower()
        if any(drop_game in name_lower for drop_game in games_with_drops):
            drops_enabled = True
            badges.append({"name": "Drops officiels", "icon": "🎁"})
            
        formatted_games.append({
            "id": index,
            "name": name,
            "platform": "Twitch",
            "metric": spectators,
            "metric_label": "Spectateurs",
            "trend": "+0%",
            "image": box_art_url,
            "drops_enabled": drops_enabled,
            "badges": badges,
            "emotes": []
        })

    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(formatted_games, f, ensure_ascii=False, indent=2)
    
    print("Fichier games.json mis à jour avec les drops !")

if __name__ == "__main__":
    fetch_live_games()
