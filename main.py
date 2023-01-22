from leagueOfLegends import *
from data import DataStore
from announcements import GameResult
import time

"""
Resources: 
https://developer.riotgames.com/docs/lol#routing-values_platform-routing-values
https://developer.riotgames.com/apis#match-v5/GET_getMatch
"""

ds = DataStore()
summoners = set(ds.getSummoners())

WAIT_TIMER = 10

live_summoners = set()
while True:
    for summoner in summoners:
        name, platform, region = summoner

        matches = getMatches(summoner_name=name, platform=platform, region=region)
        for match_data in getMatchData(matches):
            match_id = match_data['metadata']["matchId"]
            success = ds.addMatch(name=name, platform=platform, region=region, match=match_data, match_id=match_id)
            if not success:
                break

            # ANNOUNCE
            status_text = "won" if match_data['metadata']["win"] else "lost"
            print(f"Summoner: {name} has {status_text}")

    # Saving
    ds.commit()

    # Timer
    time.sleep(WAIT_TIMER)
