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


class TaskStatus:
    EXCEPTION = "0"
    CREATE = "1"
    EXECUTING = "2"
    SENDING = "3"
    CANCEL = "4"
    RESENDING = "6"
    COMPLETE = "9"


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
    OP_WH = "Pallet thành phẩm"
    IP_CT = "Pallet carton"
    IP_EMPTY = "Chồng pallet rỗng"


class LocationStatus:
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    FILL = "fill"
    DISABLE = "disable"


class DeviceControl:
    ON = 1
    OFF = 100
