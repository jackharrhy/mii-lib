"""Mii extraction functions"""

from pathlib import Path
from typing import List, Optional

from .types import MiiType


class MiiExtractionError(Exception):
    """Exception raised during Mii extraction"""

    pass


def extract_miis_from_type(
    mii_type: MiiType, input_file: Optional[Path] = None, output_dir: Path = Path(".")
) -> List[Path]:
    """Extract Miis from a specific database type

    Args:
        mii_type: The type of Mii database to extract from
        input_file: Optional custom input database file path. If None, uses mii_type.SOURCE
        output_dir: Directory where extracted .mii files will be saved

    Returns:
        List of Path objects for the extracted Mii files

    Raises:
        MiiExtractionError: If the source file doesn't exist or permission is denied
    """
    source_file = input_file or Path(mii_type.SOURCE)

    if not source_file.exists():
        raise MiiExtractionError(f"{source_file} not found")

    mii_padding = bytearray(mii_type.PADDING)
    empty_mii = bytearray(mii_type.SIZE)
    mii_count = 0
    is_active = True
    extracted_files: List[Path] = []

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(source_file, "rb") as infile:
            infile.seek(mii_type.OFFSET)

            while is_active and mii_count < mii_type.LIMIT:
                mii_data = infile.read(mii_type.SIZE)

                # Stop if we've run out of data
                if len(mii_data) < mii_type.SIZE:
                    is_active = False
                # Skip empty Miis but continue reading
                elif mii_data == empty_mii:
                    continue
                else:
                    mii_name = f"{mii_type.PREFIX}{mii_count:05d}.mii"
                    output_path = output_dir / mii_name

                    with open(output_path, "wb") as outfile:
                        outfile.write(mii_data + mii_padding)

                    extracted_files.append(output_path)
                    mii_count += 1

    except PermissionError as e:
        raise MiiExtractionError(f"Permission denied accessing {source_file}") from e

    return extracted_files
