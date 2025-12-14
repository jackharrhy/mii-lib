#!/usr/bin/env python3
"""
Mii Extractor CLI - A tool for extracting .mii files from Dolphin dumped data
"""

import csv
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from mii import (
    MiiFileReader,
    MiiType,
    extract_miis_from_type,
    MiiExtractionError,
    get_mii_mode,
    get_mii_seconds,
    get_mii_datetime,
)

app = typer.Typer(help="Extract and analyze Mii files from Wii/Dolphin files")
console = Console()


@app.command()
def extract(
    mii_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Specific Mii type to extract (wii-plaza, wii-parade, wiiu-maker, 3ds-maker)",
    ),
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Custom input database file path"
    ),
    output_dir: Path = typer.Option(
        Path("."), "--output", "-o", help="Output directory for extracted .mii files"
    ),
):
    """Extract Mii files from Nintendo console database dumps"""

    if mii_type:
        # Extract specific type
        try:
            # Handle the special case of 3DS_MAKER
            enum_name = mii_type.upper().replace("-", "_")
            if enum_name == "3DS_MAKER":
                selected_type = MiiType._3DS_MAKER
            else:
                selected_type = MiiType[enum_name]

            try:
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Extracting {selected_type.PREFIX} Miis...",
                        total=selected_type.LIMIT,
                    )

                    # Wrap extraction with progress tracking
                    extracted_files = extract_miis_from_type(
                        selected_type, input_file, output_dir
                    )
                    progress.update(task, completed=len(extracted_files))

                console.print(
                    f"[green]Extracted {len(extracted_files)} {selected_type.PREFIX} Miis to {output_dir}[/green]"
                )
                total_extracted = len(extracted_files)

            except MiiExtractionError as e:
                console.print(f"[red]Error: {e}[/red]")
                raise typer.Exit(1)

        except KeyError:
            console.print(f"[red]Error: Unknown Mii type '{mii_type}'[/red]")
            console.print("Valid types: wii-plaza, wii-parade, wiiu-maker, 3ds-maker")
            raise typer.Exit(1)
    else:
        # Extract all types
        console.print("[bold]Extracting from all supported database types...[/bold]")
        total_extracted = 0

        for mii_enum in MiiType:
            try:
                with Progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Extracting {mii_enum.PREFIX} Miis...",
                        total=mii_enum.LIMIT,
                    )

                    extracted_files = extract_miis_from_type(mii_enum, None, output_dir)
                    progress.update(task, completed=len(extracted_files))

                total_extracted += len(extracted_files)
            except MiiExtractionError:
                # Continue with other types if one fails
                pass

        console.print(
            f"\n[bold green]Total Miis extracted: {total_extracted}[/bold green]"
        )


@app.command()
def times(
    directory: Path = typer.Option(
        Path("."), "--directory", "-d", help="Directory containing .mii files"
    ),
):
    """Calculate and display creation times for Mii files"""

    if not directory.exists():
        console.print(f"[red]Error: Directory {directory} does not exist[/red]")
        raise typer.Exit(1)

    mii_files = list(directory.glob("*.mii"))
    if not mii_files:
        console.print(f"[yellow]No .mii files found in {directory}[/yellow]")
        return

    console.print(f"[bold]Analyzing {len(mii_files)} .mii files...[/bold]\n")

    table = Table(title="Mii Creation Times")
    table.add_column("Filename", style="cyan")
    table.add_column("Creation Time", style="green")
    table.add_column("Type", style="blue")

    successful_analyses = 0

    for mii_file in sorted(mii_files):
        try:
            file_size = mii_file.stat().st_size
            is_wii_mii = get_mii_mode(mii_file.name, file_size)

            with open(mii_file, "rb") as infile:
                seconds = get_mii_seconds(infile, is_wii_mii)
                creation_time = get_mii_datetime(seconds, is_wii_mii)

                mii_type = "Wii" if is_wii_mii else "3DS/WiiU"
                table.add_row(
                    mii_file.name, creation_time.strftime("%Y-%m-%d %H:%M:%S"), mii_type
                )
                successful_analyses += 1

        except Exception as err:
            console.print(f"[red]Error analyzing {mii_file.name}: {err}[/red]")

    console.print(table)
    console.print(
        f"\n[green]Successfully analyzed {successful_analyses}/{len(mii_files)} files[/green]"
    )


@app.command()
def metadata(
    directory: Path = typer.Option(
        Path("."), "--directory", "-d", help="Directory containing .mii files"
    ),
    single_file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Analyze a single .mii file"
    ),
    csv_output: Optional[Path] = typer.Option(
        None, "--csv", "-c", help="Save results to CSV file"
    ),
):
    """Display metadata for Mii files (names, colors, birthdays, etc.)"""

    if single_file:
        # Analyze single file
        if not single_file.exists():
            console.print(f"[red]Error: File {single_file} does not exist[/red]")
            raise typer.Exit(1)

        try:
            reader = MiiFileReader(single_file)
            metadata_dict = reader.read_all_metadata()

            table = Table(title=f"Metadata for {single_file.name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Mii Name", metadata_dict["mii_name"])
            table.add_row("Creator Name", metadata_dict["creator_name"])
            table.add_row("Gender", metadata_dict["gender"])
            table.add_row(
                "Birth Month",
                str(metadata_dict["birth_month"])
                if metadata_dict["birth_month"]
                else "Not set",
            )
            table.add_row(
                "Birth Day",
                str(metadata_dict["birth_day"])
                if metadata_dict["birth_day"]
                else "Not set",
            )
            table.add_row("Favorite Color", metadata_dict["favorite_color"])
            table.add_row(
                "Is Favorite", "Yes" if metadata_dict["is_favorite"] else "No"
            )
            table.add_row("Mii ID", metadata_dict["mii_id"])

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error reading {single_file}: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Analyze directory
        if not directory.exists():
            console.print(f"[red]Error: Directory {directory} does not exist[/red]")
            raise typer.Exit(1)

        mii_files = list(directory.glob("*.mii"))
        if not mii_files:
            console.print(f"[yellow]No .mii files found in {directory}[/yellow]")
            return

        console.print(f"[bold]Analyzing {len(mii_files)} .mii files...[/bold]\n")

        results = []
        successful_analyses = 0

        for mii_file in sorted(mii_files):
            try:
                reader = MiiFileReader(mii_file)
                metadata_dict = reader.read_all_metadata()

                result_data = {
                    "filename": mii_file.name,
                    **metadata_dict,
                }

                results.append(result_data)
                successful_analyses += 1

            except Exception as err:
                console.print(f"[red]Error analyzing {mii_file.name}: {err}[/red]")

        if csv_output:
            # Save to CSV
            if results:
                fieldnames = [
                    "filename",
                    "mii_name",
                    "creator_name",
                    "is_girl",
                    "gender",
                    "birth_month",
                    "birth_day",
                    "birthday",
                    "favorite_color",
                    "favorite_color_index",
                    "is_favorite",
                    "mii_id",
                ]

                with open(csv_output, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results)

                console.print(
                    f"[green]Saved metadata for {len(results)} .mii files to {csv_output}[/green]"
                )
            else:
                console.print("[yellow]No data to save to CSV[/yellow]")
        else:
            # Display table
            table = Table(title="Mii Metadata")
            table.add_column("Filename", style="cyan")
            table.add_column("Mii Name", style="green")
            table.add_column("Creator", style="blue")
            table.add_column("Gender", style="magenta")
            table.add_column("Birthday", style="yellow")
            table.add_column("Favorite Color", style="red")

            for result in results:
                table.add_row(
                    result["filename"],
                    result["mii_name"],
                    result["creator_name"],
                    result["gender"][0],  # Just show M/F for display
                    result["birthday"],
                    result["favorite_color"],
                )

            console.print(table)

        console.print(
            f"\n[green]Successfully analyzed {successful_analyses}/{len(mii_files)} files[/green]"
        )


@app.command()
def info():
    """Display information about supported Mii database types"""

    table = Table(title="Supported Mii Database Types")
    table.add_column("Type", style="cyan")
    table.add_column("Source File", style="green")
    table.add_column("Mii Size", style="blue")
    table.add_column("Max Count", style="yellow")
    table.add_column("Prefix", style="magenta")

    for mii_type in MiiType:
        table.add_row(
            mii_type.display_name,
            mii_type.SOURCE,
            f"{mii_type.SIZE} bytes",
            str(mii_type.LIMIT),
            mii_type.PREFIX,
        )

    console.print(table)
    console.print(
        "\n[dim]Place the appropriate database files in the current directory or specify custom paths with --input[/dim]"
    )


if __name__ == "__main__":
    app()
