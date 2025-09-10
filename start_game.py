print(">> start_game.py 已启动")
import json
import logging
import threading
import subprocess
import time
import random
import pygetwindow as gw
import pyautogui
import sys
import os
import ctypes
from pyautogui import ImageNotFoundException
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.scrolledtext as scrolledtext
from datetime import datetime, timedelta
ctypes.windll.shcore.SetProcessDpiAwareness(2)

formation_switched = False

# 禁用快速编辑模式，避免控制台被误点击卡住
def disable_quick_edit():
    try:
        import ctypes
        STD_INPUT_HANDLE = -10
        ENABLE_QUICK_EDIT_MODE = 0x0040
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        kernel32.SetConsoleMode(hStdin, mode.value & ~ENABLE_QUICK_EDIT_MODE)
    except Exception:
        pass

disable_quick_edit()

def safe_move_and_click(x, y, move_duration=(0.10, 0.20)):
    """在需要时临时禁用 fail-safe，移动鼠标到目标再点击，之后恢复"""
    prev = pyautogui.FAILSAFE
    try:
        if prev and pyautogui.position() == (0, 0):
            pyautogui.FAILSAFE = False  # 临时关闭
        pyautogui.moveTo(x, y, duration=random.uniform(*move_duration))
        pyautogui.click()
    finally:
        pyautogui.FAILSAFE = prev

# —— 日志系统（文件 + GUI）配置 —— #
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
date_str = datetime.now().strftime('%Y-%m-%d')
log_path = os.path.join(LOG_DIR, f"{date_str}.txt")

logger = logging.getLogger('rok')
logger.setLevel(logging.DEBUG)

# —— 这个 FileHandler 永远写入日志文件，无视 GUI 开关 —— #
fh = logging.FileHandler(log_path, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(fh)

def debug_log(msg):
    logger.debug(msg)

# 用于控制后台脚本的暂停／恢复
resume_event = threading.Event()
resume_event.set()   # 开始时允许执行

class GuiHandler(logging.Handler):
    """把 logger 输出推到 Tkinter 的 Text 组件里"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    def emit(self, record):
        msg = self.format(record) + '\n'
        # 在主线程安全地把 msg 插到 Text 组件
        self.text_widget.after(0, self._append, msg)
    def _append(self, msg):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg)
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)

# 倒计时窗口
def show_countdown(seconds: int):
    next_run = datetime.now() + timedelta(seconds=seconds)
    win = tk.Toplevel(main_win)  # 用主窗口做父窗口
    win.title("脚本运行状态")
    win.geometry("300x100")
    win.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

    lbl_time = ttk.Label(win, text="", font=("Arial", 10))
    lbl_time.pack(pady=(10,0))
    lbl_count = ttk.Label(win, text="", font=("Arial",12,"bold"))
    lbl_count.pack(pady=(5,10))

    def update():
        rem = (next_run - datetime.now()).total_seconds()
        if rem <= 0:
            return
        lbl_time.config(text=f"下次运行：{next_run:%Y-%m-%d %H:%M:%S}")
        hrs, rem2 = divmod(int(rem),3600)
        mins, secs = divmod(rem2,60)
        lbl_count.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
        win.after(1000, update)

    win.after(0, update)  # 非阻塞地启动

    # —— 可响应暂停的等待 —— #
    for _ in range(seconds):
            resume_event.wait()        # 如果被 clear()，就在这里卡住
            time.sleep(1)
    win.after(0, win.destroy)

# 随机偏移坐标，避免固定点击位置被检测
# def randomize_pos(x, y, min_offset=1, max_offset=3):
#     offset = random.randint(min_offset, max_offset)
#     # 50% 概率取负
#     if random.choice([True, False]):
#         offset = -offset
#     # 随机选择在 x 或 y 轴偏移
#     if random.choice([True, False]):
#         return x + offset, y
#     else:
#         return x, y + offset

def randomize_pos(x, y, left, top, width, height, rel_jitter=0.002, min_px=1, max_px=None):
    """
    相对窗口尺寸的双轴随机抖动，并确保落点仍在窗口内。
    rel_jitter: 抖动半径占窗口最短边的比例（默认 0.2%）
    """
    # 计算抖动像素半径
    base = int(min(width, height) * rel_jitter)
    if max_px is not None:
        base = min(base, max_px)
    base = max(base, min_px)

    # 双轴随机
    jx = random.randint(-base, base)
    jy = random.randint(-base, base)

    rx = x + jx
    ry = y + jy

    # 夹紧到窗口内
    rx = max(left, min(left + width  - 1, rx))
    ry = max(top,  min(top  + height - 1, ry))
    return rx, ry

# 包装点击，带日志和延迟
def wait_and_click(x, y, label="", delay=1.5):
    resume_event.wait()
    rx, ry = randomize_pos(x, y)
    pyautogui.click(rx, ry)
    if label:
        debug_log(f"{label} → 点击位置: ({rx}, {ry}) 原始: ({x}, {y})")
    time.sleep(delay)

# 响应时间延长版点击，用于账号切换等耗时操作
def wait_and_click_slow(x, y, label=""):
    resume_event.wait()
    wait_and_click(x, y, label, delay=5)


def type_text(text, label="", delay=0.5):
    resume_event.wait()
    pyautogui.write(text)
    if label:
        debug_log(f"{label} → 输入: {text}")
    time.sleep(delay)


def close_launcher():
    closed = False
    # 1) 尝试发送 WM_CLOSE
    for w in gw.getWindowsWithTitle('Launcher'):
        try:
            w.close()
            debug_log('通过 pygetwindow 关闭 Launcher 窗口')
            closed = True
        except Exception as e:
            debug_log(f'pygetwindow 关闭 Launcher 失败: {e}')
    # 2) 如果没找到或没关掉，再用 taskkill 强制杀进程
    if not closed:
        subprocess.run(
            ['taskkill', '/IM', 'launcher.exe', '/F'],
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        debug_log('通过 taskkill 强制结束 launcher.exe')


def get_game_window(title_keyword='Rise of Kingdoms'):
     wins = gw.getWindowsWithTitle(title_keyword)
     if not wins:
         raise RuntimeError(...)
     w = wins[0]
     return w.left, w.top, w.width, w.height

def wait_and_click_rel(rel_x, rel_y, label="", delay=1.5):
    resume_event.wait()
    left, top, width, height = get_game_window()

    # 基准绝对坐标（相对 -> 绝对）
    x = left + int(rel_x * width)
    y = top  + int(rel_y * height)

    # 相对窗口尺寸的抖动
    rx, ry = randomize_pos(x, y, left, top, width, height, rel_jitter=0.002, min_px=1, max_px=6)

    # 建议给一点点移动时间，更像真人
    pyautogui.moveTo(rx, ry, duration=random.uniform(0.08, 0.22))
    pyautogui.click()

    if label:
        debug_log(f"{label} → 点击: ({rx},{ry}) 原始rel: ({rel_x:.4f},{rel_y:.4f})")
    time.sleep(delay)

def wait_and_click_slow_rel(rel_x: float, rel_y: float, label: str = "", delay: float = 5.0):
    """
    只接受: wait_and_click_slow_rel(0.36, 0.57, 'xxx')
    """
    resume_event.wait()

    # 合法性检查（可选）
    if not (0.0 <= rel_x <= 1.0 and 0.0 <= rel_y <= 1.0):
        raise ValueError(f"rel_x/rel_y 必须在 [0,1]，当前: ({rel_x}, {rel_y})")

    left, top, width, height = get_game_window()

    # 相对 -> 绝对
    x = left + int(rel_x * width)
    y = top  + int(rel_y * height)

    # 抖动并夹紧到窗口内（如果你已把 randomize_pos 升级为带边界的版本）
    rx, ry = randomize_pos(x, y, left, top, width, height, rel_jitter=0.002, min_px=1, max_px=8)

    # 慢速移动 + 轻按停顿，更像真人
    pyautogui.moveTo(rx, ry, duration=random.uniform(0.25, 0.5))
    pyautogui.mouseDown()
    time.sleep(random.uniform(0.06, 0.12))
    pyautogui.mouseUp()

    if label:
        debug_log(f"{label} → 点击: ({rx},{ry}) 原始rel: ({rel_x:.4f},{rel_y:.4f})")

    time.sleep(delay)


# def collect_city_resources():
#     """
#     城内资源采集：每次激活窗口后都执行，无需开关
#     """
#     debug_log('开始城内收集资源')
#     # 以下坐标根据日志示例：
#     pyautogui.press('space')
#     time.sleep(1)
#     wait_and_click_rel(473, 434, '收玉米')
#     wait_and_click_rel(532, 389, '收木头')
#     wait_and_click_rel(591, 359, '收石头')
#     wait_and_click_rel(650, 314, '收金币')
#     debug_log('城内资源收集完成')

def collect_city_resources():
    debug_log('开始城内收集资源')
    pyautogui.press('space')
    time.sleep(1)

    wait_and_click_rel(0.3657, 0.5705, '收玉米')
    wait_and_click_rel(0.4144, 0.5217, '收木头')
    wait_and_click_rel(0.4568, 0.4704, '收石头')
    wait_and_click_rel(0.5008, 0.4190, '收金币')

    debug_log('城内资源收集完成')

def daily_vip_collect():
    debug_log('开始每日VIP签到')
    wait_and_click_rel(0.0941,0.0975, '打开VIP界面', delay=2)
    wait_and_click_rel(0.7068,0.3386, '收集每日VIP')
    wait_and_click_rel(0.7068,0.3386, '收集每日VIP(2)')
    wait_and_click_rel(0.6574,0.5152, '收集每日金头')
    wait_and_click_slow_rel(0.6574,0.5152, '收集每日金头(2)')
    wait_and_click_slow_rel(0.7407,0.2675, '关闭VIP窗口')
    debug_log('VIP签到完成')


def collect_alliance_resource():
    debug_log('开始收集联盟资源')
    wait_and_click_rel(0.8025,0.9407, '打开联盟')
    wait_and_click_rel(0.6319,0.5547, '打开领土')
    wait_and_click_rel(0.7006,0.3123, '收集领土资源')
    wait_and_click_rel(0.7546,0.2253, '关闭领土')
    wait_and_click_rel(0.7562,0.2266, '关闭联盟')
    debug_log('收集联盟资源完成')

def send_alliance_gather():
    debug_log('开始联盟资源采集')
    wait_and_click_rel(0.8017,0.9499, '打开联盟')
    wait_and_click_rel(0.6304,0.5507, '打开领土')
    wait_and_click_rel(0.7438,0.3900, '关闭领土建筑')
    wait_and_click_rel(0.7407,0.4783, '打开联盟资源')
    wait_and_click_rel(0.6034,0.7286, '前往联盟金矿')
    wait_and_click_rel(0.5069,0.5086, '点击金矿')
    wait_and_click_rel(0.6512,0.6271, '点击采集')
    wait_and_click_rel(0.5494,0.5007, '点击加入')
    wait_and_click_rel(0.8457,0.3202, '创建部队')
    switch_formation_once()
    wait_and_click_rel(0.7477,0.4256, '选择第一部队')
    wait_and_click_rel(0.6566,0.7642, '行军')
    pyautogui.press('space')
    debug_log('返回城内')
    time.sleep(1)
    debug_log('联盟采集完成')


def switch_email(account):
    global formation_switched
    formation_switched = False
    debug_log("重置 formation_switched = False （切换账号后）")
    pyautogui.press('esc'); debug_log('打开菜单 (Esc)'); time.sleep(1)
    wait_and_click_rel(0.2469,0.8762, '设置')
    wait_and_click_rel(0.1381,0.6667, '账号与角色')
    wait_and_click_slow_rel(0.3549,0.3070, '点击账号')
    wait_and_click_slow_rel(0.4985,0.7154, '点击切换账号')
    wait_and_click_slow_rel(0.4977,0.6970, '点击登录其他账号')
    wait_and_click_slow_rel(0.5648,0.2688, '使用密码登录')
    wait_and_click_rel(0.4228,0.3333, '点击邮箱输入框')
    type_text(account['username'], '输入邮箱')
    wait_and_click_rel(0.4159,0.4177, '点击密码输入框')
    type_text(account['password'], '输入密码')
    wait_and_click_rel(0.5031,0.5995, '点击立即登录', delay=1); debug_log('已确认切换邮箱，等待加载...')
    wait_for_game_ready()
    windows = gw.getWindowsWithTitle('Rise of Kingdoms')
    if windows:
        windows[0].activate(); debug_log('激活游戏窗口(切换邮箱后)'); time.sleep(1)

def switch_formation_once():
    global formation_switched
    if not formation_switched:
        wait_and_click_rel(0.7500,0.3715, "更换编队至2")
        wait_and_click_rel(0.7500,0.3715, "更换编队至3")
        formation_switched = True
        debug_log("切换 formation_switched = True")

def switch_role():
    global formation_switched
    formation_switched = False
    debug_log("重置 formation_switched = False （切换角色后）")
    pyautogui.press('esc'); debug_log('打开菜单 (Esc)'); time.sleep(1)
    wait_and_click_rel(0.2469,0.8762, '设置')
    wait_and_click_rel(0.1381,0.6667, '账号与角色')
    debug_log('检测到需要切换角色，开始识别绿勾...')
    try:
        check_pos = pyautogui.locateOnScreen('template_image/green_check.png', confidence=0.85)
    except ImageNotFoundException:
        debug_log('⚠ 未检测到绿勾，跳过角色切换')
        return
    center = pyautogui.center(check_pos)
    x, _ = center
    debug_log(f"✅ 检测到绿勾勾在位置: {center}")
    if x < 500:
        debug_log('绿勾在左角色 → 点击右边')
        wait_and_click_rel(0.7096, 0.4733, '点击右边角色')

    else:
        debug_log('绿勾在右角色 → 点击左边')
        wait_and_click_rel(0.4068, 0.4602, '点击左边角色')

    time.sleep(2)
    wait_and_click_rel(0.5932, 0.6597, '确认切换')
    debug_log('已确认切换角色，等待加载...')
    time.sleep(10) ##average time wait the loading page
    wait_for_game_ready()
    windows = gw.getWindowsWithTitle('Rise of Kingdoms')
    if windows:
        windows[0].activate(); debug_log('激活游戏窗口(切换角色后)'); time.sleep(1)

def wait_for_game_ready():
    logger.info("等待游戏加载完成…（最长 40s）")
    start = time.time()
    template = 'template_image/ruby.png'
    conf = 0.85  # 从 0.75 降到 0.6

    while True:
        resume_event.wait()
        if time.time() - start > 40:
            logger.warning("等待超时 40s，继续执行后续操作")
            break

        try:
            pos = pyautogui.locateOnScreen(
                template,
                confidence=conf,
                grayscale=True
            )
        except ImageNotFoundException:
            pos = None

        if pos:
            x, y = pyautogui.center(pos)
            logger.info(f"检测到红宝石（模板匹配），中心约在 ({x},{y})，继续下一步")
            break
        else:
            # 可选：动态打印最高匹配分数，需要用 pyscreeze API 才能拿到 result.max()
            # logger.debug("未匹配到，继续等待…")
            time.sleep(0.5)

    time.sleep(1)
    logger.info("完成红宝石检测")
# 静态资源采集步骤映射
resource_steps = {
    'gold': [
        ('key','f'),
        ('click_rel',(0.7045,0.9117)),  # 搜索: f 之后第1步
        ('click_rel',(0.7029,0.7747)),  # 金矿
        ('click_rel',(0.6690,0.6337)),  # 采集
        ('click_rel',(0.8526,0.3228)),  # 创建部队
        ('click_rel',(0.6590,0.7708)),  # 行军
    ],
    'stone': [
        ('key','f'),
        ('click_rel',(0.6026,0.9078)),
        ('click_rel',(0.6026,0.7708)),
        ('click_rel',(0.6690,0.6337)),
        ('click_rel',(0.8526,0.3228)),
        ('click_rel',(0.6590,0.7708)),
    ],
    'wood': [
        ('key','f'),
        ('click_rel',(0.4946,0.9104)),
        ('click_rel',(0.4992,0.7747)),
        ('click_rel',(0.6690,0.6337)),
        ('click_rel',(0.8526,0.3228)),
        ('click_rel',(0.6590,0.7708)),
    ],
    'corn': [
        ('key','f'),
        ('click_rel',(0.3981,0.9065)),
        ('click_rel',(0.3951,0.7787)),
        ('click_rel',(0.6690,0.6337)),  
        ('click_rel',(0.8526,0.3228)),
        ('click_rel',(0.6590,0.7708)),
    ],
}

# —— 用相对坐标重写 troop_coords —— 
troop_coords = {
    1: (0.7477, 0.4229),
    2: (0.7485, 0.4730),
    3: (0.7485, 0.5270),
    4: (0.7477, 0.5744),
    5: (0.7477, 0.6219),
}

# —— 用下面的新实现替换原有的 gather 函数 —— #
# —— 修改 gather，实现统一处理 —— 
def gather(config, resource_steps):
    """
    动态分配 1–5 部队去采集普通资源：
    - 前四步：按 f、选资源、搜索、采集
    - 第五步：创建部队 → 立刻 switch_formation_once()
    - 第六步：选择部队
    - 第七步：行军出发
    """
    debug_log("开始普通资源采集")
    # 确保在主城界面
    pyautogui.press('space')
    debug_log("按下键盘: space")
    time.sleep(1)

    # 1) 读取并统计配置
    counts = {res: config.get(res, 0) for res in ['stone', 'wood', 'corn', 'gold']}
    # 2) 构建目标队列（最多 5 个）
    priority = ['stone', 'wood', 'corn', 'gold']
    targets = []
    for res in priority:
        targets += [res] * counts[res]
    targets = targets[:5]

    start_troop = 2
    TOTAL_TROOPS = 5

    # 3) 循环派遣每支部队
    for idx, res in enumerate(targets):
        troop_num = (start_troop - 1 + idx) % TOTAL_TROOPS + 1
        debug_log(f"分配部队{troop_num}采集 → {res}")

        steps = resource_steps[res]

        # —— 前四步：按键 & 四次点击 —— 
        for action, val in steps[:4]:
            if action == 'key':
                pyautogui.press(val)
                debug_log(f"按下键盘: {val}")
                time.sleep(0.5)
            else:
                rel_x, rel_y = val
                wait_and_click_rel(rel_x, rel_y, f"{res} 资源 点击")

        # —— 第五步：创建部队 —— 
        _, (rel_cx, rel_cy) = steps[4]
        wait_and_click_rel(rel_cx, rel_cy, "创建部队")

        # —— 切换编队（仅首支，且非联盟资源） —— 
        if idx == 0 and not config.get("GATHER_ALLIANCE_RES", False):
            switch_formation_once()
            debug_log("更换编队完成")

        # —— 第六步：选择对应部队 —— 
        rel_tx, rel_ty = troop_coords[troop_num]
        wait_and_click_rel(rel_tx, rel_ty, f"选择采集部队{troop_num}")

        # —— 第七步：行军出发 —— 
        _, (rel_mx, rel_my) = steps[5]
        wait_and_click_rel(rel_mx, rel_my, "行军")

        # 小休息，保证界面稳定
        time.sleep(1)

    debug_log("普通资源采集完成")

def load_accounts():
    """从 accounts.json 里加载账号列表"""
    try:
        with open('accounts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("找不到 accounts.json，脚本退出")
        sys.exit(1)

def run_cycle():
    resume_event.wait()
    debug_log('========== 新一轮循环开始 ==========' )
    # 读取配置和账号列表
    cfg = json.load(open('resource_config.json'))
    # 资源配置（排除 interval 和 initial_wait 字段
    resource_config = {k: v for k, v in cfg.items() if k in resource_steps}
    accounts = load_accounts()

    # 从 cfg 中取 launcher_path，找不到就回退到默认值
    launcher_path = cfg.get(
        'launcher_path',
        r"C:\Program Files (x86)\Rise of Kingdoms\launcher.exe"
    )

    # —— 如果没配置或路径不存在，记录日志并结束本次函数 —— #
    if not launcher_path or not os.path.isfile(launcher_path):
        logger.error(f"Launcher 路径未配置或文件不存在: {launcher_path!r}，请检查 resource_config.json")
        sys.exit(1)  # 结束 run_cycle，不再继续执行
        # 或者如果想直接退出脚本，用：sys.exit(1)

    # 启动并进入游戏
    resume_event.wait()
    subprocess.Popen([launcher_path], shell=False)
    logger.info(f'已启动 launcher: {launcher_path}')
    time.sleep(10)

    resume_event.wait()
    launcher_windows = gw.getWindowsWithTitle('Launcher')
    if launcher_windows:
        launcher_windows[0].moveTo(0,0); debug_log('移动 Launcher 窗口')
    time.sleep(3)

    resume_event.wait()
    if launcher_windows:
        w = launcher_windows[0]
        try:
            if w.isMinimized:
                w.restore()
        except Exception:
            pass
        try:
            w.moveTo(0, 0)
            debug_log("移动 Launcher 窗口到 (0,0)")
        except Exception:
            pass

        time.sleep(0.3)

        # ✅ 你刚刚测出来的启动按钮相对坐标
        rel_x, rel_y = 0.8679, 0.8244

        x = w.left + int(round(rel_x * w.width))
        y = w.top  + int(round(rel_y * w.height))
        rx, ry = randomize_pos(x, y, w.left, w.top, w.width, w.height)
        safe_move_and_click(rx, ry)
        debug_log(f"点击启动按钮 → rel=({rel_x:.4f}, {rel_y:.4f}) → ({rx}, {ry})")
    else:
        logger.error("❌ 未找到 Launcher 窗口，无法点击启动按钮")
    time.sleep(1)

    # —— 等待游戏窗口出现（但不激活），再检测红宝石 —— #
    start_win = None
    start_time = time.time()
    while time.time() - start_time < 40:
        resume_event.wait()
        wins = gw.getWindowsWithTitle('Rise of Kingdoms')
        if wins:
            start_win = wins[0]
            start_win.moveTo(0, 0)
            debug_log('检测到游戏窗口，已移动但未激活')
            break
        time.sleep(0.5)
    if not start_win:
        logger.warning('40s 内未检测到游戏窗口，跳过移动及检测')
    
    # —— 确认进入游戏（红宝石出现或超时） —— #
    wait_for_game_ready()

    # —— 进入游戏后，再激活窗口 —— #
    if start_win:
        start_win.activate()
        debug_log('激活游戏窗口')
        time.sleep(1)


            
    # 处理所有账号和角色
    total = len(accounts)
    for idx, account in enumerate(accounts):
        resume_event.wait()
        logger.info(f'▶ 处理账号 {idx+1}/{total}：{account["username"]}')

        # 切换账号：账号2/3 在这里收集一次
        resume_event.wait()
        if idx > 0:
            switch_email(account)

        resume_event.wait()
        if GLOBAL_VIP:
            daily_vip_collect()

        resume_event.wait()
        if cfg.get('COLLECT_ALLIANCE_RES', True):
            collect_alliance_resource()

        if cfg.get('GATHER_ALLIANCE_RES', True):
            send_alliance_gather()
        
        resume_event.wait()
        debug_log(f'账号 {account["username"]} 开始主角色采集')
        gather(resource_config, resource_steps)

        resume_event.wait()
        if cfg.get('DEBUG_CITY_COLLECT', True):
            collect_city_resources()

        resume_event.wait()
        if account.get('character', 0) == 1:
            resume_event.wait()
            switch_role()

            resume_event.wait()
            if GLOBAL_VIP:
                daily_vip_collect()
            resume_event.wait()
            if cfg.get('COLLECT_ALLIANCE_RES', True):
                collect_alliance_resource()

            if cfg.get('GATHER_ALLIANCE_RES', True):
                send_alliance_gather()
            debug_log(f'账号 {account["username"]} 第二角色开始采集')
            resume_event.wait()
            gather(resource_config, resource_steps)

            resume_event.wait()
            # —— 第二角色普通采集之后，再收一次城内资源 —— #
            if cfg.get('DEBUG_CITY_COLLECT', True):
                collect_city_resources()    
                
        logger.info(f'✅ 账号 {account["username"]} 完成')

    # 切换回初始账号
    if len(accounts) > 1:
        resume_event.wait()
        debug_log(f"开始切换回初始账号: {accounts[0]['username']}")
        switch_email(accounts[0])
        debug_log(f"已切换回初始账号: {accounts[0]['username']}")

    debug_log('========== 本次循环完成 ==========' )

def start_script():
    first_run = True
    while True:
        resume_event.wait()
        cfg = json.load(open('resource_config.json', encoding='utf-8'))
        global GLOBAL_VIP, GLOBAL_ALLIANCE, interval_hours
        GLOBAL_VIP      = cfg.get('GLOBAL_VIP', True)
        GLOBAL_ALLIANCE = cfg.get('GLOBAL_ALLIANCE', True)
        initial_wait    = cfg.get('initial_wait_hours', 0)
        interval_hours  = cfg.get('interval_hours',   3.5)

        if first_run and initial_wait > 0:
            debug_log(f"首次等待 {initial_wait} 小时")  
            show_countdown(int(initial_wait * 3600))

        run_cycle()

        for title in ['Rise of Kingdoms']:
            for w in gw.getWindowsWithTitle(title):
                w.close(); debug_log(f"关闭窗口: {title}")
        # 关闭 launcher
        subprocess.run(['taskkill','/IM','launcher.exe','/F'], stdout=subprocess.DEVNULL)
        debug_log('关闭 Launcher')

        # 后续循环都按 interval_hours 等待
        # 首次等待逻辑只执行一次，之后设为 False
        first_run = False
        debug_log(f"下一轮间隔 {interval_hours} 小时")
        show_countdown(int(interval_hours * 3600))


# —— GUI 配置窗口 —— #
def show_config_gui():
    global config_win, vip_var, show_log_var, initial_wait_var, interval_var, res_vars
    # 用 Toplevel 弹一个配置框，独立于 main_win
    config_win = tk.Toplevel()
    config_win.title("脚本参数设置")
    config_win.geometry("350x300")
    config_win.grab_set()

    proceed_flag = {'ok': False}

    # 1. 先读旧配置（防止 NameError）
    try:
        cfg = json.load(open('resource_config.json', encoding='utf-8'))
    except FileNotFoundError:
        cfg = {}

    frm = ttk.Frame(config_win, padding=20)
    frm.pack(expand=True, fill='both')

    # 3. 在这里用 cfg 和 frm 来生成控件
    city_collect_var = tk.BooleanVar(value=cfg.get('DEBUG_CITY_COLLECT', True))
    vip_var       = tk.BooleanVar(value=cfg.get('GLOBAL_VIP', True))
    collect_res_var = tk.BooleanVar(value=cfg.get('COLLECT_ALLIANCE_RES', True))
    gather_res_var  = tk.BooleanVar(value=cfg.get('GATHER_ALLIANCE_RES', True))
    show_log_var  = tk.BooleanVar(value=cfg.get('show_log', True))
    initial_wait_var = tk.DoubleVar(value=cfg.get('initial_wait_hours', 0))
    interval_var = tk.DoubleVar(value=cfg.get('interval_hours', 3.5))


    ttk.Checkbutton(frm, text="每日 VIP 签到",     variable=vip_var).grid(column=0, row=0, sticky='w')
    ttk.Checkbutton(frm, text="收集联盟资源", variable=collect_res_var).grid(column=0, row=1, sticky='w')
    ttk.Checkbutton(frm, text="进行联盟采集", variable=gather_res_var).grid(column=1, row=1, sticky='w')
    ttk.Checkbutton(frm, text="城内资源采集 (Debug)", variable=city_collect_var).grid(column=0, row=2, columnspan=2, sticky='w')
    ttk.Checkbutton(frm, text="启动后显示日志面板", variable=show_log_var).grid(column=0, row=3, columnspan=2, sticky='w')
    
    ttk.Label(frm, text="首次等待(小时):").grid(column=0,row=4,sticky='e')
    ttk.Spinbox(frm, from_=0, to=24, increment=0.5, textvariable=initial_wait_var, width=5).grid(column=1,row=4)
    ttk.Label(frm, text="循环间隔(小时):").grid(column=0,row=5,sticky='e')
    ttk.Spinbox(frm, from_=0.5, to=24, increment=0.5, textvariable=interval_var, width=5).grid(column=1,row=5)

    # 资源次数
    resources = ['gold','wood','stone','corn']
    res_vars = {}
    for i, res in enumerate(resources, start=6):
        ttk.Label(frm, text=f"{res} 次数").grid(column=0, row=i, sticky='e')
        v = tk.IntVar(value=cfg.get(res, 1))
        res_vars[res] = v
        ttk.Spinbox(frm, from_=0, to=10, increment=1, textvariable=v, width=5).grid(column=1, row=i)
    
    # 按钮回调：保存并退出
    def on_ok():
    # 1) 先读回旧配置
        try:
            with open('resource_config.json', 'r', encoding='utf-8') as f:
                old_cfg = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            old_cfg = {}

        # 2) 把要更新的字段覆盖到 old_cfg
        old_cfg['DEBUG_CITY_COLLECT']    = city_collect_var.get()
        old_cfg['GLOBAL_VIP']            = vip_var.get()
        old_cfg['COLLECT_ALLIANCE_RES']  = collect_res_var.get()
        old_cfg['GATHER_ALLIANCE_RES']   = gather_res_var.get()
        old_cfg['show_log']              = show_log_var.get()
        old_cfg['initial_wait_hours']    = initial_wait_var.get()
        old_cfg['interval_hours']        = interval_var.get()
        for k, v in res_vars.items():
            old_cfg[k] = v.get()

        # 3) 将合并后的整个字典写回文件
        with open('resource_config.json', 'w', encoding='utf-8') as f:
            json.dump(old_cfg, f, indent=2, ensure_ascii=False)

        proceed_flag['ok'] = True
        config_win.destroy()

    ttk.Button(frm, text="启动", command=on_ok).grid(column=0,row=10,columnspan=2,pady=10)
    config_win.wait_window()

    if not proceed_flag['ok']:
        sys.exit(0)  # 用户点击叉号退出

def setup_main_gui():
    main_win.title("ROK 脚本控制台")
    main_win.geometry("600x500")

    chk = ttk.Checkbutton(main_win, text="显示日志", variable=show_log_var, command=lambda: log_frame.pack(fill='both',expand=True) if show_log_var.get() else log_frame.pack_forget())
    chk.pack(anchor='nw',padx=5,pady=5)

    global log_frame
    log_frame = ttk.Frame(main_win)
    text_area = scrolledtext.ScrolledText(log_frame, state='disabled', wrap='word')
    text_area.pack(fill='both',expand=True)
    if show_log_var.get(): log_frame.pack(fill='both',expand=True)

    # 编辑参数按钮
    def on_edit():
        resume_event.clear()
        logger.info("暂停执行，打开参数设置…")
        show_config_gui()
        resume_event.set()
        logger.info("继续执行")

    ttk.Button(main_win, text="编辑参数", command=on_edit).pack(anchor='ne',padx=5,pady=5)

    gui_h = GuiHandler(text_area)
    gui_h.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(gui_h)

    threading.Thread(target=start_script, daemon=True).start()



if __name__ == "__main__":
    main_win = tk.Tk()
    main_win.withdraw()
    # 1) 弹出配置对话框（它是一个 Toplevel，带 grab_set，主窗口此时在后台）
    show_config_gui()
    # 2) 用户点了“启动”以后，配置窗口销毁，回到这里
    #    这时主窗口已经可见，无需 deiconify
    main_win.deiconify()
    setup_main_gui()
    main_win.mainloop()