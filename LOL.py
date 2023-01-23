from collections import Counter
from datetime import datetime

import LOLbase
from data import DataStore
from server_data import ServerData, LiveTracking
import time

"""
Resources: 
https://developer.riotgames.com/docs/lol#routing-values_platform-routing-values
https://developer.riotgames.com/apis#match-v5/GET_getMatch
"""


def convert_from_ms(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    seconds = seconds + milliseconds / 1000
    return days, hours, minutes, seconds


def ms_to_str(milliseconds):
    days, hours, minutes, seconds = convert_from_ms(milliseconds)
    if days:
        return f"{days} days {hours} hrs {minutes} minutes {seconds} seconds"
    elif hours:
        return f"{hours} hrs {minutes} minutes {seconds} seconds"
    elif minutes:
        return f"{minutes} minutes {seconds} seconds"
    elif seconds:
        return f"{seconds} seconds"
    return milliseconds


ds = DataStore()
sd = ServerData()


def getGameResultUpdates(force=False):
    lt = LiveTracking(sd.getTracking())
    summoners_track = lt.getSummoners()

    summoners = set(ds.getSummoners())

    for summoner in summoners:
        name, platform, region = summoner

        matches = LOLbase.getMatches(summoner_name=name, platform=platform, region=region)
        # print(matches)
        for match_data in LOLbase.getMatchData(matches):
            # print(match_data)
            match_id = match_data['metadata']["matchId"]
            success = ds.addMatch(name=name, platform=platform, region=region, match=match_data, match_id=match_id)
            if not success and not force:
                break

            # ANNOUNCE
            if summoner in summoners_track:
                participant = getSummonerFromMatch(match_data, name)
                kills = participant["kills"]
                deaths = participant["deaths"]
                assists = participant["assists"]
                lane = participant["lane"]
                win = participant["win"]
                champion = participant["championName"]
                yield name, kills, deaths, assists, win, lane, champion

    # Saving
    ds.commit()


def getSummonerFromMatch(match_data, summoner_name):
    info = match_data["info"]
    for participant in info["participants"]:
        if participant["summonerName"].lower() == summoner_name.lower():
            return participant


def getStats(summoner_name, platform="euw1", region="europe", return_text=True):
    earliest_dt = datetime.now()
    duration_s = 0
    kills = 0
    deaths = 0
    assists = 0
    wins = 0
    losses = 0

    lanes = Counter()
    champions = Counter()

    matches = ds.getMatches(summoner_name, platform=platform, region=region)
    if matches is None:
        if return_text:
            return f"Summoner {summoner_name} data not found"
        return None
    for match in matches:
        info = match["info"]

        start_dt = datetime.fromtimestamp(info["gameCreation"] // 1000)
        duration_s += info["gameDuration"]
        if start_dt < earliest_dt:
            earliest_dt = start_dt

        participant = getSummonerFromMatch(match, summoner_name)
        kills += participant["kills"]
        deaths += participant["deaths"]
        assists += participant["assists"]
        if participant["win"]:
            wins += 1
        else:
            losses += 1

        lanes.update([participant["lane"]])
        champions.update([participant["championName"]])

    if return_text:
        lanes_common = lanes.most_common(1)
        if len(lanes_common) >= 1:
            lane = lanes_common[0]
        else:
            lane = (None, None)
        champions_common = champions.most_common(1)
        if len(champions_common) >= 1:
            champion = champions_common[0]
        else:
            champion = (None, None)

        text = f"NAME: {summoner_name}\n\nStats Since: {str(earliest_dt.date())}\nPlaying Duration: {ms_to_str(duration_s * 1000)}\n\nTotal Kills: {kills}\nTotal Deaths: {deaths}\nTotal Assists: {assists}\nTotal Wins: {wins}\nTotal losses: {losses}\n\nFavourite Lane: {lane[0]} ({lane[1]} times)\nFavourite Champion: {champion[0]} ({champion[1]} times)"
        return text
    return earliest_dt, duration_s, kills, deaths, assists, wins, losses, lanes, champions


def getActive(return_all=False):
    summoners = set(ds.getSummoners())

    active = set()

    for summoner in summoners:
        name, platform, region = summoner

        if LOLbase.isInGame(summoner_name=name, platform=platform):
            if return_all:
                active.add(summoner)
            else:
                active.add(name)

    return active


def addSummoner(summoner_name, platform="euw1", region="europe", return_text=True):
    added = ds.createSummoner(summoner_name, platform="euw1", region="europe")  # Add to database

    if added:
        # Add matches (data)
        matches = LOLbase.getMatches(summoner_name=summoner_name, platform=platform, region=region)
        for match_data in LOLbase.getMatchData(matches):
            match_id = match_data['metadata']["matchId"]
            success = ds.addMatch(name=summoner_name, platform=platform, region=region, match=match_data,
                                  match_id=match_id)
            if not success:
                print("Addition of match failed")

        ds.commit()

        if return_text:
            return f"Summoner '{summoner_name}' added to database (with {len(matches)} matches)"
        return True

    if return_text:
        return f"Summoner '{summoner_name}' already exists in database"
    return False


def removeSummoner(summoner_name, platform="euw1", region="europe", return_text=True):
    success = ds.removeSummoner(summoner_name, platform, region)
    if return_text:
        if success:
            return f"Summoner '{summoner_name}' deletion successful"
        else:
            return f"Problem removing summoner '{summoner_name}'"
    return success


def addTrackLive(guild_id, summoner_name, platform="euw1", region="europe", return_text=True):
    summoner_id = ds.getSummonerID(summoner_name, platform, region)
    if summoner_id is None:
        if return_text:
            return f"Summoner '{summoner_name}' does not exist in database"
        return False

    server = sd.getServer(guild_id)

    # Create server if not exists
    if server is None:
        sd.addServer(guild_id)
        server = sd.getServer(guild_id)

    server.addTracking(summoner_name, platform, region)
    sd.save_class()

    if return_text:
        return f"Summoner '{summoner_name}' is now tracked"
    return True


def removeTrackLive(guild_id, summoner_name, platform="euw1", region="europe", return_text=True):
    summoner_id = ds.getSummonerID(summoner_name, platform, region)
    if summoner_id is None:
        if return_text:
            return f"Summoner '{summoner_name}' does not exist in database"
        return False

    server = sd.getServer(guild_id)
    if server is not None:
        server.removeTracking(summoner_name, platform, region)
    sd.save_class()

    if return_text:
        return f"Summoner '{summoner_name}' is now tracked"
    return True


def getTrackLive():
    lt = LiveTracking(sd.getTracking())
    active = getActive(return_all=True)
    stop_active, new_active = lt.noteLive(active)

    for summoner_data in new_active:
        yield lt.getGuilds(summoner_data), summoner_data


if __name__ == "__main__":
    pass
    # for t in getGameResultUpdates(force=False):
    #     print(t)

    # print(getActive())

    # summoner_name = "BroskiSammy"
    # t = getStats(summoner_name, return_text=True)
    # print(t)

    # res = ds.getMatches("TΩXIC", platform="euw1", region="europe")
    # print(getStats("TΩXIC"))

    # res = LOLbase.getMatches(summoner_name="TΩXIC", platform="euw1", region="europe")
    # print(res)

    for x in getTrackLive():
        print(x)
