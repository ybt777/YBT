import pyautogui
import keyboard

# 计数器，记录当前抓取到第几个点了
click_count = 0

print("==========================================")
print(" 4点坐标连续抓取器 已启动！")
print(" 【使用方法】：")
print(" 1. 把鼠标移到【第1个位置】，按 Ctrl ")
print(" 2. 把鼠标移到【第2个位置】，按 Ctrl ")
print(" 3. 依此类推，把4个位置都按一遍。")
print(" 4. 全部抓完后，在游戏里按 Esc 键退出本程序。")
print("==========================================")


def catch_position():
    global click_count
    click_count += 1

    # 获取坐标
    x, y = pyautogui.position()

    # 打印结果，方便你直接复制
    print(f"[点第 {click_count} 次] 坐标为 -> X = {x}, Y = {y}")


# 监听组合键
keyboard.add_hotkey('ctrl', catch_position)

# 监听退出
keyboard.wait('esc')
print("\n探测程序已安全退出。")