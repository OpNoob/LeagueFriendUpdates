import os.path
import pickle
import json
from ClassSave import ClassSL


class LiveTracking:
    def __init__(self, tracking: list[int, tuple[str]]):
        self.live = set()  # holds current live summoners
        self.guild_map = dict()  # holds each summoner with x guilds

        for (guild_id, summoners) in tracking:
            for summoner_data in summoners:
                if summoner_data in self.guild_map:
                    self.guild_map[summoner_data].append(guild_id)
                else:
                    self.guild_map[summoner_data] = [guild_id]

    def markDone(self, summoner_name: str, platform: str, region: str):
        self.live.remove((summoner_name, platform, region))

    def filterSummoners(self, summoners: set[tuple[str]]):
        return {a for a in summoners if a in self.guild_map}

    def getSummoners(self):
        return set(self.guild_map.keys())

    def noteLive(self, active: set[tuple[str]]):
        active = self.filterSummoners(active)  # keep only those that need to be tracked

        stop_active = self.live - active  # get summoners that stopping being active
        new_active = active - self.live  # get summoners that started being active
        self.live = active  # replace live with new active
        return stop_active, new_active

    def getGuilds(self, summoner_data: tuple[str]):
        return self.guild_map[summoner_data]


class Server:
    def __init__(self, guild_id: int):
        self._guild_id = guild_id
        self.summoner_tracking = set()

    def addTracking(self, summoner_name: str, platform: str, region: str):
        self.summoner_tracking.add((summoner_name.lower(), platform.lower(), region.lower()))

    def removeTracking(self, summoner_name: str, platform: str, region: str):
        self.summoner_tracking.remove((summoner_name.lower(), platform.lower(), region.lower()))

    def getTracking(self):
        return self.summoner_tracking

    def getGuildID(self):
        return self._guild_id

    def toDict(self):
        return {
            "Guild ID": self._guild_id,
            "Summoner tracking": self.summoner_tracking
        }


class ServerData(ClassSL):
    def __init__(self, path="data/servers.pkl", **kwargs):
        super().__init__(class_path=path, **kwargs)

        if not self._loaded:
            self.servers = list()

    def addServer(self, guild_id: int):
        self.servers.append(Server(guild_id))

    def getServer(self, guild_id: int):
        for server in self.servers:
            if server.getGuildID() == guild_id:
                return server

    def getTracking(self):
        tracking = list()
        for server in self.servers:
            tracking.append((server.getGuildID(), server.summoner_tracking))
        return tracking
