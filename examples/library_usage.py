#!/usr/bin/env python3
"""
Example usage of the mii library for programmatic Mii file extraction and analysis

This demonstrates how to use the library without the CLI interface.
"""

from pathlib import Path
from mii import (
    MiiFileReader,
    MiiType,
    extract_miis_from_type,
    MiiExtractionError,
    get_mii_mode,
    get_mii_seconds,
    get_mii_datetime,
)


def example_extract_single_type():
    """Example: Extract Miis from a specific database type"""
    print("=" * 60)
    print("Example 1: Extracting Miis from Wii Plaza database")
    print("=" * 60)

    output_dir = Path("./extracted_miis")
    input_file = Path("RFL_DB.dat")  # Optional: specify custom input file

    try:
        # Extract from Wii Plaza database
        extracted_files = extract_miis_from_type(
            MiiType.WII_PLAZA,
            input_file=input_file if input_file.exists() else None,
            output_dir=output_dir,
        )

        print(f"Successfully extracted {len(extracted_files)} Miis")
        print(f"Files saved to: {output_dir}")
        print(
            f"First few files: {extracted_files[:3] if len(extracted_files) >= 3 else extracted_files}"
        )

    except MiiExtractionError as e:
        print(f"Extraction failed: {e}")


def example_extract_all_types():
    """Example: Extract Miis from all supported database types"""
    print("\n" + "=" * 60)
    print("Example 2: Extracting Miis from all database types")
    print("=" * 60)

    output_base = Path("./extracted_all")
    total_extracted = 0

    for mii_type in MiiType:
        type_output = output_base / mii_type.display_name
        try:
            extracted_files = extract_miis_from_type(mii_type, output_dir=type_output)
            print(f"{mii_type.display_name}: {len(extracted_files)} Miis extracted")
            total_extracted += len(extracted_files)
        except MiiExtractionError as e:
            print(f"{mii_type.display_name}: Failed - {e}")

    print(f"\nTotal Miis extracted: {total_extracted}")


def example_read_metadata():
    """Example: Read metadata from a single Mii file"""
    print("\n" + "=" * 60)
    print("Example 3: Reading metadata from a Mii file")
    print("=" * 60)

    # Assuming we have a Mii file
    mii_file = Path("./extracted_miis/WII_PL00000.mii")

    if not mii_file.exists():
        print(f"Note: {mii_file} does not exist. Skipping this example.")
        print("Extract some Miis first using example_extract_single_type()")
        return

    try:
        reader = MiiFileReader(mii_file)

        # Read individual fields
        mii_name = reader.read_mii_name()
        creator_name = reader.read_creator_name()
        mii_id = reader.read_mii_id()
        metadata = reader.read_mii_metadata()
        color_name = reader.get_color_name(metadata[3])

        print(f"Mii Name: {mii_name}")
        print(f"Creator: {creator_name}")
        print(f"Mii ID: {mii_id.hex().upper()}")
        print(f"Gender: {'Female' if metadata[0] else 'Male'}")
        print(
            f"Birthday: {metadata[1]}/{metadata[2]}"
            if metadata[1] and metadata[2]
            else "Birthday: Not set"
        )
        print(f"Favorite Color: {color_name}")
        print(f"Is Favorite: {metadata[4]}")

        # Or use the convenience method
        print("\n--- Using read_all_metadata() ---")
        all_metadata = reader.read_all_metadata()
        for key, value in all_metadata.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error reading Mii file: {e}")


def example_batch_metadata():
    """Example: Process multiple Mii files and collect metadata"""
    print("\n" + "=" * 60)
    print("Example 4: Batch processing Mii files")
    print("=" * 60)

    mii_directory = Path("./extracted_miis")
    mii_files = list(mii_directory.glob("*.mii"))

    if not mii_files:
        print(f"No .mii files found in {mii_directory}")
        return

    print(f"Processing {len(mii_files)} Mii files...")

    metadata_list = []
    for mii_file in sorted(mii_files)[:10]:  # Process first 10
        try:
            reader = MiiFileReader(mii_file)
            metadata = reader.read_all_metadata()
            metadata["filename"] = mii_file.name
            metadata_list.append(metadata)
        except Exception as e:
            print(f"Error processing {mii_file.name}: {e}")

    # Print summary
    print(f"\nSuccessfully processed {len(metadata_list)} files")
    print("\nSummary:")
    for meta in metadata_list[:5]:  # Show first 5
        print(f"  {meta['filename']}: {meta['mii_name']} by {meta['creator_name']}")


def example_timestamps():
    """Example: Extract and display creation timestamps"""
    print("\n" + "=" * 60)
    print("Example 5: Extracting creation timestamps")
    print("=" * 60)

    mii_directory = Path("./extracted_miis")
    mii_files = list(mii_directory.glob("*.mii"))

    if not mii_files:
        print(f"No .mii files found in {mii_directory}")
        return

    print(f"Analyzing timestamps for {len(mii_files)} files...\n")

    for mii_file in sorted(mii_files)[:5]:  # Show first 5
        try:
            file_size = mii_file.stat().st_size
            is_wii_mii = get_mii_mode(mii_file.name, file_size)

            with open(mii_file, "rb") as f:
                seconds = get_mii_seconds(f, is_wii_mii)
                creation_time = get_mii_datetime(seconds, is_wii_mii)

            mii_type = "Wii" if is_wii_mii else "3DS/WiiU"
            print(f"{mii_file.name}:")
            print(f"  Type: {mii_type}")
            print(f"  Creation Time: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

        except Exception as e:
            print(f"Error analyzing {mii_file.name}: {e}")


def example_error_handling():
    """Example: Proper error handling"""
    print("\n" + "=" * 60)
    print("Example 6: Error handling")
    print("=" * 60)

    # Try to extract from a non-existent file
    try:
        extracted_files = extract_miis_from_type(
            MiiType.WII_PLAZA,
            input_file=Path("nonexistent.dat"),
            output_dir=Path("./output"),
        )
    except MiiExtractionError as e:
        print(f"Caught expected error: {e}")

    # Try to read a non-existent Mii file
    try:
        reader = MiiFileReader(Path("nonexistent.mii"))
    except FileNotFoundError as e:
        print(f"Caught expected error: {e}")


def example_custom_processing():
    """Example: Custom processing pipeline"""
    print("\n" + "=" * 60)
    print("Example 7: Custom processing pipeline")
    print("=" * 60)

    mii_directory = Path("./extracted_miis")
    mii_files = list(mii_directory.glob("*.mii"))

    if not mii_files:
        print(f"No .mii files found in {mii_directory}")
        return

    # Filter Miis by favorite color
    red_miis = []
    for mii_file in mii_files:
        try:
            reader = MiiFileReader(mii_file)
            metadata = reader.read_all_metadata()
            if metadata["favorite_color"] == "Red":
                red_miis.append((mii_file.name, metadata["mii_name"]))
        except Exception:
            pass

    print(f"Found {len(red_miis)} Miis with Red as favorite color:")
    for filename, name in red_miis[:5]:
        print(f"  {filename}: {name}")


if __name__ == "__main__":
    print("Mii Library Usage Examples")
    print("=" * 60)
    print("\nNote: Some examples require extracted Mii files.")
    print("Run example_extract_single_type() first to extract some Miis.\n")

    # Run examples
    example_extract_single_type()
    example_extract_all_types()
    example_read_metadata()
    example_batch_metadata()
    example_timestamps()
    example_error_handling()
    example_custom_processing()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
