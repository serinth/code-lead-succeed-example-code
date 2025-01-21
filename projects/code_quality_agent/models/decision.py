from enum import Enum

class Decision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"