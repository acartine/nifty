from enum import Enum


# TODO: replace this with StrEnum (3.11)
class ClaimNamespace(str, Enum):
    """
    Corresponds to a worker so that 'n' workers can subscribe to the same channel/msg
    """

    trend = "trend"
    trend_link = "trend_link"
    image = "image"
