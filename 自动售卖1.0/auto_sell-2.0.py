import pyautogui
import time
import random
from pynput import keyboard

# ================= 1. 你的精准坐标配置 =================
POS_1_X, POS_1_Y = 1807, 937  # 第一位置（价格框）
POS_2_X, POS_2_Y = 1166, 907  # 第二位置
POS_3_X, POS_3_Y = 1765, 1077  # 第三位置

# ================= 2. 【时间调节面板】(单位：秒) =================
# =============================================================
#           ⚡ 2. 【核心操作链条与时间调节面板】 ⚡
# =============================================================

# --- 【移动到位置后，停顿多久再点】 ---
TIME_STOP_BEFORE_CLICK = 0.1  # 后两次点击移过去后“顿一会”的时间

# --- 【各个步骤的延迟】 ---
TIME_AFTER_CLICK1 = 0.20  # 点击价格框后的等待时间
TIME_AFTER_BACK = 0.15   # 按完退格键后的等待时间
TIME_SERVER_WAIT = 0.55   # 等服务器与游戏响应的时间
TIME_MOVE_2_TO_3 = 0.1  # 第二点击到第三点击之间的间隔时间  为第二点击后 隔0.2s 执行第三点击移动+点击
# =============================================================

def click_with_offset(x, y, stop_time=0.1):  # 👈 核心：小括号里必须把 stop_time 加上！
    """加入人类平滑移动和微小像素偏移点击"""
    target_x = x + random.randint(-2, 2)
    target_y = y + random.randint(-2, 2)

    # 鼠标平滑移过去
    pyautogui.moveTo(target_x, target_y, duration=0.15)

    # 顿一会
    time.sleep(stop_time)

    # 最终点下去
    pyautogui.click()


def run_action():
    print("\n[自动化启动] 正在按照您的真实操作顺序执行...")
    try:
        # 1. 点击价格框
        click_with_offset(POS_1_X, POS_1_Y)
        time.sleep(0.08)
        click_with_offset(POS_1_X, POS_1_Y)
        time.sleep(TIME_AFTER_CLICK1)

        # 2. Back一次
        pyautogui.press('right')  # ➡️ 先解除全选高亮
        time.sleep(0.05)  # ⌛ 固定的微小物理延迟，不需要经常改它！
        pyautogui.press('backspace')  # ⬅️ 严格只删一位
        time.sleep(TIME_AFTER_BACK)  # ⌛ 这里去读你顶部面板的变量

        # 3. 回车（触发性价比路线）
        pyautogui.press('enter')
        print(f"[系统提示] 已敲击回车，等服务器响应 {TIME_SERVER_WAIT} 秒...")
        time.sleep(TIME_SERVER_WAIT)  #  等服务器

        # 4. 点击第二坐标位置
        click_with_offset(POS_2_X, POS_2_Y, stop_time=TIME_STOP_BEFORE_CLICK)
        print(f"[系统提示] 第二次点击完成，正在拉长间隔，等待 {TIME_MOVE_2_TO_3} 秒...")
        time.sleep(TIME_MOVE_2_TO_3)

        # 5. 点击第三坐标位置
        click_with_offset(POS_3_X, POS_3_Y, stop_time=TIME_STOP_BEFORE_CLICK)

        print("[自动化成功] 精准连点已按序完成！")
    except Exception as e:
        print(f"[错误提示] 执行异常: {e}")


def on_press(key):
    try:
        if key == keyboard.Key.f4:
            run_action()
        elif key == keyboard.Key.alt:
            print("\n连点程序已退出。")
            return False
    except Exception as e:
        print(f"监听异常: {e}")


print("==========================================")
print(" ！")
print(" 快捷键：【 f4 】开始 / 【alt 】退出")
print("==========================================")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()