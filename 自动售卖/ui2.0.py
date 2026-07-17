import customtkinter as ctk
import threading
from pynput import keyboard
import pyautogui
import json
import os
from typing import Dict, Any
from autosell_v4 import run_auto_sell

# ==================== 1. 初始化设置 ====================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.geometry("580x920")  # 高度增加以容纳新按钮
app.title("自动售卖 2.0 YBT")

# ==================== 2. 全局变量 ====================
config_data: Dict[str, Any] = {
    'start_key': 'f4',
    'stop_key': 'f12'
}
current_focus = "A"
is_grabbing = False

# ==================== 3. 键位映射表（下拉菜单用） ====================
KEY_DISPLAY_MAP = {
    'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4', 'F5': 'f5',
    'F6': 'f6', 'F7': 'f7', 'F8': 'f8', 'F9': 'f9', 'F10': 'f10',
    'F11': 'f11', 'F12': 'f12',
    '空格 (Space)': 'space',
    '回车 (Enter)': 'enter',
    '退格 (Backspace)': 'backspace',
    'Tab': 'tab',
    'Shift': 'shift',
    'Ctrl': 'ctrl',
    'Alt': 'alt',
    '↑ 上': 'up',
    '↓ 下': 'down',
    '← 左': 'left',
    '→ 右': 'right',
    'ESC (不推荐)': 'esc'
}
KEY_TO_DISPLAY = {v: k for k, v in KEY_DISPLAY_MAP.items()}
display_keys = list(KEY_DISPLAY_MAP.keys())

# ==================== 4. 坐标雷达（按 Alt 抓取） ====================
def on_press(key):
    global current_focus, is_grabbing
    try:
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
                status_label.configure(text="🟢 三组坐标已抓取", text_color="#2ecc71")
                current_focus = "A"
                is_grabbing = False
                toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9")
    except AttributeError:
        pass

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

threading.Thread(target=start_keyboard_listener, daemon=True).start()

# ==================== 5. UI 交互函数 ====================
def toggle_radar():
    global is_grabbing
    is_grabbing = not is_grabbing
    if is_grabbing:
        toggle_radar_btn.configure(text="🛑 正在抓取中... (点击关闭雷达)", fg_color="#e74c3c", hover_color="#c0392b")
        status_label.configure(text=f"⏳ 雷达已开启！请将鼠标移到位置 {current_focus}，按 'alt' 键", text_color="#f39c12")
    else:
        toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9", hover_color="#2471a3")
        status_label.configure(text="⏸️ 雷达已关闭，现在按 alt 键不会影响坐标。", text_color="#7f8c8d")

def reset_coordinates():
    global current_focus, is_grabbing
    a_x_input.delete(0, "end")
    a_y_input.delete(0, "end")
    b_x_input.delete(0, "end")
    b_y_input.delete(0, "end")
    c_x_input.delete(0, "end")
    c_y_input.delete(0, "end")
    current_focus = "A"
    is_grabbing = False
    toggle_radar_btn.configure(text="📡 开启坐标雷达", fg_color="#2980b9")
    status_label.configure(text="🔄 坐标已清空！请点击上方【开启雷达】重新抓取", text_color="#f39c12")
    bind_button.configure(state="normal")
    confirm_program_button.configure(state="disabled")
    start_button.configure(state="disabled")

def bind_coordinates():
    try:
        config_data['a_x'] = int(a_x_input.get())
        config_data['a_y'] = int(a_y_input.get())
        config_data['b_x'] = int(b_x_input.get())
        config_data['b_y'] = int(b_y_input.get())
        config_data['c_x'] = int(c_x_input.get())
        config_data['c_y'] = int(c_y_input.get())
        config_data['delay'] = float(delay_input.get())

        # 从下拉菜单获取键位
        sk_display = start_key_var.get()
        tk_display = stop_key_var.get()
        sk = KEY_DISPLAY_MAP.get(sk_display, sk_display.lower())
        tk = KEY_DISPLAY_MAP.get(tk_display, tk_display.lower())

        if sk == tk:
            status_label.configure(text="🔴 错误：启动按键和关闭按键不能设为同一个！", text_color="#e74c3c")
            return False
        if sk == 'esc' or tk == 'esc':
            status_label.configure(text="🔴 警告：不能设置系统冲突按键 (如 ESC)！请重新修改！", text_color="#e74c3c")
            return False

        config_data['start_key'] = sk
        config_data['stop_key'] = tk

        status_label.configure(text="🟢 坐标及快捷键获取成功！请点击下一步确认程序！", text_color="#2ecc71")
        confirm_program_button.configure(state="normal")
        return True
    except ValueError:
        status_label.configure(text="🔴 错误：请确保所有坐标和延迟都已成功填入数字！", text_color="#e74c3c")
        return False

def confirm_program():
    status_label.configure(
        text=f"坐标已锁定[ 启动:{config_data['start_key'].upper()} | 关闭:{config_data['stop_key'].upper()} ] ",
        text_color="#2ecc71")
    start_button.configure(state="normal")

def start_final_program():
    status_label.configure(text="请按你设置的热键运行", text_color="#2ecc71")
    def start_hotkey_loop():
        sk = config_data.get('start_key', 'f4').lower()
        tk = config_data.get('stop_key', 'f12').lower()
        print(f"键盘热键捕获已就绪：按 [{sk.upper()}] 触发一次连点，按 [{tk.upper()}] 强制退出")
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

# ==================== 6. 方案保存与加载 ====================
CONFIG_FILE = "config.json"

def save_config():
    try:
        data = {
            'a_x': a_x_input.get(),
            'a_y': a_y_input.get(),
            'b_x': b_x_input.get(),
            'b_y': b_y_input.get(),
            'c_x': c_x_input.get(),
            'c_y': c_y_input.get(),
            'delay': delay_input.get(),
            'start_key': KEY_DISPLAY_MAP.get(start_key_var.get(), start_key_var.get().lower()),
            'stop_key': KEY_DISPLAY_MAP.get(stop_key_var.get(), stop_key_var.get().lower())
        }
        if any(v == '' for v in data.values()):
            status_label.configure(text="🔴 保存失败：请确保所有输入框都已填写！", text_color="#e74c3c")
            return
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        status_label.configure(text=f"✅ 方案已保存到 {CONFIG_FILE}", text_color="#2ecc71")
    except Exception as e:
        status_label.configure(text=f"🔴 保存失败：{e}", text_color="#e74c3c")

def load_config(auto=False):
    if not os.path.exists(CONFIG_FILE):
        if auto:
            return
        status_label.configure(text="⚠️ 未找到配置文件，请手动配置", text_color="#f39c12")
        return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 填入坐标
        a_x_input.delete(0, "end"); a_x_input.insert(0, data.get('a_x', ''))
        a_y_input.delete(0, "end"); a_y_input.insert(0, data.get('a_y', ''))
        b_x_input.delete(0, "end"); b_x_input.insert(0, data.get('b_x', ''))
        b_y_input.delete(0, "end"); b_y_input.insert(0, data.get('b_y', ''))
        c_x_input.delete(0, "end"); c_x_input.insert(0, data.get('c_x', ''))
        c_y_input.delete(0, "end"); c_y_input.insert(0, data.get('c_y', ''))
        delay_input.delete(0, "end"); delay_input.insert(0, data.get('delay', '0.35'))

        # 恢复快捷键下拉菜单
        start_key_display = KEY_TO_DISPLAY.get(data.get('start_key', 'f4'), 'F4')
        stop_key_display = KEY_TO_DISPLAY.get(data.get('stop_key', 'f12'), 'F12')
        start_key_var.set(start_key_display)
        stop_key_var.set(stop_key_display)

        if bind_coordinates():
            confirm_program()
            status_label.configure(text=f"🔄 已自动加载方案 (启动键：{config_data['start_key'].upper()})", text_color="#2ecc71")
        else:
            pass
    except Exception as e:
        if auto:
            return
        status_label.configure(text=f"🔴 加载失败：{e}", text_color="#e74c3c")

# ==================== 7. UI 界面布局 ====================
title_label = ctk.CTkLabel(app, text="⚙️ 自动售卖 2.0 YBT", font=("Arial", 20, "bold"))
title_label.pack(pady=20)

# --- 快捷键下拉选择区 ---
key_frame = ctk.CTkFrame(app)
key_frame.pack(pady=10, padx=30, fill="x")

ctk.CTkLabel(key_frame, text="⌨️ 自定义热键:", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")

ctk.CTkLabel(key_frame, text="启动键:").grid(row=0, column=1, padx=5)
start_key_var = ctk.StringVar(value="F4")
start_key_menu = ctk.CTkOptionMenu(key_frame, variable=start_key_var, values=display_keys, width=80)
start_key_menu.grid(row=0, column=2, padx=5)

ctk.CTkLabel(key_frame, text="关闭键:").grid(row=0, column=3, padx=5)
stop_key_var = ctk.StringVar(value="F12")
stop_key_menu = ctk.CTkOptionMenu(key_frame, variable=stop_key_var, values=display_keys, width=80)
stop_key_menu.grid(row=0, column=4, padx=5)

warn_label = ctk.CTkLabel(key_frame, text="⚠️ 警告：请勿使用ESC等可能导致系统冲突的按键", text_color="#e74c3c", font=("Arial", 11))
warn_label.grid(row=1, column=0, columnspan=5, padx=10, pady=5)

# --- 坐标采集区 ---
tip_label = ctk.CTkLabel(app, text="💡 提示：请先点击下方【开启雷达】，然后按 '左alt' 键抓取坐标", text_color="#7f8c8d", font=("Arial", 12))
tip_label.pack(pady=5)

toggle_radar_btn = ctk.CTkButton(app, text="📡 开启坐标雷达", command=toggle_radar, fg_color="#2980b9", hover_color="#2471a3")
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

# --- 延迟输入 ---
delay_frame = ctk.CTkFrame(app)
delay_frame.pack(pady=8, padx=30, fill="x")
ctk.CTkLabel(delay_frame, text="⏱️ 服务器响应延迟 (秒):", font=("Arial", 13, "bold"), width=180, anchor="w").pack(side="left", padx=15, pady=8)
delay_input = ctk.CTkEntry(delay_frame, width=120, placeholder_text="例如: 0.35")
delay_input.pack(side="left", padx=10)
delay_input.insert(0, "0.35")  # 默认值

# --- 状态栏 ---
status_label = ctk.CTkLabel(app, text="⏸️ 准备就绪。请先开启雷达以抓取坐标", font=("Arial", 13, "bold"))
status_label.pack(pady=20)

# --- 按钮组（重置、保存、加载） ---
btn_frame = ctk.CTkFrame(app)
btn_frame.pack(pady=5, fill="x", padx=60)
reset_button = ctk.CTkButton(btn_frame, text="🔄 重置", command=reset_coordinates, fg_color="#d35400", hover_color="#b33921")
reset_button.pack(side="left", expand=True, fill="x", padx=2)
save_button = ctk.CTkButton(btn_frame, text="💾 保存方案", command=save_config, fg_color="#2980b9", hover_color="#2471a3")
save_button.pack(side="left", expand=True, fill="x", padx=2)
load_button = ctk.CTkButton(btn_frame, text="📂 加载方案", command=lambda: load_config(auto=False), fg_color="#27ae60", hover_color="#1e8449")
load_button.pack(side="left", expand=True, fill="x", padx=2)

# --- 三步确认按钮 ---
bind_button = ctk.CTkButton(app, text="🔗 1. 确认并绑定上述参数", command=bind_coordinates, fg_color="#34495e", hover_color="#2c3e50")
bind_button.pack(pady=5, fill="x", padx=60)

confirm_program_button = ctk.CTkButton(app, text="🔒 2. 确认锁定程序坐标", command=confirm_program, fg_color="#16a085", hover_color="#118168", state="disabled")
confirm_program_button.pack(pady=5, fill="x", padx=60)

start_button = ctk.CTkButton(app, text="🚀 3. 确认启动程序 (运行)", command=start_final_program, font=("Arial", 14, "bold"), height=40, state="disabled")
start_button.pack(pady=15, fill="x", padx=60)

# ==================== 8. 自动加载配置 ====================
load_config(auto=True)

# ==================== 9. 启动主循环 ====================
app.mainloop()