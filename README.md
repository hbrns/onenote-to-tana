# onenote-to-tana

_**onenote-to-tana**_ is a script that converts OneNote Notebook(s) into
a JSON file ready for import into a [Tana](https://tana.inc/) workspace.

## Pre-Requisites

- You must have a Microsoft Windows 10 or 11 system.
- You must have the [OneNote](https://www.onenote.com/Download)
  for Windows Desktop app installed on your system.
- You must have [Python 3](https://www.python.org/downloads/windows/)
  installed on your system. This README assumes it is accessible via
  `python`, but other aliases, such as `python3`, are fine too.
- You must have Python [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
  installed on your system and accessible in your system PATH.  
  Check by running `poetry --version` in a PowerShell or command window.

## OneNote Compatibility

Only the [OneNote](https://www.onenote.com/download/win32/x64/en-US)
Desktop App for Windows is compatible with this script.  
OneNote for Mac, iPad, iPhone, Android, and Web are currently not supported.

## Known Problems

Inline images are currently not support by the Tana Intermediate Format (TIF).
Only image URL references are supported.
Therefore images that are part of an OneNote page can not be imported.
You may _copy&paste_ an image into a Tana node after an import by hand as
a workaround.

## Installation

1. Clone the repository.

    ```sh
    git clone https://github.com/hbrns/onenote-to-tana.git
    cd onenote_to-tana
    ```

2. Install the requirements.

    ```sh
    poetry install
    ```

3. Close the PowerShell or command window used during installation.

    ```sh
    exit
    ```

## Import Notes into Tana

1. Open the OneNote Desktop App and ensure the notebook you would like 
   to convert is open.
2. To convert your OneNote notebook(s), section(s), or page(s) to a JSON file
   for import into Tana, execute the convert script.

    ```bash
    cd onenote_to-tana
    poetry run python onenote-to-tana\convert_to_tif.py --user
    ```

The `--user` argument will enable you to interactively select which
notebook(s), section(s), or page(s) you like to convert.

Use the `--help` argument for an overview on other options.

## Acknowledgements

This script was inspired by the Python version of
[onenote-to-markdown](https://blog.pagekey.io/onenote-to-markdown-python/)
from PageKey.
