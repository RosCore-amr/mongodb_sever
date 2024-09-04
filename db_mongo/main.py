#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jwt
import uvicorn

from datetime import datetime, timedelta, timezone
from typing import Union, Any
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ValidationError
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from db_control import MongoDB, QueryDB


SECURITY_ALGORITHM = "HS256"
SECRET_KEY = "123456"
EOL_TOKEN = 15
db = MongoDB("mongodb://localhost:27017/")

app = FastAPI(
    title="FastAPI JWT",
    openapi_url="/openapi.json",
    docs_url="/docs",
    description="fastapi jwt",
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
    robot_name: str
    battery: int
    status: str
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


class RobotInformations(BaseModel):
    robot_code: str
    robot_type: str
    ip: str

    # return_location: str


class Mission(BaseModel):
    robot_code: str
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


def generate_token(username: Union[str, Any], password: Union[str, Any], role) -> str:
    # expire = datetime.now(timezone.utc) + timedelta(
    #     seconds=60 * 60 * 24 * 3  # Expired after 3 days
    # )
    expire = datetime.now(timezone.utc) + timedelta(days=EOL_TOKEN)
    to_encode = {
        "exp": expire,
        "username": username,
        "password": password,
        "role": role,
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=SECURITY_ALGORITHM)
    return encoded_jwt


def _tokenjwt(current_user=Depends(reusable_oauth2)) -> dict:

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
    if_acount = verify_password(decoded_token["username"], decoded_token["username"])
    exp_timestamp = decoded_token["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
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


@app.post("/test_demo")
def decode_jwt():
    # test = generate_token("admin", "admin")
    pass
    # decoded_token = jwt.decode(
    #     verify_token.encode(),
    #     SECRET_KEY,
    #     algorithms=SECURITY_ALGORITHM,
    # )
    # test = db.query_robot_status("robot_1")
    # # time_count = test
    # time = int(test["lastUpdate"]["$date"])
    # x = datetime(1, 1, 1) + timedelta(microseconds=time / 10)
    # # if _tokenjwt(current_user) is not None:

    # #     pass

    # raise HTTPException(status_code=404, detail="User not found")
    # verify_token = current_user.credentials
    # decoded_token = jwt.decode(
    #     verify_token.encode(),
    #     SECRET_KEY,
    #     algorithms=SECURITY_ALGORITHM,
    # )
    # return True


@app.post("/Singin")
def login(request_data: LoginRequest):
    _login = verify_password(
        username=request_data.username, password=request_data.password
    )
    if _login is not None and _login:

        token = generate_token(
            request_data.username, request_data.password, request_data.role
        )
        login_if = {
            "username": _login["username"],
            "password": _login["password"],
            "role": _login["role"],
            "token": token,
        }

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
def mission_code(mission: Mission, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:

        _mission_db = db.creat_missions(mission.__dict__, _verify_token["username"])
        return _mission_db
        # return True
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/add_new_robot", dependencies=[Depends(reusable_oauth2)])
def robot_code(
    _robot_information: RobotInformations, _current_user=Depends(reusable_oauth2)
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


@app.get("/all_acoount", dependencies=[Depends(reusable_oauth2)])
def get_all_account():

    area = QueryDB.ACCOUNT
    # area =  QueryDB.l
    location = db.locations_request(
        area,
    )
    return location


@app.get("/robot_status{robot_code}", dependencies=[Depends(reusable_oauth2)])
def get_robot_status(robot_code: str):

    area = QueryDB.STATUS_RB
    # _query = _collection.find_one({"robot_name": _robot_name[i]})
    search_robot = {"robot_name": robot_code}

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
    location = db.locations_request(
        area,
    )
    return location


@app.get("/all_return", dependencies=[Depends(reusable_oauth2)])
def all_returnLocation():
    area = QueryDB.RETURN_LOCATION
    location = db.locations_request(
        area,
    )
    return location


@app.get("/all_emmpty", dependencies=[Depends(reusable_oauth2)])
def all_emptyLocation():
    area = QueryDB.WAIT_LOCATION
    location = db.locations_request(
        area,
    )
    return location


@app.get("/operating_activities/{robot_code}", dependencies=[Depends(reusable_oauth2)])
def get_pickup(robot_code: str):
    area = QueryDB.ACTIVITIES
    _search = {"robot_code": robot_code}
    location = db.query_database(area, _search)
    return location


@app.get("/query_pickup/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def get_pickup(zone_id: str):
    area = QueryDB.PICKUP_LOCATION
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    return location


@app.get("/query_return/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def get_return(zone_id: str):
    area = QueryDB.RETURN_LOCATION
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    # return True
    return location


@app.get("/query_empty/{zone_id}", dependencies=[Depends(reusable_oauth2)])
def get_empty(zone_id: str):
    area = QueryDB.WAIT_LOCATION
    _search = {"name": zone_id}
    location = db.query_database(area, _search)
    return location


@app.get("/query_mission/{mission_code}", dependencies=[Depends(reusable_oauth2)])
def get_mission(mission_code: str, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.MISIONS
        _search = {"mission_code": mission_code}
        location = db.query_database(area, _search)
        # return True
        return location
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/information_missions/{max_n}", dependencies=[Depends(reusable_oauth2)])
def get_mission_histories(max_n: int, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.MISIONS
        missions_code = db.histories_mission_request(area, max_n)
        return missions_code
    raise HTTPException(status_code=404, detail="User not found")


@app.get(
    "/information_operating_robot/{max_n}", dependencies=[Depends(reusable_oauth2)]
)
def get_mission_histories(max_n: int, _current_user=Depends(reusable_oauth2)):
    if _tokenjwt(_current_user) is not None:
        area = QueryDB.ACTIVITIES
        missions_code = db.histories_mission_request(area, max_n)
        return missions_code
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_robotStatus", dependencies=[Depends(reusable_oauth2)])
def update_robot_status(
    patch_request: StatusRequestUpdate, _current_user=Depends(reusable_oauth2)
):
    if _tokenjwt(_current_user) is not None:
        update_db = db.update_robot_status(
            patch_request.robot_name,
            patch_request.status,
            patch_request.mission,
            patch_request.battery,
        )
        if update_db:
            return True
        else:
            raise HTTPException(status_code=404, detail="Update Fail ")
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
            raise HTTPException(status_code=404, detail="Update Fail ")
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_pickup_location", dependencies=[Depends(reusable_oauth2)])
def update_pickup(_location_update: dict, _current_user=Depends(reusable_oauth2)):

    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.PICKUP_LOCATION
        location = {"name": _location_update["name"]}
        _update_db = db.update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return True
        raise HTTPException(status_code=404, detail="Update Fail ")
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_return_location", dependencies=[Depends(reusable_oauth2)])
def update_return(_location_update: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.RETURN_LOCATION
        location = {"name": _location_update["name"]}
        _update_db = db.update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return True
        raise HTTPException(status_code=404, detail="Update Fail ")
    raise HTTPException(status_code=404, detail="User not found")


@app.patch("/update_empty_location", dependencies=[Depends(reusable_oauth2)])
def update_empty(_location_update: dict, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        _area = QueryDB.WAIT_LOCATION
        location = {"name": _location_update["name"]}
        _update_db = db.update_database(
            _area, location, _location_update, _verify_token["username"]
        )
        if _update_db:
            return True
        raise HTTPException(status_code=404, detail="Update Fail ")

    raise HTTPException(status_code=404, detail="User not found")


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
        raise HTTPException(status_code=404, detail="Update Fail ")
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/account_delete{account_name}", dependencies=[Depends(reusable_oauth2)])
def delete_account(account_name, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.ACCOUNT
        data_query = {"username": str(account_name)}
        _delete_db = db.delete_db(area, data_query)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/mission_delete{mission_code}", dependencies=[Depends(reusable_oauth2)])
def delete_mission(mission_code: str, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.MISIONS
        data_query = {"mission_code": str(mission_code)}
        _delete_db = db.delete_db(area, data_query)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/robot_delete{robot_code}", dependencies=[Depends(reusable_oauth2)])
def delete_robot_status(robot_code: str, _current_user=Depends(reusable_oauth2)):
    _verify_token = _tokenjwt(_current_user)
    if _verify_token is not None:
        area = QueryDB.STATUS_RB
        # data_query = {"mission_code": str(mission_code)}
        search_robot = {"robot_name": robot_code}

        _delete_db = db.delete_db(area, search_robot)
        return _delete_db
    else:
        raise HTTPException(status_code=404, detail="User not found")


if __name__ == "__main__":
    uvicorn.run(app, host="192.168.1.6", port=8000)
