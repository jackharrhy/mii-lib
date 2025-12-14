"""Mii database type definitions"""

from enum import Enum


class MiiType(Enum):
    """Enum describing different Mii database types with their configurations"""

    WII_PLAZA = ("RFL_DB.dat", 0x4, 74, 0, 49, "WII_PL")
    WII_PARADE = ("RFL_DB.dat", 0x1F1E0, 64, 10, 10_000, "WII_PA")
    WIIU_MAKER = ("FFL_ODB.dat", 0x8, 92, 0, 3_000, "WIIU_MA")
    _3DS_MAKER = ("CFL_DB.dat", 0x8, 92, 0, 100, "3DS_MA")

    def __init__(
        self, source: str, offset: int, size: int, padding: int, limit: int, prefix: str
    ):
        self.SOURCE = source
        self.OFFSET = offset
        self.SIZE = size
        self.PADDING = padding
        self.LIMIT = limit
        self.PREFIX = prefix

    @property
    def display_name(self) -> str:
        """Return a human-readable name for the Mii type"""
        return self.name.lower().replace("_", "-")
