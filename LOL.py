from collections import Counter
from datetime import datetime

from LOLbase import *
from data import DataStore
from announcements import GameResult
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


def getGameResultUpdates():
    summoners = set(ds.getSummoners())

    for summoner in summoners:
        name, platform, region = summoner

        matches = getMatches(summoner_name=name, platform=platform, region=region)
        # print(matches)
        for match_data in getMatchData(matches):
            # print(match_data)
            match_id = match_data['metadata']["matchId"]
            success = ds.addMatch(name=name, platform=platform, region=region, match=match_data, match_id=match_id)
            if not success:
                break

            # ANNOUNCE
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
        lane = lanes.most_common(1)[0]
        champion = champions.most_common(1)[0]

        text = f"NAME: {summoner_name}\n\nStats Since: {str(earliest_dt.date())}\nPlaying Duration: {ms_to_str(duration_s * 1000)}\n\nTotal Kills: {kills}\nTotal Deaths: {deaths}\nTotal Assists: {assists}\nTotal Wins: {wins}\nTotal losses: {losses}\n\nFavourite Lane: {lane[0]} ({lane[1]} times)\nFavourite Champion: {champion[0]} ({champion[1]} times)"
        return text
    return earliest_dt, duration_s, kills, deaths, assists, wins, losses, lanes, champions


def getActive():
    summoners = set(ds.getSummoners())

    active = list()

    for summoner in summoners:
        name, platform, region = summoner

        if isInGame(summoner_name=name, platform=platform):
            active.append(name)

    return active


if __name__ == "__main__":
    pass
    # for t in getGameResultUpdates():
    #     print(t)

    # print(getActive())

    # summoner_name = "BroskiSammy"
    # t = getStats(summoner_name, return_text=True)
    # print(t)
