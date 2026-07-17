import customtkinter as ctk
import threading
from pynput import keyboard
import pyautogui
from typing import Dict, Any
from autosell_v4 import run_auto_sell

# 1. 初始化设置
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.geometry("580x840")  # 📐
app.title("自动售卖 2.0 YBT")

# 全局变量库
config_data: Dict[str, Any] = {
    'start_key': 'f4',
    'stop_key': 'f12'
}
current_focus = "A"
is_grabbing = False  # 🛡️ 核心新增：雷达安全锁，默认为 False (关闭状态)


# ==================== 🛠️ 核心后端逻辑 ====================

# 📡 【雷达函数】按键盘 '左alt' 键自动抓取坐标
def on_press(key):
    global current_focus, is_grabbing
    try:
        # 🛡️ 只有当 is_grabbing 为 True 时，按 左alt 键才生效！
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r) and is_grabbing:
            x, y = pyautogui.position()

            if current_focus == "A":
                a_x_input.delete(0, "end")
                a_x_input.insert(0, str(x))
                a_y_input.delete(0, "end")
                a_y_input.insert(0, str(y))
                status_label.configure(text="🎯 已抓取位置 A！请把鼠标移到位置 B，再按 'alt' 键", text_color="#3498db")
                current_focus = "B"
            elif current_focus == "B":
                b_x_input.delete(0, "end")
                b_x_input.insert(0, str(x))
                b_y_input.delete(0, "end")
                b_y_input.insert(0, str(y))
                status_label.configure(text="🎯 已抓取位置 B！请把鼠标移到位置 C，再按 'alt' 键", text_color="#3498db")
                current_focus = "C"
            elif current_focus == "C":
                c_x_input.delete(0, "end")
                c_x_input.insert(0, str(x))
                c_y_input.delete(0, "end")
                c_y_input.insert(0, str(y))

                # 🤖 智能防呆：抓完三个后，自动关闭雷达保险！
                status_label.configure(text="🟢 三组坐标已抓取", text_color="#2ecc71")
                current_focus = "A"
                is_grabbing = False
                toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9")  # 按钮变回蓝色
    except AttributeError:
        pass


# 启动键盘监听雷达
def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


threading.Thread(target=start_keyboard_listener, daemon=True).start()


# 🔌 触发事件：雷达开关按钮
def toggle_radar():
    global is_grabbing
    is_grabbing = not is_grabbing  # 状态反转

    if is_grabbing:
        toggle_radar_btn.configure(text="🛑 正在抓取中... (点击关闭雷达)", fg_color="#e74c3c", hover_color="#c0392b")
        status_label.configure(text=f"⏳ 雷达已开启！请将鼠标移到位置 {current_focus}，按 'alt' 键", text_color="#f39c12")
    else:
        toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9", hover_color="#2471a3")
        status_label.configure(text="⏸️ 雷达已关闭，现在按 alt 键不会影响坐标。", text_color="#7f8c8d")


# 🔌 触发事件 1：重置坐标键
def reset_coordinates():
    global current_focus, is_grabbing
    a_x_input.delete(0, "end")
    a_y_input.delete(0, "end")
    b_x_input.delete(0, "end")
    b_y_input.delete(0, "end")
    c_x_input.delete(0, "end")
    c_y_input.delete(0, "end")

    current_focus = "A"
    is_grabbing = False  # 重置时默认关闭雷达
    toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9")

    status_label.configure(text="🔄 坐标已清空！请点击上方【开启雷达】重新抓取", text_color="#f39c12")
    bind_button.configure(state="normal")
    confirm_program_button.configure(state="disabled")
    start_button.configure(state="disabled")


# 🔌 触发事件 2：1. 确认并绑定上述坐标
def bind_coordinates():
    try:
        config_data['a_x'] = int(a_x_input.get())
        config_data['a_y'] = int(a_y_input.get())
        config_data['b_x'] = int(b_x_input.get())
        config_data['b_y'] = int(b_y_input.get())
        config_data['c_x'] = int(c_x_input.get())
        config_data['c_y'] = int(c_y_input.get())
        config_data['delay'] = float(delay_input.get())

        sk = start_key_input.get().strip().lower()
        tk = stop_key_input.get().strip().lower()

        if sk == tk:
            status_label.configure(text="🔴 错误：启动按键和关闭按键不能设为同一个！", text_color="#e74c3c")
            return
        if sk == 'esc' or tk == 'esc':
            status_label.configure(text="🔴 警告：不能设置系统冲突按键 (如 ESC)！请重新修改！", text_color="#e74c3c")
            return

        config_data['start_key'] = sk
        config_data['stop_key'] = tk

        status_label.configure(text="🟢 坐标及快捷键获取成功！请点击下一步确认程序！", text_color="#2ecc71")
        confirm_program_button.configure(state="normal")

    except ValueError:
        status_label.configure(text="🔴 错误：请确保所有坐标和延迟都已成功填入数字！", text_color="#e74c3c")


# 🔌 触发事件 3：2. 确认锁定程序
def confirm_program():
    status_label.configure(
        text=f"坐标已锁定[ 启动:{config_data['start_key'].upper()} | 关闭:{config_data['stop_key'].upper()} ] ",
        text_color="#2ecc71")
    start_button.configure(state="normal")


# 🔌 触发事件 4：3. 确认启动程序（最终开火）
def start_final_program():
    status_label.configure(
        text=f"请按你设置的热键运行",
        text_color="#2ecc71"
    )

    def start_hotkey_loop():
        sk = config_data.get('start_key', 'f4').lower()
        tk = config_data.get('stop_key', 'f12').lower()

        print(f" 键盘热键捕获已就绪：按 [{sk.upper()}] 触发一次连点，按 [{tk.upper()}] 强制退出")

        def on_trigger_press(key):
            try:
                if hasattr(key, 'name') and key.name == sk:
                    run_auto_sell(config_data)
                elif hasattr(key, 'name') and key.name == tk:
                    print("检测到关闭热键，退出")
                    return False
            except Exception as e:
                pass

        with keyboard.Listener(on_press=on_trigger_press) as l:
            l.join()

    threading.Thread(target=start_hotkey_loop, daemon=True).start()


# ==================== 🎨 UI 界面排版 ====================

title_label = ctk.CTkLabel(app, text="⚙️ 自动售卖 2.0 YBT", font=("Arial", 20, "bold"))
title_label.pack(pady=20)

# --- ⌨️ 快捷键自定义设置区 ---
key_frame = ctk.CTkFrame(app)
key_frame.pack(pady=10, padx=30, fill="x")
ctk.CTkLabel(key_frame, text="⌨️ 自定义热键:", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=10, pady=10,
                                                                                sticky="w")
ctk.CTkLabel(key_frame, text="启动键:").grid(row=0, column=1, padx=5)
start_key_input = ctk.CTkEntry(key_frame, width=60)
start_key_input.insert(0, "F4")
start_key_input.grid(row=0, column=2, padx=5)
ctk.CTkLabel(key_frame, text="关闭键:").grid(row=0, column=3, padx=5)
stop_key_input = ctk.CTkEntry(key_frame, width=60)
stop_key_input.insert(0, "F12")
stop_key_input.grid(row=0, column=4, padx=5)
warn_label = ctk.CTkLabel(key_frame, text="⚠️ 警告：请勿使用ESC等可能导致系统冲突的按键", text_color="#e74c3c",
                          font=("Arial", 11))
warn_label.grid(row=1, column=0, columnspan=5, padx=10, pady=5)

# --- 📍 坐标采集区 ---
tip_label = ctk.CTkLabel(app, text="💡 提示：请先点击下方【开启雷达】，然后按 '左alt' 键抓取坐标", text_color="#7f8c8d",
                         font=("Arial", 12))
tip_label.pack(pady=5)

# 🛡️ 核心新增：雷达开关按钮
toggle_radar_btn = ctk.CTkButton(app, text="📡 开启坐标雷达", command=toggle_radar, fg_color="#2980b9",
                                 hover_color="#2471a3")
toggle_radar_btn.pack(pady=5)


def create_coord_row(label_text, placeholder_x, placeholder_y):
    frame = ctk.CTkFrame(app)
    frame.pack(pady=8, padx=30, fill="x")
    lbl = ctk.CTkLabel(frame, text=label_text, font=("Arial", 14, "bold"), width=150, anchor="w")
    lbl.pack(side="left", padx=15, pady=8)
    x_in = ctk.CTkEntry(frame, width=100, placeholder_text=placeholder_x)
    x_in.pack(side="left", padx=10)
    y_in = ctk.CTkEntry(frame, width=100, placeholder_text=placeholder_y)
    y_in.pack(side="left", padx=10)
    return x_in, y_in


a_x_input, a_y_input = create_coord_row("位置 A (选价格框) ->", "X 坐标", "Y 坐标")
b_x_input, b_y_input = create_coord_row("位置 B (修改价格) ->", "X 坐标", "Y 坐标")
c_x_input, c_y_input = create_coord_row("位置 C (确定上架) ->", "X 坐标", "Y 坐标")

# --- ⏱️ enter服务器响应价格设置区一般默认0.35即可 ---
delay_frame = ctk.CTkFrame(app)
delay_frame.pack(pady=8, padx=30, fill="x")
ctk.CTkLabel(delay_frame, text="⏱️ 默认0.35 (秒):", font=("Arial", 13, "bold"), width=150, anchor="w").pack(
    side="left", padx=15, pady=8)
delay_input = ctk.CTkEntry(delay_frame, width=120, placeholder_text="例如: 0.08")
delay_input.pack(side="left", padx=10)

# ==================== 🚥 状态和多步确认按钮区 ====================

status_label = ctk.CTkLabel(app, text="⏸️ 准备就绪。请先开启雷达以抓取坐标", font=("Arial", 13, "bold"))
status_label.pack(pady=20)

reset_button = ctk.CTkButton(app, text="🔄 重置/清空所有当前坐标", command=reset_coordinates, fg_color="#d35400",
                             hover_color="#b33921")
reset_button.pack(pady=5, fill="x", padx=60)

bind_button = ctk.CTkButton(app, text="🔗 1. 确认并绑定上述参数", command=bind_coordinates, fg_color="#34495e",
                            hover_color="#2c3e50")
bind_button.pack(pady=5, fill="x", padx=60)

confirm_program_button = ctk.CTkButton(app, text="🔒 2. 确认锁定程序坐标", command=confirm_program, fg_color="#16a085",
                                       hover_color="#118168", state="disabled")
confirm_program_button.pack(pady=5, fill="x", padx=60)

start_button = ctk.CTkButton(app, text="🚀 3. 确认启动程序 (运行)", command=start_final_program,
                             font=("Arial", 14, "bold"), height=40, state="disabled")
start_button.pack(pady=15, fill="x", padx=60)

app.mainloop()