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

def update_games():
    # 1. Charger l'ancien fichier pour récupérer et préserver les jeux Steam ou autres plateformes
    try:
        with open("games.json", "r", encoding="utf-8") as f:
            existing_games = json.load(f)
    except FileNotFoundError:
        existing_games = []

    # Garder uniquement les jeux qui ne viennent pas de Twitch (ex: Steam)
    non_twitch_games = [g for g in existing_games if g.get("platform") != "Twitch"]

    # 2. Récupérer les données en direct de l'API Twitch
    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    
    twitch_games_formatted = []
    if client_id and client_secret:
        token = get_twitch_token(client_id, client_secret)
        if token:
            headers = {
                "Client-ID": client_id,
                "Authorization": f"Bearer {token}"
            }

            # Top 100 Twitch
            url = "https://api.twitch.tv/helix/games/top?first=100"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                twitch_games = response.json().get("data", [])
                
                # Récupération des spectateurs en direct
                streams_url = "https://api.twitch.tv/helix/streams?first=100"
                streams_response = requests.get(streams_url, headers=headers)
                viewer_counts = {}
                
                if streams_response.status_code == 200:
                    for stream in streams_response.json().get("data", []):
                        game_id = stream.get("game_id")
                        viewers = stream.get("viewer_count", 0)
                        viewer_counts[game_id] = viewer_counts.get(game_id, 0) + viewers

                games_with_drops = ["valorant", "rust", "brawl stars", "minecraft", "counter-strike"]

                for index, game in enumerate(twitch_games, start=1):
                    game_id = game.get("id")
                    name = game.get("name")
                    box_art_url = game.get("box_art_url", "").replace("{width}", "300").replace("{height}", "400")
                    spectators = viewer_counts.get(game_id, 0)
                    
                    badges = []
                    if spectators > 50000:
                        badges.append({"name": "Tendance", "icon": "🔥"})
                        
                    drops_enabled = False
                    name_lower = name.lower()
                    if any(drop_game in name_lower for drop_game in games_with_drops):
                        drops_enabled = True
                        badges.append({
                            "name": "Drops officiels", 
                            "icon": "🎁", 
                            "url": "https://www.twitch.tv/drops/campaigns"
                        })
                        
                    twitch_games_formatted.append({
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

    # 3. Combiner les jeux Steam et les nouveaux jeux Twitch mis à jour
    all_games = non_twitch_games + twitch_games_formatted

    # Réattribuer des IDs uniques propres
    for i, game in enumerate(all_games, start=1):
        game["id"] = i

    # Sauvegarde
    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=2)
    
    print("Mise à jour combinée réussie (Steam + Twitch en direct) !")

if __name__ == "__main__":
    update_games()
