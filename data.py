import sqlite3
import json


class DataStore:
    def __init__(self, path="data/database.db"):
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()

        # names for sql
        self._table_summoner = "summoner_data"
        self._name_k = "name"
        self._platform_k = "platform"
        self._region_k = "region"
        self._data_k = "data"
        self._table_match = "match_data"
        self._summoner_id = "summoner_id"
        self._match_k = "match"

        sql_enc = "pragma encoding = 'UTF-8'"
        self.cur.execute(sql_enc)

        sql_table_sum = f"CREATE TABLE IF NOT EXISTS {self._table_summoner} (ID INTEGER PRIMARY KEY AUTOINCREMENT, {self._name_k} TEXT(16), {self._platform_k} VARCHAR(5), {self._region_k} VARCHAR(16), {self._data_k} json, UNIQUE ({self._name_k}, {self._platform_k}, {self._region_k}) )"
        self.cur.execute(sql_table_sum)

        sql_table_mat = f"CREATE TABLE IF NOT EXISTS {self._table_match} (ID TEXT PRIMARY KEY, {self._summoner_id} INTEGER, {self._match_k} json, FOREIGN KEY({self._summoner_id}) REFERENCES {self._table_summoner}(Id) )"
        self.cur.execute(sql_table_mat)

        self.commit()

    def DROPALL(self, check='123'):
        inp = input(f"Write '{check}' to confirm dropping of all tables: ")
        if inp == check:
            sql_drop_sum = f"DROP TABLE {self._table_summoner}"
            self.cur.execute(sql_drop_sum)

            sql_drop_mat = f"DROP TABLE {self._table_match}"
            self.cur.execute(sql_drop_mat)

            self.conn.commit()

            print("Tables dropped")

    def createSummoner(self, name: str, platform: str, region: str):
        if self.getSummonerID(name=name, platform=platform, region=region) is None:
            sql_insert = f"INSERT INTO {self._table_summoner} VALUES(NULL, ?, ?, ?, NULL)"
            self.cur.execute(sql_insert, (name, platform, region))
            return True
        else:
            return False

    def setData(self, name: str, platform: str, region: str, data: dict):
        sql_update = f"UPDATE {self._table_summoner} SET {self._data_k}=? WHERE LOWER({self._name_k})=LOWER(?) AND {self._platform_k}=? AND {self._region_k}=?"
        self.cur.execute(sql_update, (json.dumps(data), name, platform, region))
        self.commit()

    def addMatch(self, name: str, platform: str, region: str, match: dict, match_id: str, commit=False):
        assert match is not None

        if self.getMatch(match_id) is not None:
            return False

        summoner_id = self.getSummonerID(name=name, platform=platform, region=region)
        if summoner_id is not None:
            summoner_id = summoner_id[0]

            sql_insert = f"INSERT INTO {self._table_match}  VALUES (?, ?, ?)"
            self.cur.execute(sql_insert, (match_id, summoner_id, json.dumps(match)))
            if commit:
                self.commit()
            return True
        # else:
        #     print("Summoner id not found in database")

        return False

    def checkExists(self, name: str, platform: str, region: str):
        data = self.getData(name=name, platform=platform, region=region)
        if data is None:
            return False
        else:
            return True

    def commit(self):
        self.conn.commit()

    def getSummonerID(self, name: str, platform: str, region: str):
        sql_get = f"SELECT Id FROM {self._table_summoner} WHERE LOWER({self._name_k})=LOWER(?) AND {self._platform_k}=? AND {self._region_k}=?"
        self.cur.execute(sql_get, (name, platform, region))
        summoner_id = self.cur.fetchone()
        return summoner_id

    def getData(self, name: str, platform: str, region: str):
        sql_select = f"SELECT data FROM {self._table_summoner} WHERE LOWER({self._name_k})=LOWER(?) AND {self._platform_k}=? AND {self._region_k}=?"
        self.cur.execute(sql_select, (name, platform, region))
        obj = self.cur.fetchone()
        if obj is None:
            return
        d = json.loads(obj[0])
        return d

    def getSummoners(self):
        sql_get = f"SELECT {self._name_k}, {self._platform_k}, {self._region_k} from {self._table_summoner}"
        self.cur.execute(sql_get)
        return self.cur.fetchall()

    def getMatches(self, name: str, platform: str, region: str):
        summoner_id = self.getSummonerID(name=name, platform=platform, region=region)
        if summoner_id is not None:
            sql_get = f"SELECT {self._match_k} FROM {self._table_match} WHERE {self._summoner_id}=?"
            self.cur.execute(sql_get, (summoner_id[0],))
            matches = self.cur.fetchall()
            return [json.loads(m[0]) for m in matches]
        else:
            print("Summoner id not found in database")

    def getMatch(self, match_id: str):
        sql_get = f"SELECT {self._match_k} FROM {self._table_match} WHERE Id=?"
        self.cur.execute(sql_get, (match_id,))
        match = self.cur.fetchone()
        if match is not None:
            match = match[0]
            match = json.loads(match)
        return match

    def getAllSummoners(self):
        sql_get = f"SELECT * from {self._table_summoner}"
        self.cur.execute(sql_get)
        return self.cur.fetchall()

    def getAllMatches(self):
        sql_get = f"SELECT * from {self._table_match}"
        self.cur.execute(sql_get)
        return self.cur.fetchall()

    def __del__(self):
        self.conn.close()


if __name__ == "__main__":
    ds = DataStore()
    # ds.createSummoner("test", "123", "234")

    # ds.setData("test", "123", "234", {1: 234})
    # print(ds.checkExists("test", "123", "234"))
    # print(ds.getSummoners())
    # print(len(ds.getAllMatches()))

    ds.DROPALL()
