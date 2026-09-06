import json
import re
import requests
from datetime import datetime, timezone


DROPS_FILE = "drops.json"

API_URL = "https://ttvdrops.lovinator.space/api/v1/twitch/campaigns/"

HEADERS = {
    "User-Agent": "Gaming-Trends-Tracker/1.0"
}

PAGE_SIZE = 100


# ============================================================
# DATES
# ============================================================

def parse_date(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except Exception:
        return None


def calculate_status(start_at, end_at):
    now = datetime.now(timezone.utc)

    start = parse_date(start_at)
    end = parse_date(end_at)

    if not start:
        return None

    if start > now:
        return "upcoming"

    if end and end < now:
        return "expired"

    return "live"


# ============================================================
# WATCH TIME
# ============================================================

def extract_watch_time(text):
    if not text:
        return ""

    patterns = [
        r"(\d+)\s*(?:minutes?|mins?)\s*(?:watched|watch)",
        r"(\d+)\s*(?:hours?|hrs?)\s*(?:watched|watch)",
        r"(\d+)\s*m(?:in)?\s*-\s*(\d+)\s*m",
        r"(\d+)\s*m\s*watch",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            groups = match.groups()

            if len(groups) == 2:
                return f"{groups[0]}-{groups[1]} minutes"

            value = groups[0]

            if "hour" in pattern:
                return f"{value} heures"

            return f"{value} minutes"

    return ""


# ============================================================
# RECUPERATION API
# ============================================================

def fetch_campaigns():

    print("")
    print("========================================")
    print(" RECUPERATION DES TWITCH DROPS")
    print("========================================")

    campaigns = []

    page = 1

    while True:

        print(
            f"[DROPS] Page {page}"
        )

        try:

            response = requests.get(
                API_URL,
                params={
                    "page": page,
                    "page_size": PAGE_SIZE
                },
                headers=HEADERS,
                timeout=30
            )

        except Exception as e:

            print(
                f"[DROPS] Erreur réseau : {e}"
            )

            break

        if response.status_code != 200:

            print(
                "[DROPS] HTTP",
                response.status_code
            )

            print(
                response.text[:500]
            )

            break

        try:

            data = response.json()

        except Exception as e:

            print(
                "[DROPS] JSON invalide :",
                e
            )

            break

        items = data.get(
            "items",
            []
        )

        if not items:
            break

        campaigns.extend(items)

        total = data.get(
            "total",
            0
        )

        print(
            f"[DROPS] {len(campaigns)} / {total}"
        )

        if len(campaigns) >= total:
            break

        page += 1

        # sécurité
        if page > 250:
            print(
                "[DROPS] Limite de pages atteinte"
            )
            break

    return campaigns


# ============================================================
# TRANSFORMATION
# ============================================================

def transform_campaign(campaign):

    game = campaign.get(
        "game",
        {}
    )

    game_name = (
        game.get("display_name")
        or game.get("name")
        or ""
    ).strip()

    campaign_name = (
        campaign.get("name")
        or "Twitch Drop"
    ).strip()

    start_at = campaign.get(
        "start_at"
    )

    end_at = campaign.get(
        "end_at"
    )

    status = calculate_status(
        start_at,
        end_at
    )

    # On ignore ce qui est expiré
    if status == "expired":
        return None

    description = (
        campaign.get(
            "description"
        )
        or ""
    )

    watch_time = extract_watch_time(
        description
    )

    return {

        "game": game_name,

        "status": status,

        "campaign": campaign_name,

        "start": start_at,

        "end": end_at,

        "watch_time": watch_time,

        "requirements": [],

        "rewards": [],

        "description": description,

        "image": campaign.get(
            "image_url"
        ),

        "url": campaign.get(
            "details_url"
        ),

        "account_link": campaign.get(
            "account_link_url"
        ),

        "twitch_campaign_id": campaign.get(
            "twitch_id"
        )

    }


# ============================================================
# NETTOYAGE
# ============================================================

def clean_duplicates(drops):

    unique = {}

    for drop in drops:

        key = (
            drop.get(
                "game",
                ""
            ).lower().strip(),

            drop.get(
                "twitch_campaign_id",
                ""
            )
        )

        unique[key] = drop

    return list(
        unique.values()
    )


# ============================================================
# MAIN
# ============================================================

def update_drops():

    campaigns = fetch_campaigns()

    print(
        f"[DROPS] {len(campaigns)} campagnes récupérées"
    )

    drops = []

    for campaign in campaigns:

        drop = transform_campaign(
            campaign
        )

        if not drop:
            continue

        if not drop.get("game"):
            continue

        drops.append(
            drop
        )

    drops = clean_duplicates(
        drops
    )

    # Trier :
    # live avant upcoming
    drops.sort(
        key=lambda x: (
            0
            if x.get("status") == "live"
            else 1,
            x.get("game", "").lower()
        )
    )

    with open(
        DROPS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            drops,
            f,
            ensure_ascii=False,
            indent=2
        )

    live = sum(
        1
        for drop in drops
        if drop.get("status") == "live"
    )

    upcoming = sum(
        1
        for drop in drops
        if drop.get("status") == "upcoming"
    )

    print("")
    print("========================================")
    print(" DROPS MIS A JOUR")
    print("========================================")
    print(
        f"Campagnes : {len(drops)}"
    )
    print(
        f"Actives   : {live}"
    )
    print(
        f"A venir   : {upcoming}"
    )
    print(
        f"Fichier   : {DROPS_FILE}"
    )
    print("")


if __name__ == "__main__":
    update_drops()
