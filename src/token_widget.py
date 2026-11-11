import argparse
import ctypes
import json
import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import font

from token_usage import collect_sessions, summarize

WINDOW_WIDTH = 240
WINDOW_HEIGHT = 190
TRANSPARENT = "#010203"
WALK_FPS = 35

CATS = {
    "luna": "Luna · silver tabby",
    "mochi": "Mochi · ginger tabby",
    "smokey": "Smokey · blue-black cat",
    "coco": "Coco · chocolate tabby",
}

AI_FACTS = (
    "The first neural network was described in 1957.",
    "AI learns patterns by adjusting weights.",
    "A context window is the text AI can consider at once.",
    "Cached tokens help AI reuse earlier work.",
    "The term AI was coined in 1956.",
    "Alan Turing proposed his famous test in 1950.",
    "Models split text into pieces called tokens.",
    "Different models can count tokens differently.",
    "Inference is when AI uses what it learned.",
    "Embeddings turn words into number coordinates.",
    "Temperature can make AI answers more varied.",
    "Attention helps AI focus on important tokens.",
    "Training adjusts a model's internal weights.",
    "Small models can be great at special tasks.",
    "AI benchmarks test skills, not consciousness.",
)


def resource_path(relative):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent / "assets"))
    return base / relative


def taskbar_geometry():
    class Rect(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    class AppBarData(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("hWnd", ctypes.c_void_p),
            ("uCallbackMessage", ctypes.c_uint),
            ("uEdge", ctypes.c_uint),
            ("rc", Rect),
            ("lParam", ctypes.c_void_p),
        ]

    work_area = Rect()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work_area), 0)
    floor = work_area.bottom
    if os.name == "nt":
        app_bar = AppBarData()
        app_bar.cbSize = ctypes.sizeof(app_bar)
        if ctypes.windll.shell32.SHAppBarMessage(0x00000005, ctypes.byref(app_bar)):
            if app_bar.uEdge == 1:
                floor = app_bar.rc.bottom
            elif app_bar.uEdge == 3:
                floor = app_bar.rc.top
    minimum_x = work_area.left + 8
    maximum_x = max(minimum_x, work_area.right - WINDOW_WIDTH - 8)
    return floor - 182, minimum_x, maximum_x


def draw_bubble(canvas, text, usage_font, fact_font, usage=False):
    canvas.create_rectangle(5, 4, 235, 64, fill="#181e2b", outline="#8b7cff", width=2)
    canvas.create_polygon(108, 64, 124, 64, 116, 72, fill="#181e2b", outline="#8b7cff")
    canvas.create_text(
        120,
        33,
        text=text,
        fill="#f3f6fc",
        font=usage_font if usage else fact_font,
        width=210,
        justify="center",
    )


class TokenWidget:
    def __init__(self, root, data_root, refresh_seconds, appearance=None):
        self.root = root
        self.data_root = data_root
        self.refresh_seconds = refresh_seconds
        self.results = queue.Queue()
        self.loading = False
        self.closed = False
        self.config_path = data_root / "token_widget.json"
        self.config = self.load_config()
        self.topmost = tk.BooleanVar(value=self.config.get("topmost", True))
        self.wandering = tk.BooleanVar(value=self.config.get("wandering", True))
        selected_appearance = appearance or self.config.get("appearance", "luna")
        if selected_appearance not in CATS:
            selected_appearance = "luna"
        self.appearance = tk.StringVar(value=selected_appearance)
        self.hovering = False
        self.dragging = False
        self.drag_moved = False
        self.action = None
        self.action_until = 0
        self.action_duration = 1
        self.sleeping = False
        self.total = "…"
        self.fact = None
        self.thought_started = 0
        self.thought_until = 0
        self.walk_phase = 0
        self.direction = "right"
        self.frame_cache = {}
        self.last_geometry_x = None

        now = time.monotonic()
        self.last_frame = now
        self.next_thought = now + random.uniform(12, 25)
        self.behavior = "walk" if self.wandering.get() else "sit"
        self.behavior_until = now + random.uniform(7, 12)

        root.title("Kimi Token Usage")
        root.overrideredirect(True)
        root.attributes("-topmost", self.topmost.get())
        root.configure(bg=TRANSPARENT, highlightthickness=0)
        root.resizable(False, False)
        try:
            root.attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

        self.y, self.minimum_x, self.maximum_x = taskbar_geometry()
        self.x = self.maximum_x - 25
        self.target_x = self.random_target()
        root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{round(self.x)}+{self.y}")

        self.fonts = {
            "usage": font.Font(family="Segoe UI", size=12, weight="bold"),
            "fact": font.Font(family="Segoe UI", size=9),
            "symbol": font.Font(family="Segoe UI", size=13, weight="bold"),
        }
        self.canvas = tk.Canvas(
            root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=TRANSPARENT,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)

        self.menu = tk.Menu(
            root,
            tearoff=False,
            bg="#181e2b",
            fg="#f3f6fc",
            activebackground="#30394d",
            activeforeground="#f3f6fc",
        )
        appearance_menu = tk.Menu(self.menu, tearoff=False, bg="#181e2b", fg="#f3f6fc")
        for key, name in CATS.items():
            appearance_menu.add_radiobutton(
                label=name,
                value=key,
                variable=self.appearance,
                command=lambda selected=key: self.select_appearance(selected),
            )
        self.menu.add_cascade(label="Choose your cat", menu=appearance_menu)
        self.menu.add_checkbutton(label="Always on top", variable=self.topmost, command=self.toggle_topmost)
        self.menu.add_checkbutton(label="Walk on the taskbar", variable=self.wandering, command=self.toggle_wandering)
        self.menu.add_command(label="Give a snack", command=self.feed)
        self.menu.add_command(label="Play together", command=self.play)
        self.menu.add_command(label="Think of an AI fact", command=self.start_thought)
        self.menu.add_command(label="Lay down / stand up", command=self.toggle_lay)
        self.menu.add_command(label="Sleep / wake up", command=self.toggle_sleep)
        self.menu.add_command(label="Refresh now", command=self.manual_refresh)
        self.menu.add_separator()
        self.menu.add_command(
            label="Artwork: bluecarrot16 (CC-BY 3.0)",
            command=lambda: webbrowser.open("https://opengameart.org/content/lpc-cats-and-dogs"),
        )
        self.menu.add_command(label="Close", command=self.close)
        root.bind_all("<Button-3>", self.show_menu)
        root.bind("<Escape>", lambda event: self.close())
        self.canvas.bind("<Double-Button-1>", lambda event: self.manual_refresh())
        self.canvas.bind("<Enter>", lambda event: self.set_hover(True))
        self.canvas.bind("<Leave>", lambda event: self.set_hover(False))
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        root.after(0, self.refresh)
        root.after(28, self.animate)

    def get_frame(self, appearance, direction, index, pose="walk"):
        key = (appearance, direction, pose, index)
        if key not in self.frame_cache:
            if pose in ("walk", "sit", "sleep"):
                filename = f"{pose}_{index:03d}.png"
            else:
                filename = f"{pose}.png"
            path = resource_path(Path("cats") / appearance / direction / filename)
            self.frame_cache[key] = tk.PhotoImage(file=str(path))
        return self.frame_cache[key]

    def get_bubble(self, name):
        key = ("bubble", name)
        if key not in self.frame_cache:
            self.frame_cache[key] = tk.PhotoImage(file=str(resource_path(Path("bubbles") / name)))
        return self.frame_cache[key]

    def draw_thought_bubble(self, now):
        elapsed = now - self.thought_started
        if elapsed < 0.35:
            image = self.get_bubble("small.png")
            self.canvas.create_image(80, 65, image=image, anchor="nw")
        elif elapsed < 0.7:
            image = self.get_bubble("medium.png")
            self.canvas.create_image(67, 51, image=image, anchor="nw")
        else:
            image = self.get_bubble(f"fact_{self.fact:02d}.png")
            self.canvas.create_image(0, 0, image=image, anchor="nw")

    def load_config(self):
        try:
            with self.config_path.open(encoding="utf-8") as handle:
                config = json.load(handle)
            return config if isinstance(config, dict) else {}
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def save_config(self):
        try:
            self.data_root.mkdir(parents=True, exist_ok=True)
            with self.config_path.open("w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "appearance": self.appearance.get(),
                        "topmost": self.topmost.get(),
                        "wandering": self.wandering.get(),
                    },
                    handle,
                    indent=2,
                )
        except OSError:
            pass

    def random_target(self):
        return random.uniform(self.minimum_x, self.maximum_x)

    def refresh(self):
        if self.closed:
            return
        self.root.after(self.refresh_seconds * 1000, self.refresh)
        if self.loading:
            return
        self.loading = True
        threading.Thread(target=self.load_usage, daemon=True).start()

    def manual_refresh(self):
        self.start_action("excited", 1.2)
        self.refresh()

    def load_usage(self):
        try:
            summary = summarize(collect_sessions(self.data_root))
            self.results.put(("ok", summary))
        except Exception as error:
            self.results.put(("error", str(error)))

    def process_results(self):
        try:
            while True:
                result = self.results.get_nowait()
                self.loading = False
                self.total = f"{result[1]['totalTokens']:,}" if result[0] == "ok" else "Unavailable"
        except queue.Empty:
            pass

    def choose_behavior(self, now):
        if not self.wandering.get():
            self.behavior = "sit"
            self.behavior_until = now + 10
            return
        self.behavior = random.choices(("walk", "sit", "lay", "sleep"), weights=(5, 3, 2, 1))[0]
        durations = {"walk": (6, 13), "sit": (5, 11), "lay": (6, 12), "sleep": (8, 16)}
        self.behavior_until = now + random.uniform(*durations[self.behavior])
        if self.behavior == "walk":
            self.target_x = self.random_target()

    def update_behavior(self, now, elapsed):
        if self.behavior == "walk" and not self.wandering.get():
            self.behavior = "sit"
        walking = self.behavior == "walk" and self.wandering.get() and not self.hovering and not self.dragging and not self.action
        if walking:
            difference = self.target_x - self.x
            if abs(difference) < 3:
                self.target_x = self.random_target()
                difference = self.target_x - self.x
            self.direction = "right" if difference >= 0 else "left"
            self.x += (1 if difference >= 0 else -1) * min(abs(difference), elapsed * 55)
            rounded_x = round(self.x)
            if rounded_x != self.last_geometry_x:
                self.root.geometry(f"+{rounded_x}+{self.y}")
                self.last_geometry_x = rounded_x
        if now >= self.behavior_until and not self.action and not self.dragging:
            self.choose_behavior(now)

    def draw_overlays(self, mood, action_progress):
        if mood == "sleepy":
            self.canvas.create_text(194, 78, text="Z", fill="#b9b0ff", font=self.fonts["symbol"])
            self.canvas.create_text(205, 67, text="z", fill="#ffe59a", font=self.fonts["fact"])
        if mood == "think":
            self.canvas.create_text(201, 81, text="?", fill="#ffe59a", font=self.fonts["symbol"])
        if mood in ("pet", "grabbed"):
            self.canvas.create_text(202, 85 - action_progress * 8, text="♥", fill="#ff9ebd", font=self.fonts["symbol"])
        if mood == "excited":
            self.canvas.create_text(198, 80, text="✦", fill="#ffe59a", font=self.fonts["symbol"])
        if mood == "snack":
            head_x = 188 if self.direction == "right" else 52
            cookie_x = head_x + (18 if self.direction == "right" else -18) * (1 - action_progress)
            cookie_y = 122 - action_progress * 7
            radius = max(2, 6 - action_progress * 3)
            self.canvas.create_oval(cookie_x - radius, cookie_y - radius, cookie_x + radius, cookie_y + radius, fill="#d99b5f", outline="#8b5737")
            self.canvas.create_oval(cookie_x - 2, cookie_y - 2, cookie_x, cookie_y, fill="#5e3b32", outline="")
        if mood == "play":
            ball_x = 195 + (1 if self.direction == "right" else -1) * action_progress * 8
            ball_y = 121 - abs(action_progress * 2 - 1) * 35
            self.canvas.create_oval(ball_x - 6, ball_y - 6, ball_x + 6, ball_y + 6, fill="#ff9ebd", outline="#ffe59a", width=2)

    def animate(self):
        if self.closed:
            return
        now = time.monotonic()
        elapsed = min(now - self.last_frame, 0.25)
        self.last_frame = now
        self.process_results()
        self.update_behavior(now, elapsed)

        if self.action and now >= self.action_until:
            self.action = None
        if now >= self.next_thought and not self.sleeping and self.behavior != "sleep" and not self.action:
            self.start_thought()
        if self.thought_until and now >= self.thought_until:
            self.thought_until = 0
            self.fact = None

        sleepy = self.sleeping or self.behavior == "sleep"
        if self.dragging and self.drag_moved:
            mood = "grabbed"
        elif self.action:
            mood = self.action
        elif sleepy:
            mood = "sleepy"
        elif self.hovering:
            mood = "happy"
        elif self.fact is not None:
            mood = "think"
        else:
            mood = "normal"

        walking = self.behavior == "walk" and self.wandering.get() and not self.hovering and not sleepy and not self.action and not self.dragging
        lying = self.behavior == "lay" and not sleepy
        if walking:
            self.walk_phase = (self.walk_phase + elapsed) % 1
        pose = "walk" if walking else "grabbed" if mood == "grabbed" else "sleep" if sleepy else "lay" if lying else "sit"
        if walking:
            frame_index = int(self.walk_phase * WALK_FPS) % WALK_FPS
        elif pose == "sit":
            frame_index = int(now * 3) % 4
        elif pose == "sleep":
            frame_index = int(now * 1.5) % 4
        else:
            frame_index = 0
        action_progress = 1 - (self.action_until - now) / self.action_duration if self.action else 0

        self.canvas.delete("all")
        if self.hovering:
            draw_bubble(self.canvas, f"Total AI token usage\n{self.total}", self.fonts["usage"], self.fonts["fact"], usage=True)
        image = self.get_frame(self.appearance.get(), self.direction, frame_index, pose)
        self.canvas.create_image(120, 34, image=image, anchor="n")
        self.draw_overlays(mood, action_progress)
        if not self.hovering and self.fact is not None:
            self.draw_thought_bubble(now)

        if self.fact is not None and now - self.thought_started < 0.75:
            delay = 50
        elif self.dragging or self.action or walking:
            delay = round(1000 / WALK_FPS)
        elif sleepy:
            delay = 700
        elif self.hovering:
            delay = 200
        else:
            delay = 350
        self.root.after(delay, self.animate)

    def start_thought(self):
        now = time.monotonic()
        self.fact = random.randrange(len(AI_FACTS))
        self.thought_started = now
        self.thought_until = now + 8
        self.next_thought = now + random.uniform(35, 65)
        self.sleeping = False
        if self.behavior in ("lay", "sleep"):
            self.behavior = "sit"

    def start_action(self, action, duration):
        self.action = action
        self.action_until = time.monotonic() + duration
        self.action_duration = duration
        self.sleeping = False

    def set_hover(self, hovering):
        self.hovering = hovering
        if hovering:
            self.sleeping = False
            if self.behavior in ("lay", "sleep"):
                self.behavior = "sit"

    def select_appearance(self, appearance):
        self.appearance.set(appearance)
        self.save_config()
        self.start_action("excited", 1.2)

    def pet(self):
        self.start_action("pet", 1.4)

    def feed(self):
        self.start_action("snack", 2.4)

    def play(self):
        self.start_action("play", 3)

    def toggle_lay(self):
        self.behavior = "sit" if self.behavior == "lay" else "lay"
        self.sleeping = False
        self.action = None
        self.behavior_until = time.monotonic() + 10

    def toggle_sleep(self):
        self.sleeping = not self.sleeping
        self.action = None

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost.get())
        self.save_config()

    def toggle_wandering(self):
        if self.wandering.get():
            self.behavior = "walk"
            self.target_x = self.random_target()
        else:
            self.behavior = "sit"
        self.save_config()

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def start_drag(self, event):
        self.dragging = True
        self.drag_moved = False
        self.action = None
        self.sleeping = False
        self.press_position = (event.x_root, event.y_root)
        self.drag_x = event.x_root - self.root.winfo_x()
        self.drag_y = event.y_root - self.root.winfo_y()

    def drag(self, event):
        if abs(event.x_root - self.press_position[0]) > 3 or abs(event.y_root - self.press_position[1]) > 3:
            self.drag_moved = True
        if self.drag_moved:
            self.x = event.x_root - self.drag_x
            self.y = event.y_root - self.drag_y
            self.root.geometry(f"+{round(self.x)}+{round(self.y)}")

    def stop_drag(self, event):
        if not self.dragging:
            return
        was_click = not self.drag_moved
        self.dragging = False
        self.y, self.minimum_x, self.maximum_x = taskbar_geometry()
        self.x = max(self.minimum_x, min(self.maximum_x, self.x))
        self.root.geometry(f"+{round(self.x)}+{self.y}")
        self.target_x = self.random_target()
        if was_click:
            self.pet()

    def close(self):
        self.closed = True
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Show a live Kimi Code token-count desktop pet.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("KIMI_CODE_HOME", Path.home() / ".kimi-code")),
    )
    parser.add_argument("--refresh-seconds", type=int, default=60)
    parser.add_argument("--appearance", choices=tuple(CATS))
    args = parser.parse_args()
    if args.refresh_seconds < 15:
        parser.error("--refresh-seconds must be at least 15")

    root = tk.Tk()
    icon_path = resource_path("token_widget.ico")
    if icon_path.is_file():
        root.iconbitmap(default=str(icon_path))
    TokenWidget(root, args.root.expanduser(), args.refresh_seconds, args.appearance)
    root.mainloop()


if __name__ == "__main__":
    main()
