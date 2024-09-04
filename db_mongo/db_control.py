#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from datetime import datetime, timedelta
import yaml
from os.path import expanduser
from enum import Enum
import json
from re import sub
import pydantic


# from dns.rdatatype import NULL
from pymongo import MongoClient
import copy
from bson import json_util, ObjectId
from dataclasses import dataclass
from bson.timestamp import Timestamp
import datetime as dt

# pydantic.Json.ENCODERS_BY_TYPE[ObjectId] = str


class LogLevel:
    INFO = 0
    WARN = 1
    ERROR = 2


class MissionStatus:
    RUNNING = 0
    SUCCEEDED = 1
    PAUSED = 2
    ERROR = 3
    CANCEL = 4


class QueryDB:
    STATUS_RB = "status_robots"
    PICKUP_LOCATION = "pickup_locations"
    RETURN_LOCATION = "return_locations"
    WAIT_LOCATION = "empty_locations"
    MISIONS = "missions"
    ACCOUNT = "accounts"
    ROLE = "roles"
    ACTIVITIES = "robot_activites"


@dataclass
class Response:
    """An HTTP response"""

    status: int
    content_type: str
    body: str


class MongoDB:
    def __init__(self, connectionString="mongodb://localhost:27017"):
        self.client = MongoClient(connectionString)
        project = "zss"
        list_db = [
            QueryDB.STATUS_RB,
            QueryDB.PICKUP_LOCATION,
            QueryDB.RETURN_LOCATION,
            QueryDB.WAIT_LOCATION,
            QueryDB.MISIONS,
            QueryDB.ACCOUNT,
            QueryDB.ACTIVITIES,
            # QueryDB.ROLE,
        ]

        value_account = {
            "username": "admin",
            "password": "admin",
            "role": 2,
        }

        value_location = {
            "name": "initial",
            "line": 10000,
            "point": "initial",
            "model": "initial",
            "kitting": True,
        }
        value_mission = {
            "mission_code": "initial",
            "robot_code": "initial",
            "pickup_location": "initial",
            "return_location": "initial",
            "sector": "",
            "current_state": "initial ",
            "creatAT": "00-00-00:00:00",
        }
        value_robot_status = {
            "robot_name": "initial",
            "battery": 100,
            "status": "initial",
            "mission": "initial",
            "robot_type": "initial",
            "ip": "000.000.0.0",
        }
        robot_activity = {
            "robot_name": "initial",
            "msg": "test_initial",
            "date": "08-28-09:21:20",
        }
        initial_mapping = [
            value_robot_status,
            value_location,
            value_location,
            value_location,
            value_mission,
            value_account,
            robot_activity,
        ]

        database_name = self.client.list_database_names()
        self.work_db = self.client[project]
        if not project in database_name:
            for initial in range(len(list_db)):
                # for initial in list_db:
                collection = self.work_db[list_db[initial]]
                collection.insert_one(initial_mapping[initial])

        # for i in range(1, 7):
        #     self.built_location(QueryDB.WAIT_LOCATION, i)

    def built_location(self, _area, n_location):

        # area = "pickup_locations"
        _collection = self.work_db[_area]
        document = {
            "name": "vt" + str(n_location),
            "line": n_location,
            "point": "LM1",
            "model": "",
            "kitting": True,
        }
        _collection.insert_one(document)

    def import_db(self, collection, data) -> None:
        _collection = collection.insert_one(data)
        return _collection.acknowledged

    def delete_db(self, _area, date_delete):
        collection = self.work_db[_area]
        result_code = {"code": 0}

        _collection = collection.find_one_and_delete(date_delete)
        if _collection is not None:
            result_code = {"code": 1}
            _collection.update(result_code)
            return self.json_payload(_collection)
        return result_code

    def clear_row(self, _area, data_search):
        collection = self.work_db[_area]
        _collection = collection.delete_many(data_search)

    def test_db(self):
        return "ok query success"

    def creat_accounts(self, _username, _password, _role):
        area = QueryDB.ACCOUNT
        _collection = self.work_db[area]
        value_creat = {"username": _username, "password": _password, "role": _role}
        if _collection.find_one({"username": _username}) != None:
            return "account already exists"
        else:
            self.import_db(_collection, value_creat)
            return "creat success acoount "

    def creat_robots(self, _area, comtemplate, creator):
        _collection = self.work_db[_area]
        # print(_collection.find_one({"robot_name": comtemplate["robot_code"]}))

        if _collection.find_one({"robot_name": comtemplate["robot_code"]}) != None:
            return False
        else:
            self.import_db(_collection, comtemplate)
            return "creat success acoount "

    def robot_operating(self, msg):
        area = QueryDB.ACTIVITIES
        _collection = self.work_db[area]
        mess_update = {
            "robot_code": msg["robot_code"],
            "msg": msg["msg"],
            "date": datetime.now(),
        }
        if self.import_db(_collection, mess_update):
            return "update success "
        return False

    def check_accounts(self, _username, _password):
        area = QueryDB.ACCOUNT
        _collection = self.work_db[area]
        _query = _collection.find_one({"username": _username})
        x = {"username": _username, "password": _password}

        if _query != None:
            if _query["password"] == _password:
                _query.pop("_id", None)
                return _query
            # return "account already exists"
        else:
            return None

    def update_account(self, account):
        area = QueryDB.ACCOUNT
        _collection = self.work_db[area]
        search_robot = {"username": account["username"]}
        value_update = {"$set": account}
        _query = _collection.find_one_and_update(search_robot, value_update)
        if _query == None:
            return False
        return self.json_payload(_query)

    def update_robot_status(self, _robot_name, _status, _mission, _battery):
        area = QueryDB.STATUS_RB
        _collection = self.work_db[area]
        # _query = _collection.find_one({"robot_name": _robot_name})
        search_robot = {"robot_name": _robot_name}
        value_update = {
            "$set": {
                "status": _status,
                "mission": _mission,
                "battery": _battery,
                "lastUpdate": {"date": datetime.now(), "estimate_ability": 10},
            },
            # "$setOnInsert": {"created_update": datetime.now()},
            # "$currentDate": {"lastUpdate": datetime.now()},
        }
        # db.collection.updateOne(
        #     {"key": 5},
        #     {
        #         "$set": {"updated_at": datetime.now()},
        #         "$setOnInsert": {"created_update": datetime.now()},
        #     },
        #     upsert=True,
        # )
        _update = _collection.update_one(
            search_robot,
            value_update,
            upsert=True,
        )
        if _update.raw_result["n"]:
            return True
        return False

    def query_database(self, _area, _search):
        _collection = self.work_db[_area]
        _query = _collection.find_one(_search)
        if _query is not None:
            # res = {
            #     "name": _query["name"],
            #     "line": _query["line"],
            #     "point": _query["point"],
            #     "model": _query["model"],
            #     "kitting": _query["kitting"],
            # }
            _query.pop("_id", None)
            return _query
        return False

    def query_robot_status(self, _robot_name):
        area = QueryDB.STATUS_RB
        _collection = self.work_db[area]
        # _query = _collection.find_one({"robot_name": _robot_name[i]})
        search_robot = {"robot_name": _robot_name}
        response = []
        # for i in range(len(_robot_name)):
        _query = _collection.find_one(search_robot)
        if _query == None:
            return False

        return self.json_payload(_query)
        # res = {
        #     "robot_name": _query["robot_name"],
        #     "status": _query["status"],
        #     "mission": _query["mission"],
        #     "battery": _query["battery"],
        # }
        # return res

    def query_all_robot(self, _robot_type):
        area = QueryDB.STATUS_RB
        search_robot = {"robot_type": _robot_type}
        _collection = self.work_db[area]
        curr = _collection.find(search_robot)
        response = []

        for amr in curr:
            response.append(self.json_payload(amr))
        return response

    def locations_request(self, _area):
        _collection = self.work_db[_area]
        _locations = _collection.find()
        response = []
        for location in _locations:
            # res = {
            #     "name": location["name"],
            #     "line": location["line"],
            #     "point": location["point"],
            #     "model": location["model"],
            #     "kitting": location["kitting"],
            # }
            response.append(self.json_payload(location))
        return response

    def update_database(self, area, location, value, username):
        _collection = self.work_db[area]
        status_list = {"username": username, "date": datetime.now()}
        value.update({"status_list": status_list})

        value_update = {"$set": value}
        _update = _collection.update_one(location, value_update)
        if _update.raw_result["n"]:
            return True
        return False

    def find_sector(self, zone):
        search_location = {"name": zone}
        value = self.query_database(QueryDB.PICKUP_LOCATION, search_location)
        if value is not None and value:
            return value["model"]
        return ""

    def creat_missions(self, mission_value, creator):
        area = QueryDB.MISIONS
        _collection = self.work_db[area]
        # dt = datetime.now().strftime("%Y-%m-%d %H:%M")

        storage = {
            "mission_code": "MISSION-"
            + mission_value["robot_code"]
            + "-"
            + str(self.datetimes_st()),
            "robot_code": mission_value["robot_code"],
            "pickup_location": mission_value["pickup_location"],
            "return_location": mission_value["return_location"],
            "sector": self.find_sector(mission_value["pickup_location"]),
            "current_state": "registered ",
            "creator": creator,
            "creatAT": self.datetimes_st(),
        }
        if self.import_db(_collection, storage):
            return self.json_payload(storage)
        return False

    def histories_mission_request(self, _area, max_n):
        _collection = self.work_db[_area]
        _missions = _collection.find().limit(max_n)
        response = []
        for mission in _missions:
            mission.pop("_id", None)
            response.append(mission)

        return response

    def mission_histories_request(self):
        area = QueryDB.MISIONS
        _collection = self.work_db[area]
        _locations = _collection.find()
        response = []
        for location in _locations:
            res = {
                "name": location["name"],
                "line": location["line"],
                "point": location["point"],
                "model": location["model"],
                "kitting": location["kitting"],
            }
            response.append(res)
        return response

    def datetimes_st(self):
        return datetime.now().strftime("%m-%d-%H:%M:%S")

    def get_database(self, args):
        return self.client[args]

    def json_payload(self, value):
        return json.loads(json_util.dumps(value))

    def printJson(self, data):
        _convert_json = json.loads(json_util.dumps(data, default=str))
        return _convert_json

        # return data

    # def bson2Json(self, data):
    #     return dumps(data, indent=4, sort_keys=True)


MongoDB()
