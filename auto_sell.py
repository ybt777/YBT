import pyautogui
import time
import random
from pynput import keyboard

# ================= 1. 你的精准坐标配置 =================
POS_1_X, POS_1_Y = 1807, 937
POS_2_X, POS_2_Y = 1166, 907
POS_3_X, POS_3_Y = 1765, 1077

# ================= 2. 【时间调节面板】(单位：秒) =================
# 你可以根据实际体验，随时修改下面这些数字（支持小数，如 0.5）
TIME_AFTER_CLICK1 = 0.3  # 第一次点击价格框后的等待时间
TIME_AFTER_BACK = 0.2  # 按完退格键（Backspace）后的等待时间
TIME_SERVER_WAIT = 1.1  # 【核心】按完第一次回车，等待服务器弹出最高性价比价格的时间
TIME_AFTER_ENTER2 = 0.5  # 按完第一次回车，确认价格后的等待时间
TIME_BETWEEN_2_3 = 0.5  # 【核心】第二次点击到第三次点击之间的漫长等待时间


# =============================================================

def click_with_offset(x, y):
    """加入微小像素偏移点击，防封"""
    target_x = x + random.randint(-2, 2)
    target_y = y + random.randint(-2, 2)
    pyautogui.click(target_x, target_y)


def run_action():
    print("\n[自动化启动] 收到指令，正在按照您的精细时间表执行动作...")
    try:
        # ---- 步骤 1：第一次点击价格框 ----
        click_with_offset(POS_1_X, POS_1_Y)
        time.sleep(TIME_AFTER_CLICK1)

        # ---- 步骤 2：按下退格键 ----
        pyautogui.press('backspace')
        time.sleep(TIME_AFTER_BACK)

        # ---- 步骤 3：按下第一次回车（触发性价比价格） ----
        pyautogui.press('enter')
        print(f"[系统提示] 已发送改价请求，等服务器响应 {TIME_SERVER_WAIT} 秒...")
        time.sleep(TIME_SERVER_WAIT)  # 这里会老老实实等 2 秒左右

        # ---- 步骤 4：按下第二次回车（确认这个价格） ----
        pyautogui.press('enter')
        time.sleep(TIME_AFTER_ENTER2)

        # ---- 步骤 5：去第 2 个位置点击 ----
        click_with_offset(POS_2_X, POS_2_Y)
        print(f"[系统提示] 第二次点击完成，正在拉长间隔，等待 {TIME_BETWEEN_2_3} 秒...")
        time.sleep(TIME_BETWEEN_2_3)  # 这里会拉长第一次到第二次（完成步骤2后到步骤3）的间隔

        # ---- 步骤 6：去第 3 个位置点击 ----
        click_with_offset(POS_3_X, POS_3_Y)

        print("[自动化成功] 已执行完毕！")
    except Exception as e:
        print(f"[错误提示] 执行异常: {e}")


def on_press(key):
    try:
        if key == keyboard.Key.f4:
            run_action()
        elif key == keyboard.Key.esc:
            print("\n连点程序已安全退出。")
            return False
    except Exception as e:
        print(f"监听异常: {e}")


print("==========================================")
print(" 连点主程序")
print(" 快捷键：【 F4 】开始 / 【 Esc 】退出  上方第58行修改")
print(" 提示：如果觉得太快或太慢，随时修改代码上方的【时间调节面板】")
print("==========================================")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()