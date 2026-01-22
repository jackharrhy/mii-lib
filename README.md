# mii-lib

https://jackharrhy.github.io/mii-lib/

https://pypi.org/project/mii-lib/

Library and CLI for extracting .mii files from misc. Wii/Dolphin data dumps, and extracting information from them (name, fav. color, gender, etc.)

## Installation

- Library only: `pip install mii-lib`
- With CLI: `pip install mii-lib[cli]` / `uvx mii-cli --help` / etc.

## Usage

```python
from pathlib import Path
from mii import MiiDatabase, MiiParser, MiiType

database = MiiDatabase(Path("RFL_DB.dat"), MiiType.WII_PLAZA)
mii = database[0]
print(mii.name)
print(mii.favorite_color)

for mii in database:
    print(f"{mii.name} by {mii.creator_name}")

with open("WII_PL00000.mii", "rb") as f:
    mii_data = f.read()

mii = MiiParser.parse(mii_data)
print(mii.get_birthday_string())
```

More complete examples can be found in [examples/library_usage.py](./examples/library_usage.py)

## RFL_DB.dat

This is all based around reading from a [`RFL_DB.dat` file](https://wiibrew.org/wiki//shared2/menu/FaceLib/RFL_DB.dat).

The library automatically checks for database files in known Dolphin Emulator locations:

- `C:\Users\<Your Username>\Documents\Dolphin Emulator\Wii\shared2\menu\FaceLib\`
- `C:\Users\<Your Username>\AppData\Roaming\Dolphin Emulator\Wii\shared2\menu\FaceLib\`
- `~/.dolphin-emu/Wii/shared2/menu/FaceLib/`

If the database file is not in your current directory, the library will automatically search these locations. If none of these exist, check where Dolphin is saving its data to in its settings, and provide the full path when creating a `MiiDatabase`.

---

Originally based on https://github.com/PuccamiteTech/PyMii/
