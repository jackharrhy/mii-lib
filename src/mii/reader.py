"""Mii file reader for extracting metadata from .mii files"""

from pathlib import Path
from typing import Dict, Any


class MiiFileReader:
    """Reader for extracting metadata from .mii files"""

    def __init__(self, file_path: Path):
        with open(file_path, "rb") as f:
            self.data = f.read()

        self.colors = [
            "Red",
            "Orange",
            "Yellow",
            "Green",
            "DarkGreen",
            "Blue",
            "LightBlue",
            "Pink",
            "Purple",
            "Brown",
            "White",
            "Black",
        ]

    def read_string(self, offset: int, length: int) -> str:
        """Read UTF-16BE string from the file data"""
        string_data = self.data[offset : offset + length]
        # Find the first null terminator (0x0000 in UTF-16BE)
        null_pos = string_data.find(b"\x00\x00")
        if null_pos != -1:
            # Ensure we align to 2-byte boundaries for UTF-16
            if null_pos % 2 != 0:
                null_pos -= 1
            string_data = string_data[: null_pos + 2]

        # Convert from UTF-16BE and remove null terminators
        return string_data.decode("utf-16be").rstrip("\x00")

    def read_mii_name(self) -> str:
        """Read Mii name starting at offset 2"""
        return self.read_string(2, 20)

    def read_creator_name(self) -> str:
        """Read creator name starting at offset 54"""
        return self.read_string(54, 20)

    def read_mii_metadata(self) -> list:
        """Read and parse Mii metadata from first 2 bytes"""
        # Read first 2 bytes and convert to binary string
        metadata_bytes = self.data[0:2]
        binary_str = "".join(format(b, "08b") for b in metadata_bytes)

        # Extract metadata fields
        is_girl = int(binary_str[1], 2)
        birth_month = int(binary_str[2:6], 2)
        birth_day = int(binary_str[6:11], 2)
        favorite_color = int(binary_str[11:15], 2)
        is_favorite = int(binary_str[15], 2)

        return [is_girl, birth_month, birth_day, favorite_color, is_favorite]

    def read_mii_id(self) -> bytes:
        """Read 4-byte Mii ID starting at offset 24"""
        return self.data[24:28]

    def get_color_name(self, color_index: int) -> str:
        """Get color name from color index"""
        if 0 <= color_index < len(self.colors):
            return self.colors[color_index]
        return f"Unknown ({color_index})"

    def read_all_metadata(self) -> Dict[str, Any]:
        """Read all metadata from the Mii file and return as a dictionary"""
        mii_name = self.read_mii_name()
        creator_name = self.read_creator_name()
        metadata = self.read_mii_metadata()
        mii_id = self.read_mii_id()
        color_name = self.get_color_name(metadata[3])

        gender = "Female" if metadata[0] else "Male"
        birthday = (
            f"{metadata[1]}/{metadata[2]}" if metadata[1] and metadata[2] else "Not set"
        )

        return {
            "mii_name": mii_name or "Unnamed",
            "creator_name": creator_name or "Unknown",
            "is_girl": metadata[0],
            "gender": gender,
            "birth_month": metadata[1],
            "birth_day": metadata[2],
            "birthday": birthday,
            "favorite_color": color_name,
            "favorite_color_index": metadata[3],
            "is_favorite": metadata[4],
            "mii_id": mii_id.hex().upper(),
        }
