from enum import Enum


class MainState(Enum):
    NONE = -1
    INIT = 0
    CREATE_TASK = 1
    WAIT_PROCESS = 2
    PROCESSING = 3
    CANCEL = 4
    PROCESS_CANCEL = 5
    DONE = 6
    DONE_PROCESS = 7
    TASK_REGISTER = 8
    REGISTER_AGAIN = 9
    FINISH = 10


class TaskStatus(Enum):
    EXCEPTION = 0
    CREATE = 1
    EXECUTING = 2
    TAKE = 5
    ELEVATOR = 7
    # PUT = 3
    RESENDING = 6
    CANCEL = 9
    COMPLETE = 11


class SignalCallbox:
    NONE = 0
    SIGN_SUCCESS = 1
    SIGN_ERROR = 2
    CANCEL_SUCCESS = 3
    CANCEL_ERROR = 4


# class MissionStatus:
#     SIGN = "registered"
#     PROCESS = "processing"
#     CANCEL = "cancel"
#     DONE = "accomplished"
#     PENDING = "pending"


class Sectors:
    OP_WH = "Pallet electric"
    IP_CT = "Pallet carton"
    IP_EMPTY = "Pallet empty"


class LocationStatus(Enum):
    GOODS = 3
    EMPTY_LOCATION = 5
    EMPTY_STOCK = 6
    ROBOT_TRANSPORTING = 8
    # UNAVAILABLE = "unavailable"
    # FILL = "fill"
    DISABLE = 9


class SortSearch(Enum):
    OLD = -1
    NEW = 1


class MapCode:
    T1 = "pickup_locations"
    T2 = "return_locations"


class DeviceControl:
    ON = 1
    OFF = 100
