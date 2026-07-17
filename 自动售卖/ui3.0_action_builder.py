import json
import os
import random
import threading
import time
from typing import Any, Dict, List, Optional

import customtkinter as ctk
import pyautogui
from pynput import keyboard, mouse


APP_TITLE = "自动售卖 3.0 - 自定义动作版 YBT"
CONFIG_FILE = "action_config.json"

pyautogui.FAILSAFE = True


KEY_DISPLAY_MAP = {
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4", "F5": "f5", "F6": "f6",
    "F7": "f7", "F8": "f8", "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
    "空格 Space": "space",
    "回车 Enter": "enter",
    "退格 Backspace": "backspace",
    "Tab": "tab",
    "Shift": "shift",
    "Ctrl": "ctrl",
    "Alt": "alt",
    "上方向 Up": "up",
    "下方向 Down": "down",
    "左方向 Left": "left",
    "右方向 Right": "right",
}
KEY_TO_DISPLAY = {value: key for key, value in KEY_DISPLAY_MAP.items()}
DISPLAY_KEYS = list(KEY_DISPLAY_MAP.keys())

ACTION_TYPES = ["鼠标点击", "键盘按键", "输入文字", "等待"]
ACTION_TYPE_MAP = {
    "鼠标点击": "click",
    "键盘按键": "key",
    "输入文字": "text",
    "等待": "wait",
}
ACTION_TYPE_DISPLAY = {value: key for key, value in ACTION_TYPE_MAP.items()}


def config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)


def legacy_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def sleep_until_done(seconds: float, stop_event: threading.Event) -> bool:
    end_at = time.time() + max(0.0, seconds)
    while time.time() < end_at:
        if stop_event.is_set():
            return False
        time.sleep(min(0.03, end_at - time.time()))
    return not stop_event.is_set()


def click_with_offset(x: int, y: int, button: str = "left", move_duration: float = 0.15, jitter: int = 2) -> None:
    target_x = x + random.randint(-jitter, jitter) if jitter > 0 else x
    target_y = y + random.randint(-jitter, jitter) if jitter > 0 else y
    pyautogui.moveTo(target_x, target_y, duration=max(0.0, move_duration))
    pyautogui.click(button=button)


def execute_action_sequence(steps: List[Dict[str, Any]], stop_event: threading.Event) -> None:
    for index, step in enumerate(steps, start=1):
        if stop_event.is_set():
            print(f"[停止] 已在第 {index} 步前停止")
            return

        step_type = step.get("type")

        if step_type == "click":
            count = max(1, int(step.get("count", 1)))
            interval = max(0.0, float(step.get("interval", 0.05)))
            for click_index in range(count):
                if stop_event.is_set():
                    return
                click_with_offset(
                    int(step["x"]),
                    int(step["y"]),
                    button=step.get("button", "left"),
                    move_duration=float(step.get("move_duration", 0.15)),
                    jitter=int(step.get("jitter", 2)),
                )
                if click_index < count - 1 and not sleep_until_done(interval, stop_event):
                    return

        elif step_type == "key":
            pyautogui.press(step["key"])

        elif step_type == "text":
            pyautogui.write(step.get("text", ""), interval=max(0.0, float(step.get("interval", 0.02))))

        elif step_type == "wait":
            if not sleep_until_done(float(step.get("seconds", 0.2)), stop_event):
                return

        delay_after = float(step.get("delay_after", 0))
        if delay_after > 0 and not sleep_until_done(delay_after, stop_event):
            return


class ActionBuilderApp:
    def __init__(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        self.app = ctk.CTk()
        self.app.geometry("860x820")
        self.app.title(APP_TITLE)

        self.steps: List[Dict[str, Any]] = []
        self.selected_index: Optional[int] = None
        self.listener_started = False
        self.listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        self.last_mouse_click: Optional[tuple[int, int]] = None
        self.stop_event = threading.Event()
        self.run_thread: Optional[threading.Thread] = None

        self.start_key_var = ctk.StringVar(value="F4")
        self.stop_key_var = ctk.StringVar(value="F12")
        self.action_type_var = ctk.StringVar(value="鼠标点击")
        self.key_var = ctk.StringVar(value="右方向 Right")

        self.build_ui()
        self.start_mouse_click_monitor()
        self.load_config(auto=True)

    def build_ui(self) -> None:
        self.title_label = ctk.CTkLabel(self.app, text=APP_TITLE, font=("Microsoft YaHei UI", 22, "bold"))
        self.title_label.pack(pady=(18, 10))

        hotkey_frame = ctk.CTkFrame(self.app)
        hotkey_frame.pack(pady=6, padx=24, fill="x")
        ctk.CTkLabel(hotkey_frame, text="启动键", width=70).pack(side="left", padx=(12, 4), pady=10)
        ctk.CTkOptionMenu(hotkey_frame, variable=self.start_key_var, values=DISPLAY_KEYS, width=110).pack(side="left", padx=4)
        ctk.CTkLabel(hotkey_frame, text="停止键", width=70).pack(side="left", padx=(16, 4), pady=10)
        ctk.CTkOptionMenu(hotkey_frame, variable=self.stop_key_var, values=DISPLAY_KEYS, width=110).pack(side="left", padx=4)
        ctk.CTkButton(hotkey_frame, text="启动热键监听", command=self.start_hotkey_listener, width=130).pack(side="right", padx=12)
        ctk.CTkButton(hotkey_frame, text="单次测试执行", command=self.run_once_from_ui, width=130, fg_color="#16a085").pack(side="right", padx=6)

        editor_frame = ctk.CTkFrame(self.app)
        editor_frame.pack(pady=8, padx=24, fill="x")

        row1 = ctk.CTkFrame(editor_frame, fg_color="transparent")
        row1.pack(pady=(12, 6), padx=12, fill="x")
        ctk.CTkLabel(row1, text="动作类型", width=70).pack(side="left")
        ctk.CTkOptionMenu(row1, variable=self.action_type_var, values=ACTION_TYPES, command=lambda _: self.refresh_form_hint(), width=110).pack(side="left", padx=(4, 12))
        ctk.CTkLabel(row1, text="X").pack(side="left")
        self.x_input = ctk.CTkEntry(row1, width=80, placeholder_text="坐标 X")
        self.x_input.pack(side="left", padx=4)
        ctk.CTkLabel(row1, text="Y").pack(side="left")
        self.y_input = ctk.CTkEntry(row1, width=80, placeholder_text="坐标 Y")
        self.y_input.pack(side="left", padx=4)
        ctk.CTkButton(row1, text="读取上次点击坐标", command=self.capture_mouse_position, width=130).pack(side="left", padx=8)
        ctk.CTkLabel(row1, text="按键").pack(side="left", padx=(12, 4))
        ctk.CTkOptionMenu(row1, variable=self.key_var, values=DISPLAY_KEYS, width=120).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(editor_frame, fg_color="transparent")
        row2.pack(pady=6, padx=12, fill="x")
        ctk.CTkLabel(row2, text="文本").pack(side="left")
        self.text_input = ctk.CTkEntry(row2, width=190, placeholder_text="输入文字动作使用")
        self.text_input.pack(side="left", padx=4)
        ctk.CTkLabel(row2, text="点击次数").pack(side="left", padx=(12, 4))
        self.count_input = ctk.CTkEntry(row2, width=64)
        self.count_input.insert(0, "1")
        self.count_input.pack(side="left", padx=4)
        ctk.CTkLabel(row2, text="间隔/等待秒").pack(side="left", padx=(12, 4))
        self.interval_input = ctk.CTkEntry(row2, width=72)
        self.interval_input.insert(0, "0.05")
        self.interval_input.pack(side="left", padx=4)
        ctk.CTkLabel(row2, text="动作后延迟").pack(side="left", padx=(12, 4))
        self.delay_after_input = ctk.CTkEntry(row2, width=72)
        self.delay_after_input.insert(0, "0.10")
        self.delay_after_input.pack(side="left", padx=4)

        row3 = ctk.CTkFrame(editor_frame, fg_color="transparent")
        row3.pack(pady=(6, 12), padx=12, fill="x")
        ctk.CTkButton(row3, text="添加动作", command=self.add_action, width=110, fg_color="#2980b9").pack(side="left", padx=4)
        ctk.CTkButton(row3, text="更新选中动作", command=self.update_selected_action, width=120, fg_color="#8e44ad").pack(side="left", padx=4)
        ctk.CTkButton(row3, text="导入旧版售卖流程", command=self.import_legacy_sequence, width=150, fg_color="#d35400").pack(side="left", padx=4)
        ctk.CTkButton(row3, text="取消选中", command=self.clear_selection, width=100).pack(side="left", padx=4)
        self.form_hint = ctk.CTkLabel(row3, text="", text_color="#7f8c8d")
        self.form_hint.pack(side="left", padx=12)

        coord_tip = ctk.CTkLabel(
            editor_frame,
            text="坐标说明：先在目标位置真实点击一次，再回到本软件点“读取上次点击坐标”。它读取的是鼠标上一次按下的位置，不是鼠标当前悬停位置。",
            text_color="#7f8c8d",
            anchor="w",
        )
        coord_tip.pack(pady=(0, 10), padx=12, fill="x")

        list_outer = ctk.CTkFrame(self.app)
        list_outer.pack(pady=8, padx=24, fill="both", expand=True)
        ctk.CTkLabel(list_outer, text="动作列表：按顺序执行", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.steps_frame = ctk.CTkScrollableFrame(list_outer, height=330)
        self.steps_frame.pack(pady=(4, 10), padx=12, fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(self.app)
        bottom_frame.pack(pady=8, padx=24, fill="x")
        ctk.CTkButton(bottom_frame, text="保存方案", command=self.save_config, fg_color="#2980b9").pack(side="left", expand=True, fill="x", padx=4, pady=8)
        ctk.CTkButton(bottom_frame, text="加载方案", command=lambda: self.load_config(auto=False), fg_color="#27ae60").pack(side="left", expand=True, fill="x", padx=4, pady=8)
        ctk.CTkButton(bottom_frame, text="停止当前执行", command=self.request_stop, fg_color="#c0392b").pack(side="left", expand=True, fill="x", padx=4, pady=8)

        self.status_label = ctk.CTkLabel(self.app, text="准备就绪。先添加动作，或导入旧版售卖流程。", font=("Microsoft YaHei UI", 13, "bold"))
        self.status_label.pack(pady=(4, 16))
        self.refresh_form_hint()
        self.refresh_steps_view()

    def refresh_form_hint(self) -> None:
        action_type = ACTION_TYPE_MAP[self.action_type_var.get()]
        hints = {
            "click": "点击动作使用 X/Y、点击次数、间隔、动作后延迟。",
            "key": "按键动作使用右侧按键和动作后延迟。",
            "text": "输入文字动作使用文本、间隔和动作后延迟。",
            "wait": "等待动作使用“间隔/等待秒”。",
        }
        self.form_hint.configure(text=hints[action_type])

    def start_mouse_click_monitor(self) -> None:
        # 记录鼠标上一次按下的位置。这样用户可以先点目标位置，再回界面读取坐标。
        def on_click(x: int, y: int, button: mouse.Button, pressed: bool) -> None:
            if pressed:
                self.last_mouse_click = (x, y)

        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

    def capture_mouse_position(self) -> None:
        if self.last_mouse_click is None:
            self.set_status("还没有记录到鼠标点击。请先在目标位置真实点击一次。", "#f39c12")
            return

        x, y = self.last_mouse_click
        self.x_input.delete(0, "end")
        self.x_input.insert(0, str(x))
        self.y_input.delete(0, "end")
        self.y_input.insert(0, str(y))
        self.set_status(f"已读取上次点击坐标：X={x}, Y={y}", "#2ecc71")

    def read_float(self, entry: ctk.CTkEntry, default: float) -> float:
        value = entry.get().strip()
        return default if value == "" else float(value)

    def read_int(self, entry: ctk.CTkEntry, default: int) -> int:
        value = entry.get().strip()
        return default if value == "" else int(value)

    def build_action_from_form(self) -> Dict[str, Any]:
        action_type = ACTION_TYPE_MAP[self.action_type_var.get()]
        delay_after = self.read_float(self.delay_after_input, 0.0)

        if action_type == "click":
            return {
                "type": "click",
                "x": int(self.x_input.get()),
                "y": int(self.y_input.get()),
                "count": self.read_int(self.count_input, 1),
                "interval": self.read_float(self.interval_input, 0.05),
                "delay_after": delay_after,
                "button": "left",
                "move_duration": 0.15,
                "jitter": 2,
            }

        if action_type == "key":
            return {
                "type": "key",
                "key": KEY_DISPLAY_MAP[self.key_var.get()],
                "delay_after": delay_after,
            }

        if action_type == "text":
            return {
                "type": "text",
                "text": self.text_input.get(),
                "interval": self.read_float(self.interval_input, 0.02),
                "delay_after": delay_after,
            }

        return {
            "type": "wait",
            "seconds": self.read_float(self.interval_input, 0.2),
            "delay_after": delay_after,
        }

    def add_action(self) -> None:
        try:
            self.steps.append(self.build_action_from_form())
            self.selected_index = None
            self.refresh_steps_view()
            self.set_status("已添加动作。", "#2ecc71")
        except Exception as error:
            self.set_status(f"添加失败：{error}", "#e74c3c")

    def update_selected_action(self) -> None:
        if self.selected_index is None:
            self.set_status("请先在动作列表里选择一行。", "#f39c12")
            return
        try:
            self.steps[self.selected_index] = self.build_action_from_form()
            self.refresh_steps_view()
            self.set_status("已更新选中动作。", "#2ecc71")
        except Exception as error:
            self.set_status(f"更新失败：{error}", "#e74c3c")

    def select_action(self, index: int) -> None:
        self.selected_index = index
        step = self.steps[index]
        self.action_type_var.set(ACTION_TYPE_DISPLAY.get(step["type"], "鼠标点击"))
        self.delay_after_input.delete(0, "end")
        self.delay_after_input.insert(0, str(step.get("delay_after", 0)))

        self.x_input.delete(0, "end")
        self.y_input.delete(0, "end")
        self.text_input.delete(0, "end")
        self.count_input.delete(0, "end")
        self.interval_input.delete(0, "end")

        if step["type"] == "click":
            self.x_input.insert(0, str(step.get("x", "")))
            self.y_input.insert(0, str(step.get("y", "")))
            self.count_input.insert(0, str(step.get("count", 1)))
            self.interval_input.insert(0, str(step.get("interval", 0.05)))
        elif step["type"] == "key":
            self.key_var.set(KEY_TO_DISPLAY.get(step.get("key", "right"), "右方向 Right"))
            self.count_input.insert(0, "1")
            self.interval_input.insert(0, "0.05")
        elif step["type"] == "text":
            self.text_input.insert(0, step.get("text", ""))
            self.count_input.insert(0, "1")
            self.interval_input.insert(0, str(step.get("interval", 0.02)))
        else:
            self.count_input.insert(0, "1")
            self.interval_input.insert(0, str(step.get("seconds", 0.2)))

        self.refresh_form_hint()
        self.refresh_steps_view()
        self.set_status(f"已选中第 {index + 1} 步。", "#3498db")

    def clear_selection(self) -> None:
        self.selected_index = None
        self.refresh_steps_view()
        self.set_status("已取消选中。", "#7f8c8d")

    def delete_action(self, index: int) -> None:
        del self.steps[index]
        self.selected_index = None
        self.refresh_steps_view()
        self.set_status("已删除动作。", "#2ecc71")

    def move_action(self, index: int, direction: int) -> None:
        new_index = index + direction
        if not 0 <= new_index < len(self.steps):
            return
        self.steps[index], self.steps[new_index] = self.steps[new_index], self.steps[index]
        self.selected_index = new_index
        self.refresh_steps_view()

    def describe_step(self, step: Dict[str, Any]) -> str:
        step_type = step.get("type")
        delay = step.get("delay_after", 0)
        if step_type == "click":
            return f"鼠标点击 ({step.get('x')}, {step.get('y')}) x{step.get('count', 1)}，间隔 {step.get('interval', 0)}s，后延迟 {delay}s"
        if step_type == "key":
            return f"键盘按键 {step.get('key')}，后延迟 {delay}s"
        if step_type == "text":
            text = step.get("text", "")
            preview = text if len(text) <= 18 else text[:18] + "..."
            return f"输入文字 “{preview}”，字符间隔 {step.get('interval', 0)}s，后延迟 {delay}s"
        if step_type == "wait":
            return f"等待 {step.get('seconds', 0)}s，后延迟 {delay}s"
        return str(step)

    def refresh_steps_view(self) -> None:
        for child in self.steps_frame.winfo_children():
            child.destroy()

        if not self.steps:
            ctk.CTkLabel(self.steps_frame, text="还没有动作。可以手动添加，或点击“导入旧版售卖流程”。", text_color="#7f8c8d").pack(pady=30)
            return

        for index, step in enumerate(self.steps):
            selected = index == self.selected_index
            row = ctk.CTkFrame(self.steps_frame, fg_color="#dfeee6" if selected else "transparent")
            row.pack(pady=4, padx=4, fill="x")
            ctk.CTkLabel(row, text=f"{index + 1}. {self.describe_step(step)}", anchor="w").pack(side="left", padx=8, pady=8, fill="x", expand=True)
            ctk.CTkButton(row, text="选中", width=54, command=lambda i=index: self.select_action(i)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="上移", width=54, command=lambda i=index: self.move_action(i, -1)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="下移", width=54, command=lambda i=index: self.move_action(i, 1)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="删除", width=54, fg_color="#c0392b", command=lambda i=index: self.delete_action(i)).pack(side="left", padx=(2, 8))

    def import_legacy_sequence(self) -> None:
        legacy_data = self.read_legacy_config()
        if legacy_data:
            a_x, a_y = legacy_data["a_x"], legacy_data["a_y"]
            b_x, b_y = legacy_data["b_x"], legacy_data["b_y"]
            c_x, c_y = legacy_data["c_x"], legacy_data["c_y"]
            enter_delay = legacy_data["delay"]
        else:
            try:
                a_x = b_x = c_x = int(self.x_input.get())
                a_y = b_y = c_y = int(self.y_input.get())
                enter_delay = 0.35
            except ValueError:
                self.set_status("没有找到旧版 config.json。请先抓取或输入位置 A 坐标，再导入模板。", "#f39c12")
                return

        self.steps = [
            {"type": "click", "x": a_x, "y": a_y, "count": 2, "interval": 0.08, "delay_after": 0.15, "button": "left", "move_duration": 0.15, "jitter": 2},
            {"type": "key", "key": "right", "delay_after": 0.05},
            {"type": "key", "key": "backspace", "delay_after": 0.10},
            {"type": "key", "key": "enter", "delay_after": enter_delay},
            {"type": "click", "x": b_x, "y": b_y, "count": 1, "interval": 0.05, "delay_after": 0.10, "button": "left", "move_duration": 0.15, "jitter": 2},
            {"type": "click", "x": c_x, "y": c_y, "count": 1, "interval": 0.05, "delay_after": 0.00, "button": "left", "move_duration": 0.15, "jitter": 2},
        ]
        self.selected_index = None
        self.refresh_steps_view()
        if legacy_data:
            self.set_status("已从旧版 config.json 导入 A/B/C 坐标和延迟。", "#2ecc71")
        else:
            self.set_status("已导入旧版流程模板。请把第 5、6 步选中后改成 B/C 坐标。", "#2ecc71")

    def read_legacy_config(self) -> Optional[Dict[str, Any]]:
        path = legacy_config_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return {
                "a_x": int(data["a_x"]),
                "a_y": int(data["a_y"]),
                "b_x": int(data["b_x"]),
                "b_y": int(data["b_y"]),
                "c_x": int(data["c_x"]),
                "c_y": int(data["c_y"]),
                "delay": float(data.get("delay", 0.35)),
            }
        except Exception:
            return None

    def build_config(self) -> Dict[str, Any]:
        start_key = KEY_DISPLAY_MAP[self.start_key_var.get()]
        stop_key = KEY_DISPLAY_MAP[self.stop_key_var.get()]
        if start_key == stop_key:
            raise ValueError("启动键和停止键不能相同")
        if not self.steps:
            raise ValueError("动作列表为空")
        return {
            "start_key": start_key,
            "stop_key": stop_key,
            "steps": self.steps,
        }

    def save_config(self) -> None:
        try:
            data = self.build_config()
            with open(config_path(), "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            self.set_status(f"方案已保存：{config_path()}", "#2ecc71")
        except Exception as error:
            self.set_status(f"保存失败：{error}", "#e74c3c")

    def load_config(self, auto: bool = False) -> None:
        path = config_path()
        if not os.path.exists(path):
            if not auto:
                self.set_status("没有找到 action_config.json。", "#f39c12")
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.start_key_var.set(KEY_TO_DISPLAY.get(data.get("start_key", "f4"), "F4"))
            self.stop_key_var.set(KEY_TO_DISPLAY.get(data.get("stop_key", "f12"), "F12"))
            self.steps = list(data.get("steps", []))
            self.selected_index = None
            self.refresh_steps_view()
            self.set_status("方案已加载。", "#2ecc71")
        except Exception as error:
            if not auto:
                self.set_status(f"加载失败：{error}", "#e74c3c")

    def normalize_pressed_key(self, key: keyboard.Key) -> str:
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        if hasattr(key, "name") and key.name:
            return key.name.lower()
        return str(key).replace("Key.", "").lower()

    def start_hotkey_listener(self) -> None:
        if self.listener_started:
            self.set_status("热键监听已经启动。", "#3498db")
            return
        try:
            self.build_config()
        except Exception as error:
            self.set_status(f"启动监听失败：{error}", "#e74c3c")
            return

        def on_press(key: keyboard.Key) -> None:
            pressed = self.normalize_pressed_key(key)
            start_key = KEY_DISPLAY_MAP[self.start_key_var.get()]
            stop_key = KEY_DISPLAY_MAP[self.stop_key_var.get()]
            if pressed == start_key:
                self.run_once_from_hotkey()
            elif pressed == stop_key:
                self.request_stop()

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()
        self.listener_started = True
        self.set_status(f"热键监听已启动：{KEY_DISPLAY_MAP[self.start_key_var.get()].upper()} 执行，{KEY_DISPLAY_MAP[self.stop_key_var.get()].upper()} 停止。", "#2ecc71")

    def run_once_from_ui(self) -> None:
        try:
            self.build_config()
            self.run_once_from_hotkey()
        except Exception as error:
            self.set_status(f"无法执行：{error}", "#e74c3c")

    def run_once_from_hotkey(self) -> None:
        if self.run_thread and self.run_thread.is_alive():
            self.set_status("当前动作还在执行中，已忽略重复启动。", "#f39c12")
            return

        steps_snapshot = json.loads(json.dumps(self.steps, ensure_ascii=False))
        self.stop_event.clear()
        self.run_thread = threading.Thread(target=self.run_worker, args=(steps_snapshot,), daemon=True)
        self.run_thread.start()

    def run_worker(self, steps_snapshot: List[Dict[str, Any]]) -> None:
        try:
            self.set_status("正在执行动作序列。", "#3498db")
            execute_action_sequence(steps_snapshot, self.stop_event)
            if self.stop_event.is_set():
                self.set_status("执行已停止。", "#f39c12")
            else:
                self.set_status("动作序列执行完成。", "#2ecc71")
        except Exception as error:
            self.set_status(f"执行异常：{error}", "#e74c3c")

    def request_stop(self) -> None:
        self.stop_event.set()
        self.set_status("已请求停止，当前动作完成后会尽快停下。", "#f39c12")

    def set_status(self, text: str, color: str) -> None:
        self.app.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def run(self) -> None:
        self.app.mainloop()


if __name__ == "__main__":
    ActionBuilderApp().run()
