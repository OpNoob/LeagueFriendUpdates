import requests

with open("data/riot_key.txt") as f_key:
    api_key = f_key.read()


def getResponse(path, platform: str = "euw1"):
    url = f"https://{platform}.api.riotgames.com" + path
    params = {"api_key": api_key}

    res = requests.get(url, params=params)

    return res.json()


def getResponseR(path, region: str = "europe"):
    url = f"https://{region}.api.riotgames.com" + path
    params = {"api_key": api_key}

    res = requests.get(url, params=params)

    return res.json()


def getSummoner(summoner_name: str, platform: str = "euw1"):
    path = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
    return getResponse(path, platform=platform)


def getSpectator(summoner_id: int = None, summoner_name: str = None, platform: str = "euw1"):
    assert summoner_id is not None or summoner_name is not None  # make sure that either name or id are input

    if summoner_id is None:  # and summoner_name is not None
        summoner_id = getSummoner(summoner_name, platform=platform)["id"]

    path = f"/lol/spectator/v4/active-games/by-summoner/{summoner_id}"
    return getResponse(path, platform=platform)


def isInGame(summoner_id: int = None, summoner_name: str = None, platform: str = "euw1"):
    spectator = getSpectator(summoner_id=summoner_id, summoner_name=summoner_name, platform=platform)
    if "status" in spectator and spectator["status"]["status_code"] == 404:
        return False
    return True


def getMatches(puuid: int = None, summoner_name: str = None, platform: str = "euw1", region: str = "europe"):
    assert puuid is not None or summoner_name is not None  # make sure that either name or id are input

    if puuid is None:  # and summoner_name is not None
        summoner = getSummoner(summoner_name, platform=platform)
        puuid = summoner["puuid"]

    path = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return getResponseR(path, region=region)


def getMatchData(match_ids: list[str] = None, region: str = "europe"):
    for matchId in match_ids:
        path = f"/lol/match/v5/matches/{matchId}"
        yield getResponseR(path, region=region)