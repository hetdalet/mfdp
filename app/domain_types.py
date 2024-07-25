from enum import IntEnum


class TransactionType(IntEnum):
    dep = 1
    wdr = 2


class ServicePricingType(IntEnum):
    fixed = 1
    token = 2
