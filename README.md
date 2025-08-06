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

## Setting
1. **Add the lilith Account Credential in accounts.json**
   If your your account have two character to swtich set as 1 else one gmail one character as 0, only support two character in one account
   ```bash
   {
        "username": "email1@gmail.com",
        "password": "exp123",
        "character": 0 
    }
   ```

3. Set your ROK PC as 

## Usage
1. Ensure your game window is visible and not minimized.
2. Run the main script:
    ```bash
    python start_game.py
   ```

