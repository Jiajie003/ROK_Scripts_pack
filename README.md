# Resource Gatherer Bot

## 中文说明
一个使用相对坐标在《Rise of Kingdoms》中自动采集资源的 Python 脚本，适用于不同屏幕分辨率。

## 功能

- 根据游戏窗口的尺寸和位置，动态计算点击坐标  
- 支持最多五队部队自动采集金币、石头、木材和粮食  
- 首次派遣后自动切换阵型  

## 环境要求

- Python 3.7 及以上  
- Windows 操作系统  

## 安装

1. **克隆仓库**  
   ```bash
   git clone https://github.com/Jiajie003/ROK_Scripts_pack.git ROK_Scripts
   cd ROK_Scripts
   ```

2. **创建并激活虚拟环境**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   ```

3. **(可选）升级 pip**
   ```bash
    python -m pip install --upgrade pip
   ``

4. **安装依赖**
   ```bash
    pip install -r requirements.txt
   ```
## 配置
1. **添加账号信息**
   编辑 accounts.json，按以下格式填写你的 Lilith 账号和角色设置：
   ```bash
   {
        "username": "email1@gmail.com",
        "password": "exp123",
        "character": 0 
    }
   ```
   character：如果该账号有两个角色需自动切换，填 1；否则填 0。

2. 配置启动器路径
   用编辑器打开 resource_config.json，将 launcher_path 替换为你本地的启动器可执行文件完整路径：
    ```bash
   {
        "launcher_path": "C:\\Program Files (x86)\\Rise of Kingdoms\\launcher.exe",
    }
   ```

3. 预设分辨率
   为保证首次配置顺利，请将游戏分辨率都设置为 1280×720，然后退出游戏和启动器。

## 使用
1. 确保游戏窗口未最小化且可见。
2. 激活虚拟环境：右键以管理员身份运行 activate_venv_pws.bat。
3. 启动脚本：
    ```bash
    python start_game.py
   ```
    或者使用无控制台模式：
   ```bash
    pythonw start_game.py
   ```
脚本会自动启动启动器、进入游戏并开始资源采集。

## English ver
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
    python -m venv venv
    # Windows
    venv\Scripts\activate
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

