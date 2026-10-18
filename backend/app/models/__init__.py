from enum import Enum

SLOT_IDS = ('P01', 'P02', 'P03', 'P04')

class SlotStatus(str, Enum):
    EMPTY = 'EMPTY'
    OCCUPIED = 'OCCUPIED'
    UNKNOWN = 'UNKNOWN'
