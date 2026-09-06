import json
import os
import requests
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

GAMES_FILE = "games.json"
DROPS_FILE = "drops.json"

TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")


# ============================================================
# STEAM
# ============================================================

STEAM_GAMES = [
    {"name": "Counter-Strike 2", "appid": 730},
    {"name": "Dota 2", "appid": 570},
    {"name": "PUBG: BATTLEGROUNDS", "appid": 578080},
    {"name": "Grand Theft Auto V", "appid": 271590},
    {"name": "Apex Legends", "appid": 1172470},
    {"name": "Rust", "appid": 252490},
    {"name": "Baldur's Gate 3", "appid": 1086940},
    {"name": "Cyberpunk 2077", "appid": 1091500},
    {"name": "Elden Ring", "appid": 1245620},
    {"name": "Helldivers 2", "appid": 553850},
    {"name": "Terraria", "appid": 105600},
    {"name": "Left 4 Dead 2", "appid": 550},
    {"name": "Monster Hunter: World", "appid": 582010},
    {"name": "Palworld", "appid": 1623730},
    {"name": "Dead by Daylight", "appid": 381210},
]


def get_steam_players(appid):
    url = (
        "https://api.steampowered.com/"
        "ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    )

    try:
        response = requests.get(
            url,
            params={"appid": appid},
            headers={
                "User-Agent": "Gaming-Trends-Tracker/1.0"
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

    print("")
    print("========================================")
    print(" MISE A JOUR STEAM")
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
            "drops": [],
            "badges": [],
            "emotes": []
        })

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

            token = response.json().get(
                "access_token"
            )

            if token:
                print("[TWITCH] Token obtenu")
                return token

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

    print("")
    print("========================================")
    print(" MISE A JOUR TWITCH")
    print("========================================")

    if not TWITCH_CLIENT_ID:
        print(
            "[TWITCH] TWITCH_CLIENT_ID manquant"
        )
        return []

    if not TWITCH_CLIENT_SECRET:
        print(
            "[TWITCH] TWITCH_CLIENT_SECRET manquant"
        )
        return []

    token = get_twitch_token(
        TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET
    )

    if not token:
        print(
            "[TWITCH] Impossible d'obtenir le token"
        )
        return []

    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    # ========================================================
    # TOP 100 JEUX
    # ========================================================

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

    print(
        f"[TWITCH] {len(twitch_games)} jeux récupérés"
    )

    # ========================================================
    # STREAMS
    # ========================================================

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

            print(
                f"[TWITCH] {len(streams)} streams analysés"
            )

        else:

            print(
                "[TWITCH] Erreur streams:",
                streams_response.status_code
            )

    except Exception as e:

        print(
            "[TWITCH] Erreur streams:",
            e
        )

    # ========================================================
    # FORMATAGE
    # ========================================================

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

        # ====================================================
        # TENDANCE
        # ====================================================

        if spectators > 50000:

            badges.append({
                "name": "Tendance",
                "icon": "🔥"
            })

        formatted.append({

            "name": name,

            "platform": "Twitch",

            "metric": spectators,

            "metric_label": "Spectateurs",

            "trend": "+0%",

            "image": box_art_url,

            "twitch_game_id": game_id,

            "drops_enabled": False,

            "drops": [],

            "badges": badges,

            "emotes": []

        })

    # ========================================================
    # TRI
    # ========================================================

    formatted.sort(
        key=lambda game: game["metric"],
        reverse=True
    )

    return formatted


# ============================================================
# DROPS
# ============================================================

def parse_date(value):

    if not value:
        return None

    try:

        value = value.strip()

        # Support YYYY-MM-DD
        if len(value) == 10:
            return datetime.fromisoformat(
                value
            ).replace(
                tzinfo=timezone.utc
            )

        # Support ISO + Z
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

    except Exception as e:

        print(
            f"[DROPS] Date invalide '{value}': {e}"
        )

        return None


def get_drop_status(drop):

    """
    Détermine automatiquement le statut :

    upcoming = avant la date de début
    live     = entre début et fin
    expired  = après la date de fin
    """

    now = datetime.now(
        timezone.utc
    )

    start = parse_date(
        drop.get("start")
    )

    end = parse_date(
        drop.get("end")
    )

    # Si les dates sont absentes,
    # on utilise le status fourni.
    if not start and not end:

        status = str(
            drop.get(
                "status",
                ""
            )
        ).lower()

        if status in (
            "live",
            "active"
        ):
            return "live"

        if status in (
            "upcoming",
            "coming"
        ):
            return "upcoming"

        return "expired"

    # Pas encore commencé
    if start and now < start:
        return "upcoming"

    # Terminé
    if end and now > end:
        return "expired"

    # En cours
    return "live"


def load_drops():

    print("")
    print("========================================")
    print(" CHARGEMENT DES DROPS")
    print("========================================")

    if not os.path.exists(
        DROPS_FILE
    ):

        print(
            "[DROPS] drops.json absent"
        )

        return []

    try:

        with open(
            DROPS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            drops = json.load(f)

        if not isinstance(
            drops,
            list
        ):

            print(
                "[DROPS] drops.json doit contenir une liste"
            )

            return []

        valid_drops = []

        for drop in drops:

            if not isinstance(
                drop,
                dict
            ):
                continue

            game = drop.get(
                "game"
            )

            if not game:
                continue

            status = get_drop_status(
                drop
            )

            # ------------------------------------------------
            # ON IGNORE LES DROPS EXPIRÉS
            # ------------------------------------------------

            if status == "expired":

                print(
                    f"[DROPS] Expiré : {game}"
                )

                continue

            # ------------------------------------------------
            # ON NORMALISE LE STATUS
            # ------------------------------------------------

            drop["status"] = status

            # ------------------------------------------------
            # Valeurs par défaut
            # ------------------------------------------------

            if not isinstance(
                drop.get("rewards"),
                list
            ):
                drop["rewards"] = []

            if not isinstance(
                drop.get("requirements"),
                list
            ):
                drop["requirements"] = []

            valid_drops.append(
                drop
            )

            print(
                f"[DROPS] {game} -> {status}"
            )

        print(
            f"[DROPS] {len(valid_drops)} campagnes valides"
        )

        return valid_drops

    except Exception as e:

        print(
            "[DROPS] Erreur lecture:",
            e
        )

        return []


# ============================================================
# ASSOCIATION DROPS
# ============================================================

def attach_drops(games, drops):

    print("")
    print("========================================")
    print(" ASSOCIATION DES DROPS")
    print("========================================")

    # Dictionnaire :
    #
    # "valorant" -> [drop1, drop2]
    #
    drops_by_game = {}

    for drop in drops:

        game_name = str(
            drop.get(
                "game",
                ""
            )
        ).lower().strip()

        if not game_name:
            continue

        if game_name not in drops_by_game:
            drops_by_game[game_name] = []

        drops_by_game[
            game_name
        ].append(
            drop
        )

    for game in games:

        game_name = str(
            game.get(
                "name",
                ""
            )
        ).lower().strip()

        matching_drops = drops_by_game.get(
            game_name,
            []
        )

        # ----------------------------------------------------
        # Aucun Drop
        # ----------------------------------------------------

        if not matching_drops:

            game["drops_enabled"] = False
            game["drops"] = []

            continue

        # ----------------------------------------------------
        # Drops trouvés
        # ----------------------------------------------------

        game["drops_enabled"] = True

        game["drops"] = matching_drops

        badges = game.get(
            "badges",
            []
        )

        # Évite les doublons
        badges = [
            badge
            for badge in badges
            if badge.get(
                "name"
            ) not in (
                "Drop actif",
                "Drop à venir",
                "Drops disponibles"
            )
        ]

        # ----------------------------------------------------
        # Badge selon le statut
        # ----------------------------------------------------

        has_live = any(
            drop.get("status") == "live"
            for drop in matching_drops
        )

        has_upcoming = any(
            drop.get("status") == "upcoming"
            for drop in matching_drops
        )

        if has_live:

            badges.append({
                "name": "Drop actif",
                "icon": "🎁"
            })

        elif has_upcoming:

            badges.append({
                "name": "Drop à venir",
                "icon": "🎁"
            })

        game["badges"] = badges

        print(
            f"[DROPS] {game['name']} "
            f"-> {len(matching_drops)} campagne(s)"
        )

    return games


# ============================================================
# NETTOYAGE DES DOUBLONS
# ============================================================

def remove_duplicates(games):

    unique_games = []
    seen = set()

    for game in games:

        key = (
            game.get("platform"),
            game.get("name", "").lower().strip()
        )

        if key in seen:
            continue

        seen.add(key)
        unique_games.append(game)

    return unique_games


# ============================================================
# UPDATE GLOBAL
# ============================================================

def update_games():

    print("")
    print("========================================")
    print("      GAMING TRENDS TRACKER")
    print("========================================")
    print("")

    # ========================================================
    # STEAM
    # ========================================================

    steam_games = get_steam_games()

    # ========================================================
    # TWITCH
    # ========================================================

    twitch_games = get_twitch_games()

    # ========================================================
    # DROPS
    # ========================================================

    drops = load_drops()

    # ========================================================
    # COMBINAISON
    # ========================================================

    all_games = (
        steam_games
        + twitch_games
    )

    # ========================================================
    # SUPPRESSION DES DOUBLONS
    # ========================================================

    all_games = remove_duplicates(
        all_games
    )

    # ========================================================
    # ASSOCIATION DROPS
    # ========================================================

    all_games = attach_drops(
        all_games,
        drops
    )

    # ========================================================
    # IDS
    # ========================================================

    for index, game in enumerate(
        all_games,
        start=1
    ):

        game["id"] = index

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    try:

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
            f"Steam  : {len(steam_games)} jeux"
        )

        print(
            f"Twitch : {len(twitch_games)} jeux"
        )

        print(
            f"Drops  : {len(drops)} campagnes"
        )

        print(
            f"Total  : {len(all_games)} jeux"
        )

        print(
            f"Fichier : {GAMES_FILE}"
        )

        print("")

    except Exception as e:

        print(
            "[ERREUR] Impossible d'écrire games.json:",
            e
        )

        raise


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    update_games()
