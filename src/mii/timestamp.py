"""Timestamp utilities for Mii files"""

from datetime import datetime, timedelta


def get_mii_mode(filename: str, file_size: int) -> bool:
    """Determine if a Mii file is from Wii (True) or 3DS/WiiU (False)"""
    if file_size == 74:
        return True  # Wii Mii
    elif file_size == 92:
        return False  # 3DS/WiiU Mii
    else:
        raise ValueError(f"{filename}'s format is unknown (size: {file_size})")


def get_mii_seconds(file_handle, is_wii_mii: bool) -> int:
    """Extract timestamp seconds from Mii file"""
    multiplier = 4 if is_wii_mii else 2
    seek_pos = 0x18 if is_wii_mii else 0xC

    file_handle.seek(seek_pos)
    str_id = file_handle.read(4).hex()
    int_id = int(str_id[1:], 16)
    return int_id * multiplier


def get_mii_datetime(seconds: int, is_wii_mii: bool) -> datetime:
    """Convert Mii timestamp seconds to datetime"""
    base_date = datetime(2006, 1, 1) if is_wii_mii else datetime(2010, 1, 1)
    shift = timedelta(seconds=seconds)
    return base_date + shift
