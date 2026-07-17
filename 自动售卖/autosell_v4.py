import pyautogui
import time
import random

# ================= 1. 时间调节面板保持原样 (单位：秒) =================
TIME_STOP_BEFORE_CLICK = 0.1  # 后两次点击移过去后“顿一会”的时间
TIME_AFTER_CLICK1 = 0.15  # 点击价格框后的等待时间
TIME_AFTER_BACK = 0.10  # 按完退格键后的等待时间
TIME_SERVER_WAIT = 0.35  # 等服务器与游戏响应的时间
TIME_MOVE_2_TO_3 = 0.1  # 第二点击到第三点击之间的间隔时间


def click_with_offset(x, y, stop_time=0.1):
    """人类平滑移动和微小像素偏移点击（保持你的完美核心逻辑）"""
    target_x = x + random.randint(-2, 2)
    target_y = y + random.randint(-2, 2)
    pyautogui.moveTo(target_x, target_y, duration=0.15)
    time.sleep(stop_time)
    pyautogui.click()


# 🎯 核心改造：把原本的动作变成一个可以接收 UI 数据的函数！
def run_auto_sell(config):
    print("\n[核心引擎激活] 收到UI传输的锁死参数，开始按序轰炸...")

    # 🔌 从 UI 传过来的大本子（字典）里，钓出动态抓取的自定义坐标和延迟！
    pos_1_x, pos_1_y = config['a_x'], config['a_y']
    pos_2_x, pos_2_y = config['b_x'], config['b_y']
    pos_3_x, pos_3_y = config['c_x'], config['c_y']

    # 动态延迟也可以从 UI 读，如果 UI 没填就用顶部面板默认的
    ui_delay = config.get('delay', TIME_SERVER_WAIT)

    try:
        # 1. 点击价格框（位置 A）
        click_with_offset(pos_1_x, pos_1_y)
        time.sleep(0.08)
        click_with_offset(pos_1_x, pos_1_y)
        time.sleep(TIME_AFTER_CLICK1)

        # 2. Back一次
        pyautogui.press('right')
        time.sleep(0.05)
        pyautogui.press('backspace')
        time.sleep(TIME_AFTER_BACK)

        # 3. 回车
        pyautogui.press('enter')
        print(f"[游戏内核] 已敲击回车，等待响应...")
        time.sleep(ui_delay)  # ⌛ 使用你 UI 填写的动态延迟！

        # 4. 点击第二位置（位置 B）
        click_with_offset(pos_2_x, pos_2_y, stop_time=TIME_STOP_BEFORE_CLICK)
        time.sleep(TIME_MOVE_2_TO_3)

        # 5. 点击第三位置（位置 C）
        click_with_offset(pos_3_x, pos_3_y, stop_time=TIME_STOP_BEFORE_CLICK)

        print("[自动化成功] 精准连点已按序完成！")
    except Exception as e:
        print(f"[错误提示] 执行异常: {e}")