import json
import os
import requests
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

GAMES_FILE = "games.json"

TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")


# ============================================================
# STEAM
# ============================================================

STEAM_GAMES = [
    {
        "name": "Counter-Strike 2",
        "appid": 730
    },
    {
        "name": "Dota 2",
        "appid": 570
    },
    {
        "name": "PUBG: BATTLEGROUNDS",
        "appid": 578080
    },
    {
        "name": "Grand Theft Auto V",
        "appid": 271590
    },
    {
        "name": "Apex Legends",
        "appid": 1172470
    },
    {
        "name": "Rust",
        "appid": 252490
    },
    {
        "name": "Baldur's Gate 3",
        "appid": 1086940
    },
    {
        "name": "Cyberpunk 2077",
        "appid": 1091500
    },
    {
        "name": "Elden Ring",
        "appid": 1245620
    },
    {
        "name": "Helldivers 2",
        "appid": 553850
    },
    {
        "name": "Terraria",
        "appid": 105600
    },
    {
        "name": "Left 4 Dead 2",
        "appid": 550
    },
    {
        "name": "Monster Hunter: World",
        "appid": 582010
    },
    {
        "name": "Palworld",
        "appid": 1623730
    },
    {
        "name": "Dead by Daylight",
        "appid": 381210
    }
]


def get_steam_players(appid):

    url = (
        "https://api.steampowered.com/"
        "ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    )

    try:

        response = requests.get(
            url,
            params={
                "appid": appid
            },
            headers={
                "User-Agent": "Gaming-Trends-Tracker"
            },
            timeout=15
        )

        if response.status_code != 200:
            print(
                f"[STEAM] HTTP {response.status_code} "
                f"pour AppID {appid}"
            )
            return 0

        data = response.json()

        return data.get(
            "response",
            {}
        ).get(
            "player_count",
            0
        )

    except Exception as e:

        print(
            f"[STEAM] Erreur AppID {appid}: {e}"
        )

        return 0


def get_steam_games():

    print("========================================")
    print("MISE A JOUR STEAM")
    print("========================================")

    steam_games = []

    for game in STEAM_GAMES:

        name = game["name"]
        appid = game["appid"]

        players = get_steam_players(appid)

        print(
            f"[STEAM] {name}: "
            f"{players:,} joueurs"
        )

        steam_games.append({

            "name": name,

            "platform": "Steam",

            "metric": players,

            "metric_label": "Joueurs actifs",

            "trend": "+0%",

            "image": (
                "https://cdn.cloudflare.steamstatic.com/"
                f"steam/apps/{appid}/header.jpg"
            ),

            "appid": appid,

            "drops_enabled": False,

            "drop": None,

            "badges": [],

            "emotes": []

        })

    # Plus gros nombre de joueurs en premier

    steam_games.sort(
        key=lambda game: game["metric"],
        reverse=True
    )

    return steam_games


# ============================================================
# TWITCH AUTH
# ============================================================

def get_twitch_token(client_id, client_secret):

    url = "https://id.twitch.tv/oauth2/token"

    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    try:

        response = requests.post(
            url,
            params=params,
            timeout=15
        )

        if response.status_code == 200:

            return response.json().get(
                "access_token"
            )

        print(
            "[TWITCH] Erreur token:",
            response.status_code,
            response.text
        )

    except Exception as e:

        print(
            "[TWITCH] Erreur token:",
            e
        )

    return None


# ============================================================
# TWITCH
# ============================================================

def get_twitch_games():

    print("========================================")
    print("MISE A JOUR TWITCH")
    print("========================================")

    if not TWITCH_CLIENT_ID:
        print("[TWITCH] TWITCH_CLIENT_ID manquant")
        return []

    if not TWITCH_CLIENT_SECRET:
        print("[TWITCH] TWITCH_CLIENT_SECRET manquant")
        return []

    token = get_twitch_token(
        TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET
    )

    if not token:
        print("[TWITCH] Impossible d'obtenir le token")
        return []

    headers = {

        "Client-ID": TWITCH_CLIENT_ID,

        "Authorization": f"Bearer {token}"

    }

    # --------------------------------------------------------
    # TOP 100 JEUX TWITCH
    # --------------------------------------------------------

    games_url = (
        "https://api.twitch.tv/helix/games/top"
    )

    try:

        response = requests.get(
            games_url,
            headers=headers,
            params={
                "first": 100
            },
            timeout=15
        )

    except Exception as e:

        print(
            "[TWITCH] Erreur jeux:",
            e
        )

        return []

    if response.status_code != 200:

        print(
            "[TWITCH] Erreur jeux:",
            response.status_code,
            response.text
        )

        return []

    twitch_games = response.json().get(
        "data",
        []
    )

    # --------------------------------------------------------
    # STREAMS EN DIRECT
    # --------------------------------------------------------

    streams_url = (
        "https://api.twitch.tv/helix/streams"
    )

    viewer_counts = {}

    try:

        streams_response = requests.get(
            streams_url,
            headers=headers,
            params={
                "first": 100
            },
            timeout=15
        )

        if streams_response.status_code == 200:

            streams = streams_response.json().get(
                "data",
                []
            )

            for stream in streams:

                game_id = stream.get(
                    "game_id"
                )

                viewers = stream.get(
                    "viewer_count",
                    0
                )

                if game_id:

                    viewer_counts[game_id] = (
                        viewer_counts.get(
                            game_id,
                            0
                        )
                        + viewers
                    )

    except Exception as e:

        print(
            "[TWITCH] Erreur streams:",
            e
        )

    # --------------------------------------------------------
    # FORMATAGE
    # --------------------------------------------------------

    formatted = []

    for game in twitch_games:

        game_id = game.get(
            "id"
        )

        name = game.get(
            "name",
            "Jeu inconnu"
        )

        box_art_url = game.get(
            "box_art_url",
            ""
        )

        box_art_url = box_art_url.replace(
            "{width}",
            "300"
        ).replace(
            "{height}",
            "400"
        )

        spectators = viewer_counts.get(
            game_id,
            0
        )

        badges = []

        # ----------------------------------------------------
        # TENDANCE
        # ----------------------------------------------------

        if spectators > 50000:

            badges.append({

                "name": "Tendance",

                "icon": "🔥"

            })

        # ----------------------------------------------------
        # DROPS
        #
        # IMPORTANT :
        # On ne prétend plus qu'un jeu possède un Drop
        # simplement parce qu'il est dans une liste.
        # ----------------------------------------------------

        drops_enabled = False

        drop = None

        formatted.append({

            "name": name,

            "platform": "Twitch",

            "metric": spectators,

            "metric_label": "Spectateurs",

            "trend": "+0%",

            "image": box_art_url,

            "twitch_game_id": game_id,

            "drops_enabled": drops_enabled,

            "drop": drop,

            "badges": badges,

            "emotes": []

        })

    # --------------------------------------------------------
    # TRI PAR SPECTATEURS
    # --------------------------------------------------------

    formatted.sort(
        key=lambda game: game["metric"],
        reverse=True
    )

    return formatted


# ============================================================
# CHARGER DROPS
# ============================================================

def load_drops():

    """
    Charge drops.json s'il existe.

    Format attendu :

    [
        {
            "game": "Minecraft",
            "status": "live",
            "campaign": "...",
            "start": "...",
            "end": "...",
            "requirement": "...",
            "rewards": [],
            "connection": "...",
            "url": "..."
        }
    ]
    """

    if not os.path.exists("drops.json"):

        print(
            "[DROPS] drops.json absent"
        )

        return []

    try:

        with open(
            "drops.json",
            "r",
            encoding="utf-8"
        ) as f:

            drops = json.load(f)

            if not isinstance(
                drops,
                list
            ):

                return []

            return drops

    except Exception as e:

        print(
            "[DROPS] Erreur:",
            e
        )

        return []


# ============================================================
# ASSOCIER LES DROPS AUX JEUX
# ============================================================

def attach_drops(games, drops):

    print("========================================")
    print("ASSOCIATION DES DROPS")
    print("========================================")

    now = datetime.now(
        timezone.utc
    )

    for game in games:

        game_name = game.get(
            "name",
            ""
        ).lower().strip()

        matching_drop = None

        for drop in drops:

            drop_game = drop.get(
                "game",
                ""
            ).lower().strip()

            if drop_game != game_name:
                continue

            status = drop.get(
                "status"
            )

            # ------------------------------------------------
            # ON GARDE :
            # live = actif
            # upcoming = à venir
            # ------------------------------------------------

            if status in (
                "live",
                "upcoming"
            ):

                matching_drop = drop

                break

        if matching_drop:

            game["drops_enabled"] = True

            game["drop"] = matching_drop

            game["badges"] = game.get(
                "badges",
                []
            )

            game["badges"].append({

                "name": (
                    "Drop actif"
                    if matching_drop.get("status") == "live"
                    else "Drop à venir"
                ),

                "icon": "🎁"

            })

            print(
                f"[DROPS] {game['name']} "
                f"-> {matching_drop.get('status')}"
            )

        else:

            game["drops_enabled"] = False

            game["drop"] = None

    return games


# ============================================================
# UPDATE GLOBAL
# ============================================================

def update_games():

    print("")
    print("========================================")
    print(" GAMING TRENDS TRACKER")
    print("========================================")
    print("")

    # --------------------------------------------------------
    # STEAM
    # --------------------------------------------------------

    steam_games = get_steam_games()

    # --------------------------------------------------------
    # TWITCH
    # --------------------------------------------------------

    twitch_games = get_twitch_games()

    # --------------------------------------------------------
    # DROPS
    # --------------------------------------------------------

    drops = load_drops()

    # --------------------------------------------------------
    # COMBINAISON
    # --------------------------------------------------------

    all_games = (
        steam_games
        + twitch_games
    )

    # --------------------------------------------------------
    # ASSOCIATION DES DROPS
    # --------------------------------------------------------

    all_games = attach_drops(
        all_games,
        drops
    )

    # --------------------------------------------------------
    # IDS
    # --------------------------------------------------------

    for index, game in enumerate(
        all_games,
        start=1
    ):

        game["id"] = index

    # --------------------------------------------------------
    # SAUVEGARDE
    # --------------------------------------------------------

    with open(
        GAMES_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_games,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("")
    print("========================================")
    print(" MISE A JOUR TERMINEE")
    print("========================================")

    print(
        f"Steam : {len(steam_games)} jeux"
    )

    print(
        f"Twitch : {len(twitch_games)} jeux"
    )

    print(
        f"Drops : {len(drops)} campagnes"
    )

    print(
        f"Total : {len(all_games)} jeux"
    )

    print("")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    update_games()
