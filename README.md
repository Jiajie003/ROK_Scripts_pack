# Resource Gatherer Bot

A Python script to automate resource gathering in Rise of Kingdoms across different screen resolutions by using relative coordinates.

## Features

- Dynamically computes click positions based on window size and position
- Supports gathering gold, stone, wood, and corn with up to five troops
- Automatic formation switching after first troop dispatch

## Prerequisites

- Python 3.7 or higher
- Windows

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Jiajie003/ROK_Scripts_pack.git ROK_Scripts
   cd ROK_Scripts
   ```

2. **Create and activate a virtual environment**
      ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
   ```

3. **Upgrade pip (optional)**
   ```bash
    python -m pip install --upgrade pip
   ```

4. **Install dependencies**
   ```bash
    pip install -r requirements.txt
   ```

## Configuration
1. **Account settings**
   Edit accounts.json and add your Lilith account credentials and character-switch flag:
   ```bash
   {
        "username": "email1@gmail.com",
        "password": "exp123",
        "character": 0 
    }
   ```
   character: set to 1 if you have two characters to switch between, otherwise 0

2. Launcher path
   Open resource_config.json and set your local launcher executable path:
    ```bash
   {
        "launcher_path": "C:\\Program Files (x86)\\Rise of Kingdoms\\launcher.exe",
    }
   ```

3. Initial resolution
   For first-time setup, set your desktop and game resolution to 1280×720, then close the game and launcher.

## Usage
1. Ensure your game window is visible and not minimized.
2. Activate the virtual environment by running activate_venv_pws.bat as administrator.
3. Then, run the main script:
    ```bash
    python start_game.py
   ```
    or run without a console window:
   ```bash
    pythonw start_game.py
   ```
   
   The script will launch the game launcher, enter the game, and begin resource gathering automatically.

