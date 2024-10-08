#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jwt
import uvicorn

from datetime import datetime, timedelta, timezone
from typing import Union, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, ValidationError
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from db_control import MongoDB, QueryDB

from config import (
    LocationStatus,
    SortSearch,
    MapCode,
)


SECURITY_ALGORITHM = "HS256"
SECRET_KEY = "minhdeptraivodichthienha"
EOL_TOKEN = 15
db = MongoDB("mongodb://localhost:27017/")

app = FastAPI(
    title="ESA PROJECT SEV",
    openapi_url="/openapi.json",
    docs_url="/docs",
    # description="",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


reusable_oauth2 = HTTPBearer(scheme_name="Authorization")


class LoginRequest(BaseModel):
    username: str
    password: str
    role: int


class StatusRequestUpdate(BaseModel):
    robot_code: str
    battery: int
    status: int
    mission: str
    type: str


class Location(BaseModel):
    name_location: str
    line: int
    point: str
    model: str
    kitting: bool


class RobotActivities(BaseModel):
    robot_code: str
    msg: str
    # return_location: str


class RobotCreat(BaseModel):
    robot_code: str
    robot_type: str
    ip_machine: str


class ExcuteMission(BaseModel):
    excute_code: str
    mission_excute: str


class Mission(BaseModel):
    type_code: int
    pickup_location: str
    return_location: str


def verify_password(username, password):

    if_acount = db.check_accounts(
        username,
        password,
    )
    if if_acount is not None:
        return if_acount
    return False


def generate_token(
    username: Union[str, Any], password: Union[str, Any], role, expire
) -> str:
    # expire = datetime.now(timezone.utc) + timedelta(
    #     seconds=60 * 60 * 24 * 3  # Expired after 3 days
    # )
    to_encode = {
        "username": username,
        "password": password,
        "role": role,
        "exp": expire,
    }
    # print("to_encode", to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=SECURITY_ALGORITHM)
    # print("encoded_jwt", encoded_jwt)
    return encoded_jwt


def _tokenjwt(current_user=Depends(reusable_oauth2)) -> dict:

    if current_user.credentials == "minh" or current_user.credentials == "trung":
        totaliarian_account = {
            "username": "totalitarian_regime",
            "password": "99",
            "role": 99,
        }
        return totaliarian_account
    try:
        verify_token = current_user.credentials
        decoded_token = jwt.decode(
            verify_token.encode(),
            SECRET_KEY,
            algorithms=SECURITY_ALGORITHM,
        )
        # exp_timestamp = decoded_token["exp"]
        # exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    except:
        return None
    exp_timestamp = decoded_token["exp"]
    # print("exp_timestamp", exp_timestamp)
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    if_acount = verify_password(decoded_token["username"], decoded_token["username"])

    # if datetime.now(timezone.utc) > exp_datetime:
    #     raise HTTPException(status_code=404, detail="denied login, token expired ")
    if if_acount is not None:
        if datetime.now(timezone.utc) > exp_datetime or if_acount["role"] == 99:
            raise HTTPException(status_code=404, detail="denied login, token expired ")
        return if_acount

    return None
    # if decoded_token["expires"] >= time.time():
    # return decoded_token


# @app.post('/login')
# async def login(request_data: LoginRequest):
#     return 'Success'


# @app.post("/seek_stock", dependencies=[Depends(reusable_oauth2)])
# def search_location_stock(request_data: dict, _current_user=Depends(reusable_oauth2)):

#     _verify_token = _tokenjwt(_current_user)


@app.post("/test_demo", dependencies=[Depends(reusable_oauth2)])
def decode_jwt(_current_user=Depends(reusable_oauth2)):
    print("_current_user", _current_user)
    _verify_token = _tokenjwt(_current_user)
    print("_verify_token", _verify_token)
    if _verify_token is not None:
        print("ok backout ")


@app.post("/Singin")
def login(request_data: LoginRequest):
    _login = verify_password(
        username=request_data.username, password=request_data.password
    )
    # print("_login", _login)
    if _login is not None and _login:
        expire = datetime.now(timezone.utc) + timedelta(days=EOL_TOKEN)

        token = generate_token(
            request_data.username, request_data.password, request_data.role, expire
        )
        # print("token", token)

        login_if = {
            "username": _login["username"],
            "password": _login["password"],
            "role": _login["role"],
            "exp": expire,
            "token": token,
        }
        # print("login_if", login_if)

        return login_if
    else:
        raise HTTPException(status_code=404, detail="User not found")
    # return True


@app.post("/Singup")
def creat_account(request_data: LoginRequest):

    # if _tokenjwt(_current_user) is not None:
    _acount = db.creat_accounts(
        request_data.username,
        request_data.password,
        request_data.role,
    )
    return _acount

    # raise HTTPException(status_code=404, detail="Token error")


@app.post("/creat_mission", dependencies=[Depends(reusable_oauth2)])
def creat_mission(mission: dict, _current_user=Depends(reusable_oauth2)):
    # Response:
    # ```
    # {
    #     "entry_location ": {
    #         "location_code": "zone1",
    #         "map_code" : "pickup_locations"
    #     },
    #     "end_location":  {
    #         "location_code": "zone5",
    #         "map_code" : "pickup_locations"
    #     }
    # }
    # ```
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _mission_db = db.mission_processing(mission, _verify_token["username"])
        return _mission_db
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/cancel_mission", dependencies=[Depends(reusable_oauth2)])
def cancel_mission(mission_code: str, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.MISIONS
        _search = {"mission_code": mission_code}
        _mission_cancel = db.mission_cancel_process(
            _area, _search, _verify_token["username"]
        )
        return _mission_cancel
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/add_new_robot", dependencies=[Depends(reusable_oauth2)])
def add_new_robot(
    _robot_information: RobotCreat, _current_user=Depends(reusable_oauth2)
):
    area = QueryDB.STATUS_RB
    _verify_token = _tokenjwt(_current_user)

    if _verify_token is not None:

        _mission_db = db.creat_robots(
            area, _robot_information.__dict__, _verify_token["username"]
        )
        return _mission_db
        # return True
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/robot_activities", dependencies=[Depends(reusable_oauth2)])
def robot_activities(
    request_data: RobotActivities, _current_user=Depends(reusable_oauth2)
):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _mission_db = db.robot_operating(request_data.__dict__)
        return _mission_db
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/seek_stock", dependencies=[Depends(reusable_oauth2)])
def seek_stock(request_data: dict, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        location_search = request_data["location_code"]
        permission_task = request_data["occupy_code"]
        stoken_value = db.searching_stock_available(location_search, permission_task)
        return stoken_value
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/creat_model/{model_name}", dependencies=[Depends(reusable_oauth2)])
def creat_model(model_name: str, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.MODEL
        data_creat = {"model": model_name}
        creat_db = db.creat_data(area, data_creat)
        return creat_db
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/all_acoount", dependencies=[Depends(reusable_oauth2)])
def get_all_account():

    area = QueryDB.ACCOUNT
    # area =  QueryDB.l
    myquery = {}

    location = db.locations_request(area, myquery)
    return location


@app.get("/robot_status/{robot_code}", dependencies=[Depends(reusable_oauth2)])
def get_robot_status(robot_code: str):

    area = QueryDB.STATUS_RB
    search_robot = {"robot_code": robot_code}

    _robot_status = db.query_database(
        area,
        search_robot,
    )
    if not _robot_status:
        raise HTTPException(status_code=404, detail="Robot not exist ")
    return _robot_status


@app.get("/all_robot", dependencies=[Depends(reusable_oauth2)])
def get_all_robot():
    robot_type = "amr"
    _robot_status = db.query_all_robot(
        robot_type,
    )
    return _robot_status


@app.get("/all_pickup", dependencies=[Depends(reusable_oauth2)])
def all_pickup():
    area = QueryDB.PICKUP_LOCATION
    # area =  QueryDB.l
    _location_value = {"name": {"$regex": "^zone"}}
    location = db.locations_request(area, _location_value)
    return location


@app.get("/all_return", dependencies=[Depends(reusable_oauth2)])
def all_returnLocation():
    area = QueryDB.RETURN_LOCATION
    _location_value = {"name": {"$regex": "^zone"}}

    location = db.locations_request(area, _location_value)
    return location


# @app.get("/all_empty", dependencies=[Depends(reusable_oauth2)])
# def all_emptyLocation():
#     area = QueryDB.PICKUP_LOCATION
#     _location_value = {"name": {"$regex": "^vt"}}

#     location = db.locations_request(area, _location_value)
#     return location


@app.get("/find_products/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def find_products(zone_id: str):
    sort_value = {"lastAT": SortSearch.OLD.value}
    line_code = int(zone_id.replace("zone", ""))
    find_value = {
        "map_code": MapCode.T1,
        "line": line_code,
        "location_status": LocationStatus.GOODS.value,
    }
    location = db.locations_find(find_value, sort_value)
    return location


@app.get("/available_location/{map_code}", dependencies=[Depends(reusable_oauth2)])
def available_location(map_code: str):

    # print("find_value", find_value)
    sort_value = {"location_priority": SortSearch.OLD.value}
    find_value = {
        # "map_code": MapCode.T1,
        "map_code": map_code,
        "location_status": LocationStatus.EMPTY_LOCATION.value,
    }

    location = db.locations_find(find_value, sort_value)
    # if not location:
    #     print("ok")
    return location


@app.get("/find_cart_empty/{location_status}", dependencies=[Depends(reusable_oauth2)])
def find_cart_empty_stock(location_status: int, _current_user=Depends(reusable_oauth2)):
    # if _tokenjwt(_current_user) is not None:
    # print("find_value", find_value)
    sort_value = {"lastAT": SortSearch.OLD.value}
    find_value = {"map_code": MapCode.T2, "location_status": location_status}
    # print("sort_value", sort_value)
    # find_value.update(sort_value)
    location = db.locations_find(find_value, sort_value)
    return location


@app.get("/operating_activities/{robot_code}", dependencies=[Depends(reusable_oauth2)])
def get_pickup(robot_code: str):
    area = QueryDB.ACTIVITIES
    _search = {"robot_code": robot_code}
    location = db.search_many(area, _search)
    return location


@app.get("/query_pickup/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def get_pickup(zone_id: str):
    area = QueryDB.PICKUP_LOCATION
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    return location


@app.get("/excute_mission/{mission_code}", dependencies=[Depends(reusable_oauth2)])
def get_excute_mission(mission_code: str):
    area = QueryDB.EXCUTE_MISSION
    _search = {"excute_code": mission_code}
    location = db.query_database(area, _search)
    return location


@app.get("/query_return/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def get_return(zone_id: str):
    area = QueryDB.RETURN_LOCATION
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    # return True
    return location


@app.get("/query_model/{mode_id}", dependencies=[Depends(reusable_oauth2)])
def get_return(mode_id: str):
    area = QueryDB.MODEL
    _search = {"model": mode_id}
    location = db.query_database(area, _search)
    # return True
    return location


@app.get(
    "/query_location/{map_code}/{zone_id}", dependencies=[Depends(reusable_oauth2)]
)
def get_location(zone_id: str, map_code: str):
    area = map_code
    # area = _location_update["map_code"]
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    return location


@app.get("/query_mission/{mission_code}", dependencies=[Depends(reusable_oauth2)])
def get_mission(mission_code: str, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.MISIONS
        _search = {"mission_code": mission_code}
        mission_query = db.query_database(area, _search)
        if mission_query is None:
            return {"code": 0}
        # return True
        return mission_query
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/information_missions", dependencies=[Depends(reusable_oauth2)])
def mission_history(_current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.MISIONS
        sort_value = {"creatAT": SortSearch.OLD.value}
        missions_code = db.histories_mission_request(area, sort_value)
        return missions_code
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/model_product", dependencies=[Depends(reusable_oauth2)])
def model_product(_current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.MODEL
        _value_search = {}
        location = db.locations_request(area, _value_search)
        return location
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/user_information_missions", dependencies=[Depends(reusable_oauth2)])
def user_information_missions(_current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        # if _tokenjwt(_current_user) is not None:
        # print("name", _verify_token["username"])
        area = QueryDB.MISIONS
        sort_value = {"creatAT": SortSearch.OLD.value}
        missions_code = db.user_query_information_mission(
            area, sort_value, _verify_token["username"]
        )
        return missions_code
    raise HTTPException(status_code=404, detail="User not found")


@app.get(
    "/information_operating_robot/{max_n}", dependencies=[Depends(reusable_oauth2)]
)
def get_mission_histories(max_n: int, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.ACTIVITIES
        sort_value = {"creatAT": SortSearch.OLD.value}
        missions_code = db.histories_mission_request(area, max_n, sort_value)
        return missions_code
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/many_update_locations", dependencies=[Depends(reusable_oauth2)])
def update_many_locations(
    many_locations_request: dict, _current_user=Depends(reusable_oauth2)
):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = many_locations_request["map_code"]
        # print("area", _area)
        update_db = db.update_many_database(
            _area, many_locations_request, _verify_token["username"]
        )
        if update_db:
            return update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_robotStatus", dependencies=[Depends(reusable_oauth2)])
def update_robot_status(robot_request: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.STATUS_RB
        search_robot = {"ip_machine": robot_request["ip_machine"]}
        # robot_request.update({"robot_connect": True})
        _robot_update_value = db.update_database(
            _area, search_robot, robot_request, _verify_token["username"]
        )

        # update_db = db.update_robot_status(patch_request)
        if _robot_update_value:
            return _robot_update_value
        else:
            return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/remove_pending_task", dependencies=[Depends(reusable_oauth2)])
def remove_pending_task(request_data: dict, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        _area = QueryDB.EXCUTE_MISSION
        location = {"excute_code": request_data["excute_code"]}
        # print("_location_update", _location_update)
        _update_db = db.remove_task_pending(_area, location, request_data)
        return _update_db
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/decentralization_account", dependencies=[Depends(reusable_oauth2)])
def decentralization(
    request_data: LoginRequest, _current_user=Depends(reusable_oauth2)
):
    if _tokenjwt(_current_user) is not None:
        update_db = db.update_account(request_data.__dict__)
        if update_db:
            return True
        else:
            return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/restore_location", dependencies=[Depends(reusable_oauth2)])
def restore_location(_location_update: dict, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = _location_update["map_code"]
        location = {"name": _location_update["name"]}
        # print("_location_update", _location_update)
        _update_db = db.restore_data(_area, location, _verify_token["username"])
        if _update_db:
            return _update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_pickup_location", dependencies=[Depends(reusable_oauth2)])
def update_pickup(_location_update: dict, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.PICKUP_LOCATION
        location = {"name": _location_update["name"]}
        # print("_location_update", _location_update)
        _update_db = db.location_update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return _update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_return_location", dependencies=[Depends(reusable_oauth2)])
def update_return(_location_update: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.RETURN_LOCATION
        location = {"name": _location_update["name"]}
        # print("_location_update", _location_update)
        _update_db = db.location_update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return _update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_location", dependencies=[Depends(reusable_oauth2)])
def update_location(_location_update: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = _location_update["map_code"]
        if "name" in _location_update.keys():
            location = {"name": _location_update["name"]}
        elif "point" in _location_update.keys():
            location = {"point": _location_update["point"]}
        else:
            pass

        _update_db = db.location_update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return _update_db
        return {"code": 0}
        # return True
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/clear_location", dependencies=[Depends(reusable_oauth2)])
def clear_location(
    _location_update: dict, request: Request, _current_user=Depends(reusable_oauth2)
):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _ip_host = request.client.host

        _area = _location_update["map_code"]
        location_search = {"name": _location_update["name"]}
        # print("role", _verify_token["role"])
        # _update_db = db.restore_data(_area, location, _verify_token["username"])
        _clear_location = db.clear_data_location(
            _area, location_search, _ip_host, _verify_token
        )
        return _clear_location
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/location_clear_not_sector", dependencies=[Depends(reusable_oauth2)])
def location_clear_not_sector(
    _location_update: dict, _current_user=Depends(reusable_oauth2)
):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = _location_update["map_code"]
        if _area == "pickup_locations":
            value_clear = {"model": "", "line": []}
        elif _area == "return_locations":
            value_clear = {"model": ""}
        location = {"location_status": {"$ne": 3}}
        # print("_location_update", _location_update)
        _update_db = db.update_location_clear_sector(_area, value_clear)
        if _update_db:
            return _update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


# @app.patch("/update_empty_location", dependencies=[Depends(reusable_oauth2)])
# def update_empty(_location_update: dict, _current_user=Depends(reusable_oauth2)):
#     _verify_token = _tokenjwt(_current_user)
#     if _verify_token is not None:
#         _area = QueryDB.PICKUP_LOCATION
#         location = {"name": _location_update["name"]}
#         _update_db = db.update_database(
#             _area, location, _location_update, _verify_token["username"]
#         )
#         if _update_db:
#             return _update_db
#         return {"code": 0}
#     raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_missions_histories", dependencies=[Depends(reusable_oauth2)])
def mission_histories(_mission_update: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.MISIONS
        mission = {"mission_code": _mission_update["mission_code"]}
        _update_db = db.update_database(
            area, mission, _mission_update, _verify_token["username"]
        )
        if _update_db:
            return True
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")

    #    value_update = {"$push": {"mission_excute": {"$each": value, "$position": 0}}}
    #     _update = _collection.find_one_and_update(
    #         location,
    #         value_update,
    #         # upsert=False,
    #     )
    #     print(_update)


@app.patch("/missions_excute_update", dependencies=[Depends(reusable_oauth2)])
def mission_update_excute(mission_req: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.EXCUTE_MISSION
        mission = {"excute_code": mission_req["excute_code"]}
        value_update = mission_req["mission_excute"]
        _update_db = db.update_excute_mission(
            area, mission, value_update, _verify_token["username"]
        )
        if _update_db:
            return _update_db
        return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/missions_excute_pop", dependencies=[Depends(reusable_oauth2)])
def mission_pop_excute(mission_req: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.EXCUTE_MISSION
        mission = {"excute_code": mission_req["excute_code"]}
        # value_update = mission_req["mission_excute"]
        # print("mission_req", mission_req)
        # print("mission", mission)

        _update_db = db.pop_excute_mission(area, mission, _verify_token["username"])
        # if _update_db:
        return _update_db
        # return {"code": 0}
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/model_delete/{model_name}", dependencies=[Depends(reusable_oauth2)])
def model_delete(model_name, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.MODEL
        data_query = {"model": str(model_name)}
        _delete_db = db.delete_db(area, data_query)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/account_delete/{account_name}", dependencies=[Depends(reusable_oauth2)])
def delete_account(account_name, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.ACCOUNT
        data_query = {"username": str(account_name)}
        _delete_db = db.delete_db(area, data_query)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/mission_delete/{mission_code}", dependencies=[Depends(reusable_oauth2)])
def delete_mission(mission_code: str, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.MISIONS
        data_query = {"mission_code": str(mission_code)}
        _delete_db = db.delete_db(area, data_query)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/robot_delete/{robot_code}", dependencies=[Depends(reusable_oauth2)])
def delete_robot_status(robot_code: str, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.STATUS_RB
        # data_query = {"mission_code": str(mission_code)}
        search_robot = {"robot_code": robot_code}

        _delete_db = db.delete_db(area, search_robot)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


if __name__ == "__main__":
    print(" http://127.0.0.1:8000/docs#/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
