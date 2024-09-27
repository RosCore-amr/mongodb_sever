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
from copy import copy
import random

# from dns.rdatatype import NULL
from pymongo import MongoClient
import copy
from bson import json_util, ObjectId
from dataclasses import dataclass
from bson.timestamp import Timestamp

# pydantic.Json.ENCODERS_BY_TYPE[ObjectId] = str

from config import (
    LocationStatus,
    SortSearch,
    MapCode,
)


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
    EXCUTE_MISSION = "mission_excute"


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
            # QueryDB.EXCUTE_MISSION,
            QueryDB.MISIONS,
            QueryDB.ACCOUNT,
            QueryDB.ACTIVITIES,
            QueryDB.EXCUTE_MISSION,
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
            "mission_state": "initial ",
            "creatAT": "00-00-00:00:00",
        }
        value_robot_status = {
            "robot_code": "initial",
            "battery": 100,
            "status": "initial",
            "mission": "initial",
            "robot_type": "initial",
            "ip": "000.000.0.0",
        }
        robot_activity = {
            "robot_code": "initial",
            "msg": "test_initial",
            "date": "08-28-09:21:20",
        }
        excute_mission = {
            "excute_code": "transport_empty_cart",
            "mission_wait": [],
            # "mission_next": "",
            "mission_excute": [],
            "mission_type": 46,
        }
        initial_mapping = [
            value_robot_status,
            value_location,
            value_location,
            value_location,
            value_mission,
            value_account,
            robot_activity,
            excute_mission,
        ]

        database_name = self.client.list_database_names()
        self.work_db = self.client[project]
        if not project in database_name:
            for initial in range(len(list_db)):
                # for initial in list_db:
                collection = self.work_db[list_db[initial]]
                collection.insert_one(initial_mapping[initial])

        # self.filled_data(QueryDB.PICKUP_LOCATION, "zone1", 7)
        # for i in range(1, 49):
        #     self.built_location(QueryDB.RETURN_LOCATION, i)

    def built_location(self, _area, n_location):

        # area = "pickup_locations"
        _collection = self.work_db[_area]
        document = {
            "name": "zone" + str(n_location),
            # "line": [
            #     random.randint(1, 49),
            #     random.randint(1, 49),
            #     random.randint(1, 49),
            #     random.randint(1, 49),
            # ],
            "line": (n_location),
            "point": "LM" + str(n_location),
            "model": "",
            "kitting": True,
            "location_status": 6,
            "map_code": QueryDB.RETURN_LOCATION,
            "location_priority": 1,
            "lastAT": datetime.now(),
        }

        _collection.insert_one(document)

    def import_db(self, collection, data) -> None:
        _collection = collection.insert_one(data)
        return _collection.acknowledged

    def delete_db(self, _area, date_delete):
        collection = self.work_db[_area]
        _result_code = {"code": 0}

        _collection = collection.find_one_and_delete(date_delete)
        if _collection is not None:
            _result_code = {"code": 1}
            _collection.update(_result_code)
            return self.json_payload(_collection)
        return _result_code

    def clear_row(self, _area, data_search):
        collection = self.work_db[_area]
        # _collection = collection.delete_many(data_search)
        # _collection = collection.

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
        comtemplate.update({"lastUpdate": {"date": datetime.now()}})

        if _collection.find_one({"robot_code": comtemplate["robot_code"]}) != None:
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

    def update_robot_status(self, status_code):
        area = QueryDB.STATUS_RB
        _collection = self.work_db[area]
        _result_code = {"code": 0}
        search_robot = {"robot_code": status_code["robot_code"]}
        status_code.update({"lastUpdate": {"date": datetime.now()}})
        value_update = {
            "$set": status_code
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
        _update = _collection.find_one_and_update(
            search_robot,
            value_update,
            upsert=False,
        )
        # return _update
        if _update is not None:
            _result_code = {"code": 1}
            return _result_code
        return _result_code

    def query_robot_status(self, _robot_name):
        area = QueryDB.STATUS_RB
        _collection = self.work_db[area]
        search_robot = {"robot_code": _robot_name}
        response = []
        _query = _collection.find_one(search_robot)
        if _query == None:
            return False

        return self.json_payload(_query)

    def query_all_robot(self, _robot_type):
        area = QueryDB.STATUS_RB
        # search_robot = {"robot_type": _robot_type}
        _collection = self.work_db[area]
        curr = _collection.find()
        response = []

        for amr in curr:
            response.append(self.json_payload(amr))
        return response

    def locations_request(self, _area, _find_value):
        _collection = self.work_db[_area]
        _locations = _collection.find(_find_value)
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

    def locations_find(self, _find_value, sort_value):
        _collection = self.work_db[_find_value["map_code"]]
        _locations = _collection.find(_find_value).sort(sort_value).limit(1)

        for location in _locations:
            # print("location", i)
            return self.json_payload(location)

        # response = []
        # # return True
        # for location in _locations:
        #     print("location", location)
        #     # res = {
        #     #     "name": location["name"],
        #     #     "line": location["line"],
        #     #     "point": location["point"],
        #     #     "model": location["model"],
        #     #     "kitting": location["kitting"],
        #     # }
        #     response.append(self.json_payload(location))
        return self.json_payload(_locations)
        return True

    def update_many_database(self, area, value, username):

        _collection = self.work_db[area]
        histories_update = dict(value)
        histories_update.setdefault("username", username)
        value.update(
            {
                "lastAT": datetime.now(),
                "status_list": histories_update,
            }
        )
        value_update = {"$set": value}
        _update = _collection.update_many(
            {},
            value_update,
            upsert=False,
        )
        return _update.raw_result

    def location_update_database(self, area, location, value, username):
        _collection = self.work_db[area]

        # "lastAT": datetime.now()
        _find = _collection.find_one(
            location,
            # value_update,
            # upsert=False,
        )
        # print("value_update", _find["name"])
        history_before_update = {
            "line": _find["line"],
            "point": _find["point"],
            "model": _find["model"],
            "location_status": _find["location_status"],
            "location_priority": _find["location_priority"],
        }

        # status_list = {"username": username}
        histories_update = dict(value)
        histories_update.setdefault("username", username)
        value.update(
            {
                "lastAT": datetime.now(),
                "status_list": histories_update,
                "status_before_change": history_before_update,
            }
        )

        value_update = {"$set": value}
        # print("value_update", value_update)
        _update = _collection.find_one_and_update(
            location,
            value_update,
            upsert=False,
        )
        # print("value_update", value_update)

        if _update is None:
            return None
        return self.json_payload(_update)

    def update_database(self, area, location, value, username):
        _collection = self.work_db[area]

        # "lastAT": datetime.now()

        # status_list = {"username": username}
        histories_update = dict(value)
        histories_update.setdefault("username", username)
        value.update(
            {
                "lastAT": datetime.now(),
                "status_list": histories_update,
            }
        )

        value_update = {"$set": value}
        # print("value_update", value_update)
        _update = _collection.find_one_and_update(
            location,
            value_update,
            upsert=False,
        )

        if _update is None:
            return None
        return self.json_payload(_update)
        # if _update.raw_result["n"]:
        #     return True
        return False

    def update_excute_mission(self, area, location, value, username):
        _collection = self.work_db[area]
        value_update = {"$push": {"mission_excute": value}}
        # value_pop = {"$pop": {"mission_excute": -1}}
        # print("value_update", value_set)
        _update = _collection.find_one_and_update(
            location,
            value_update,
            # upsert=False,
        )
        # print(_update)
        return self.json_payload(_update)

    def pop_excute_mission(self, area, location, username):
        _collection = self.work_db[area]
        value_pop = {"$pop": {"mission_excute": -1}}
        _find = _collection.find_one_and_update(
            location,
            value_pop,
        )
        # if len(_find["mission_excute"]) != 0:
        #     _mission_next = {"mission_next": _find["mission_excute"][0]}
        # else:
        #     _mission_next = {"mission_next": ""}

        if len(_find["mission_excute"]) == 0:
            return {"code": 0, "msg": "khong co nhiem vu trong nao ca "}

        # body_update = {
        #     "mission_next": _find["mission_excute"][0],
        #     # "mission_wait": list(_find["mission_wait"]).append(_find["mission_next"]),
        # }
        value_update_mission_wait = {
            "$push": {"mission_wait": _find["mission_excute"][0]},
            # "$set": _mission_next,
        }

        # print("_find mission_next", _find["mission_next"])
        # print("_find mission_wait", (_find["mission_wait"].append("studentId")))

        # value_update = {"$set": body_update}
        _update = _collection.find_one_and_update(
            location,
            value_update_mission_wait,
            # value_update_mission_wait,
            upsert=False,
        )
        # _update.update({"code : 1 "})
        return self.json_payload(_update)

    def occupy_location(self, _occupe_location, creator):

        for i in range(len(_occupe_location)):
            area = _occupe_location[i]["map_code"]
            location = {"name": _occupe_location[i]["location_code"]}
            _location_update = {"location_status": 8}
            _update = self.update_database(area, location, _location_update, creator)
            if _update is None:
                response_error = {"name": location["name"], "map_code": area, "code": 0}
                return response_error
        _update.update({"code": 1})
        return _update

    def query_database(self, _area, _search):
        _collection = self.work_db[_area]
        _query = _collection.find_one(_search)
        if _query is not None:
            _query.pop("_id", None)
            return _query
        return None

    def search_many(self, _area, _search):
        _collection = self.work_db[_area]
        _query = _collection.find(_search)
        # _missions = _collection.find(
        #     {
        #         "creatAT": {
        #             "$lt": datetime.now(),
        #             "$gt": datetime.now() - timedelta(hours=datetime.now().hour + 1),
        #         }
        #     }
        # )
        response = []
        for amr in _query:

            response.append(self.json_payload(amr))
        response.reverse()
        return response

    def find_sector(self, zone):
        search_location = {"name": zone}
        value = self.query_database(QueryDB.PICKUP_LOCATION, search_location)
        if value is not None and value:
            return value["model"]
        return ""

    def searching_stock_available(
        self,
        _location_code,
        _permission_task,
    ):
        area = QueryDB.PICKUP_LOCATION
        if _permission_task == 3:

            search_location = {"line": _location_code}
            _error_code = "There are currently no components in stock"
        elif _permission_task == 5:
            search_location = {"name": _location_code}
            _error_code = "There are no vacancies under the warehouse"
        else:
            return None
        _query = self.query_database(area, search_location)
        if _query is None:
            return None
        if _query["location_status"] != _permission_task:
            _query.update({"code": 0, "msg": _error_code})
            return _query
        _query.update({"code": 1})
        return _query

    def remove_task_pending(self, _area, _search, value):
        _collection = self.work_db[_area]
        value_update = {"$pull": {"mission_wait": value["mission_code"]}}
        _query = _collection.update_one(_search, value_update)
        # print("value ", value["mission_code"])
        # _update.raw_result["n"]:
        # print("_query ", _query.raw_result["nModified"])
        return {"code": _query.raw_result["nModified"]}

    def mission_processing(self, mission_value, creator):

        entry_location = mission_value["entry_location"]
        end_location = mission_value["end_location"]
        _occupe_location = [
            entry_location,
            end_location,
        ]
        occupe_status = self.occupy_location(_occupe_location, creator)
        if not occupe_status["code"]:
            return occupe_status
        occupy_mission = self.add_new_mission(
            # entry_location,
            # end_location,
            mission_value,
            creator,
        )
        return occupy_mission
        sector = self.find_sector(entry_location["location_code"])

    def add_new_mission(self, _destination_mission, creator):
        area = QueryDB.MISIONS
        _collection = self.work_db[area]
        n_mission = len(
            list(
                _collection.find(
                    {
                        "creatAT": {
                            "$lt": datetime.now(),
                            "$gt": datetime.now()
                            - timedelta(hours=datetime.now().hour + 1),
                        }
                    }
                )
            )
        )
        # print("len", (n_mission))
        storage = {
            "mission_code": "MISSION-"
            + str((n_mission))
            + "-"
            + str(self.datetimes_st()),
            # "robot_code": mission_value["robot_code"],
            "destination": _destination_mission,
            # "entry_location": _entry_location["location_code"]
            # + "-"
            # + _entry_location["map_code"],
            # "end_location": _end_location["location_code"]
            # + "-"
            # + _end_location["map_code"],
            # "sector": "asd",
            "mission_state": 1,
            "code": 1,
            "creator": creator,
            "creatAT": datetime.now(),
        }
        if self.import_db(_collection, storage):
            return self.json_payload(storage)
        return False

    def user_query_information_mission(self, _area, sort_value, user_namne):
        _collection = self.work_db[_area]

        # return self.json_payload(mx)
        # _missions = _collection.find().limit(max_n)
        search = {"creator": user_namne}
        _missions = _collection.find(
            search
            # {
            #     "creatAT": {
            #         "$lt": datetime.now(),
            #         "$gt": datetime.now() - timedelta(hours=datetime.now().hour + 1),
            #     }
            # }
        ).sort(sort_value)
        # if

        return self.json_payload(_missions)

    def histories_mission_request(self, _area, sort_value):
        _collection = self.work_db[_area]

        # return self.json_payload(mx)
        # _missions = _collection.find().limit(max_n)
        _missions = _collection.find(
            # {
            #     "creatAT": {
            #         "$lt": datetime.now(),
            #         "$gt": datetime.now() - timedelta(hours=datetime.now().hour + 1),
            #     }
            # }
        ).sort(sort_value)

        return self.json_payload(_missions)

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

    # def

    def datetimes_st(self):
        return datetime.now().strftime("%m-%d-%H:%M:%S")

    def datetimes_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def get_database(self, args):
        return self.client[args]

    def json_payload(self, value):
        return json.loads(json_util.dumps(value))

    def printJson(self, data):
        _convert_json = json.loads(json_util.dumps(data, default=str))
        return _convert_json

        # return data


MongoDB()
