import json
import urllib.request

def get_real_steam_data():
    # Liste de jeux populaires avec leur identifiant Steam (AppID)
    games_list = [
        {"id": 1, "name": "Counter-Strike 2", "appid": 730, "platform": "Steam", "trend": "+3%"},
        {"id": 2, "name": "Dota 2", "appid": 570, "platform": "Steam", "trend": "-1%"},
        {"id": 3, "name": "Grand Theft Auto V", "appid": 271590, "platform": "Steam", "trend": "+2%"},
        {"id": 4, "name": "Cyberpunk 2077", "appid": 1091500, "platform": "Steam", "trend": "+5%"},
        {"id": 5, "name": "Baldur's Gate 3", "appid": 1086940, "platform": "Steam", "trend": "-2%"},
        {"id": 6, "name": "Rust", "appid": 252490, "platform": "Steam", "trend": "+4%"}
    ]
    
    updated_data = []
    
    for game in games_list:
        players = 0
        try:
            # Appel de l'API Steam en direct
            url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={game['appid']}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("response", {}).get("result") == 1:
                    players = data["response"].get("player_count", 0)
        except Exception as e:
            print(f"Erreur pour {game['name']}: {e}")
            players = 150000  # Valeur de secours
            
        # Récupération automatique de l'image officielle du jeu via Steam
        image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game['appid']}/header.jpg"
        
        updated_data.append({
            "id": game["id"],
            "name": game["name"],
            "platform": game["platform"],
            "players": players,
            "trend": game["trend"],
            "image": image_url
        })
        
    # Enregistrement dans le fichier JSON
    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    get_real_steam_data()
