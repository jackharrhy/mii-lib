"""Mii database reader and manager"""

import platform
from pathlib import Path
from typing import Iterator, List, Callable, Optional

from .models import Mii
from .parser import MiiParser
from .types import MiiType


class MiiDatabaseError(Exception):
    """Exception raised during Mii database operations"""

    pass


def _get_known_database_locations(filename: str) -> List[Path]:
    """Get list of known locations where database files might be found
    
    Args:
        filename: The database filename to look for (e.g., "RFL_DB.dat")
    
    Returns:
        List of potential paths where the database file might exist
    """
    locations = []
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        # Windows locations
        # Documents location
        docs_path = home / "Documents" / "Dolphin Emulator" / "Wii" / "shared2" / "menu" / "FaceLib" / filename
        locations.append(docs_path)
        
        # AppData Roaming location
        appdata_path = home / "AppData" / "Roaming" / "Dolphin Emulator" / "Wii" / "shared2" / "menu" / "FaceLib" / filename
        locations.append(appdata_path)
    else:
        # Unix-like systems (Linux, macOS, etc.)
        dolphin_path = home / ".dolphin-emu" / "Wii" / "shared2" / "menu" / "FaceLib" / filename
        locations.append(dolphin_path)
    
    return locations


class MiiDatabase:
    """Reads and manages Miis from a database file"""

    def __init__(self, file_path: Path, mii_type: MiiType):
        """Initialize MiiDatabase by reading from a database file

        Args:
            file_path: Path to the database file
            mii_type: Type of Mii database (determines offset, size, etc.)

        Raises:
            MiiDatabaseError: If file doesn't exist or can't be read

        Examples:
            >>> from pathlib import Path
            >>> from mii import MiiDatabase, MiiType
            >>> database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
            >>> print(len(database))
        """
        # If the provided path doesn't exist, check known locations
        if not file_path.exists():
            known_locations = _get_known_database_locations(file_path.name)
            found_path = None
            
            for location in known_locations:
                if location.exists():
                    found_path = location
                    break
            
            if found_path:
                file_path = found_path
            else:
                raise MiiDatabaseError(f"{file_path} not found")

        self.file_path = file_path
        self.mii_type = mii_type
        self._miis: List[Mii] = []
        self._load_miis()

    def _load_miis(self) -> None:
        """Load all Miis from the database file into memory"""
        empty_mii = bytearray(self.mii_type.SIZE)

        try:
            with open(self.file_path, "rb") as infile:
                infile.seek(self.mii_type.OFFSET)

                mii_count = 0
                is_active = True

                while is_active and mii_count < self.mii_type.LIMIT:
                    mii_data = infile.read(self.mii_type.SIZE)

                    # Stop if we've run out of data
                    if len(mii_data) < self.mii_type.SIZE:
                        is_active = False
                    # Skip empty Miis but continue reading
                    elif mii_data == empty_mii:
                        continue
                    else:
                        # Parse the Mii data
                        mii = MiiParser.parse(mii_data, padding=self.mii_type.PADDING)
                        self._miis.append(mii)
                        mii_count += 1

        except PermissionError as e:
            raise MiiDatabaseError(
                f"Permission denied accessing {self.file_path}"
            ) from e
        except Exception as e:
            raise MiiDatabaseError(f"Error reading database: {e}") from e

    def __iter__(self) -> Iterator[Mii]:
        """Make MiiDatabase iterable"""
        return iter(self._miis)

    def __len__(self) -> int:
        """Return count of Miis in database"""
        return len(self._miis)

    def __getitem__(self, index: int) -> Mii:
        """Index access to Miis"""
        return self._miis[index]

    def filter(self, predicate: Callable[[Mii], bool]) -> List[Mii]:
        """Filter Miis by a predicate function

        Args:
            predicate: Function that takes a Mii and returns True to include it

        Returns:
            List of Miis that match the predicate

        Examples:
            >>> database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
            >>> red_miis = database.filter(lambda m: m.favorite_color == "Red")
            >>> named_miis = database.filter(lambda m: m.name and m.name != "Unnamed")
        """
        return [mii for mii in self._miis if predicate(mii)]

    def get_all(self) -> List[Mii]:
        """Get all Miis as a list"""
        return self._miis.copy()

    def get_by_name(self, name: str) -> Optional[Mii]:
        """Get the first Mii with a matching name (case-insensitive)

        Args:
            name: Name to search for

        Returns:
            Mii with matching name, or None if not found

        Examples:
            >>> database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
            >>> mii = database.get_by_name("My Mii")
            >>> if mii:
            ...     print(mii.creator_name)
        """
        name_lower = name.lower()
        for mii in self._miis:
            if mii.name.lower() == name_lower:
                return mii
        return None

    def get_favorites(self) -> List[Mii]:
        """Get all favorite Miis

        Returns:
            List of Miis marked as favorites

        Examples:
            >>> database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
            >>> favorites = database.get_favorites()
            >>> print(f"Found {len(favorites)} favorite Miis")
        """
        return self.filter(lambda m: m.is_favorite)

    def export_all(self, output_dir: Path, prefix: Optional[str] = None) -> List[Path]:
        """Export all Miis from this database to individual files

        Args:
            output_dir: Directory where Mii files should be written
            prefix: Optional prefix for filenames. If None, uses mii_type.PREFIX

        Returns:
            List of Path objects for the exported files

        Examples:
            >>> database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
            >>> exported = database.export_all(Path("./miis"))
            >>> print(f"Exported {len(exported)} Miis")
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_prefix = prefix if prefix is not None else self.mii_type.PREFIX
        exported_paths: List[Path] = []

        for idx, mii in enumerate(self._miis):
            mii_name = f"{file_prefix}{idx:05d}.mii"
            output_path = output_dir / mii_name
            mii.export(output_path)
            exported_paths.append(output_path)

        return exported_paths
