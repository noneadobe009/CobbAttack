"""The CobbAttack window: status light, live activity feed, and the teach-a-word box.

tkinter on purpose — it ships with Python, so Cobb installs nothing extra for the UI.
All app events arrive via a thread-safe queue; only the Tk mainloop touches widgets.
Clicking a "heard" line in the feed pre-fills the correction box, so teaching a word
is: click the mistake, type the truth, press Add.
"""

import ctypes
import os
import queue
import re
import webbrowser
import winsound
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

import config
import jokes
import tray as tray_mod

# Dark cockpit-ish palette.
BG = "#14181d"
PANEL = "#1c2229"
FIELD = "#242c35"
TEXT = "#d7dde3"
DIM = "#7a8794"
GREEN = "#5dd08c"
AMBER = "#e8b33e"
RED = "#e06c5b"
BLUE = "#5aa7e0"
GOLD = "#ffd97a"  # jokes — bright corn gold so people actually notice them

STATE_STYLES = {
    "ready": ("● READY", GREEN),
    "recording": ("● RECORDING", RED),
    "thinking": ("● THINKING", AMBER),
    "starting": ("● STARTING…", AMBER),
}


def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class RoundButton(tk.Canvas):
    """Label-look button: rounded card, thin colored border, hover fill."""

    def __init__(self, master, text, fg, border, command, hover="#2e3946",
                 font=("Segoe UI", 9, "bold"), pad_x=14, pad_y=7, radius=11):
        super().__init__(master, bg=master["bg"], highlightthickness=0, cursor="hand2")
        f = tkfont.Font(font=font)
        w = f.measure(text) + pad_x * 2
        h = f.metrics("linespace") + pad_y * 2
        self.configure(width=w, height=h)
        self._shape = _round_rect(self, 1, 1, w - 2, h - 2, radius,
                                  fill=FIELD, outline=border, width=1.2)
        self.create_text(w // 2, h // 2, text=text, fill=fg, font=font)
        self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self.itemconfigure(self._shape, fill=hover))
        self.bind("<Leave>", lambda e: self.itemconfigure(self._shape, fill=FIELD))


class RoundBox(tk.Canvas):
    """Rounded card hosting one widget that stretches with it."""

    def __init__(self, master, build, fill=FIELD, border="#34455a",
                 focus_border=None, padding=6, radius=11, **kw):
        super().__init__(master, bg=master["bg"], highlightthickness=0, **kw)
        self._fill, self._border, self._radius = fill, border, radius
        self._pad = padding
        self._shape = None
        self._focused = False
        self._focus_border = focus_border
        self.child = build(self)
        self._win = self.create_window(padding, padding, window=self.child, anchor="nw")
        self.bind("<Configure>", self._redraw)
        if focus_border:
            self.child.bind("<FocusIn>", lambda e: self._set_focus(True))
            self.child.bind("<FocusOut>", lambda e: self._set_focus(False))

    def _set_focus(self, focused):
        self._focused = focused
        self.itemconfigure(self._shape, outline=self._focus_border if focused
                           else self._border)

    def _redraw(self, _event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8:
            return
        if self._shape is not None:
            self.delete(self._shape)
        outline = self._focus_border if self._focused else self._border
        self._shape = _round_rect(self, 1, 1, w - 2, h - 2, self._radius,
                                  fill=self._fill, outline=outline, width=1.2)
        self.tag_lower(self._shape)
        self.coords(self._win, self._pad, self._pad)
        self.itemconfigure(self._win, width=w - 2 * self._pad, height=h - 2 * self._pad)


class CobbWindow:
    def __init__(self, on_teach, on_close, on_suggest=None,
                 on_practice=None, practice_phrases=None,
                 on_unteach=None, on_troubleshoot=None,
                 on_valink=None, valink_on=False):
        self._on_teach_cb = on_teach
        self.on_close = on_close
        self.on_suggest = on_suggest or (lambda word: [])
        self.on_practice = on_practice or (lambda on: None)
        self.on_unteach = on_unteach
        self.on_troubleshoot = on_troubleshoot
        self.on_valink = on_valink or (lambda on: None)
        self.practice_phrases = practice_phrases or []
        self.events = queue.Queue()
        self._popup = None
        self._teach_history = []  # (wrong, right) of fixes taught this session
        self._last_click = None   # last clicked word span, for Shift+click phrases
        self._tr_active = False
        self._tr_i = 0
        self._tr_hits = 0
        self._tr_taught = 0
        self._tr_last_raw = None

        self.root = tk.Tk()
        self.root.title("CobbAttack")
        self.root.configure(bg=BG)
        self.root.geometry("700x640")
        self.root.minsize(600, 540)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        # Minimize → system tray (X still quits). Created before the widgets so a
        # failed tray never blocks the window from appearing.
        self.tray = tray_mod.Tray(self.root, on_show=self._restore, on_quit=self._close)
        self._hidden = False
        self.root.bind("<Unmap>", self._on_unmap)
        try:
            self.root.iconbitmap(os.path.join(config.ROOT, "cobbattack.ico"))
        except tk.TclError:
            pass  # icon is decoration; never block launch over it
        try:
            icon_png = os.path.join(config.ROOT, "cob-hero-icon.png")
            if os.path.exists(icon_png):
                self._icon_img = tk.PhotoImage(file=icon_png)
                self.root.iconphoto(True, self._icon_img)
        except tk.TclError:
            pass
        self.root.after(10, self._darken_title_bar)

        base = tkfont.nametofont("TkDefaultFont")
        base.configure(family="Segoe UI", size=10)
        self.mono = tkfont.Font(family="Consolas", size=10)

        # --- Header: title, state light, device line ---
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(4, 8))
        here = config.ROOT
        hero_png = os.path.join(here, "cob-hero-48.png")
        hero_big = os.path.join(here, "cob-hero-72.png")
        if os.path.exists(hero_png):
            self._hero_img = tk.PhotoImage(file=hero_png)  # keep refs — tk drops them otherwise
            self._hero_img_big = (tk.PhotoImage(file=hero_big)
                                  if os.path.exists(hero_big) else self._hero_img)
            # 12px left pad: puts the icon's center where the pop-over's center will
            # be, so the popped jet's left edge lines up with the joke text below
            hero_lbl = tk.Label(header, image=self._hero_img, bg=BG)
            hero_lbl.pack(side="left", padx=(12, 8))
            # hover pop-over: floats via place() so the header keeps its tight 48px
            # height — the big jet is allowed to hang down over the joke line
            big_lbl = tk.Label(self.root, image=self._hero_img_big, bg=BG, bd=0)

            def _hero_pop(_e):
                # centered on the small icon so it grows out from the middle
                x = (hero_lbl.winfo_rootx() - self.root.winfo_rootx()
                     + (hero_lbl.winfo_width() - self._hero_img_big.width()) // 2)
                y = (hero_lbl.winfo_rooty() - self.root.winfo_rooty()
                     + (hero_lbl.winfo_height() - self._hero_img_big.height()) // 2)
                big_lbl.place(x=max(x, 0), y=max(y, 0))
                big_lbl.lift()

            hero_lbl.bind("<Enter>", _hero_pop)
            # the pop-over covers the small icon, so the pointer "leaves" via big_lbl
            big_lbl.bind("<Leave>", lambda e: big_lbl.place_forget())

            # click (on either the icon or its hover pop-over) → full-size art,
            # dead center of the window, with a fresh joke as the caption;
            # click the big picture to dismiss
            xl_png = os.path.join(here, "cob-hero-200.png")
            self._hero_img_xl = (tk.PhotoImage(file=xl_png)
                                 if os.path.exists(xl_png) else self._hero_img_big)
            xl_frame = tk.Frame(self.root, bg=BG, cursor="hand2")
            tk.Label(xl_frame, image=self._hero_img_xl, bg=BG, bd=0).pack()
            xl_caption = tk.Label(xl_frame, text="", bg=BG, fg=GOLD,
                                  wraplength=340, justify="center",
                                  font=("Segoe UI", 11, "italic"))
            xl_caption.pack(pady=(4, 8), padx=12)

            def _hero_open(_e):
                big_lbl.place_forget()
                xl_caption.configure(text=f"“{jokes.pick()}”")
                xl_frame.place(relx=0.5, rely=0.5, anchor="center")
                xl_frame.lift()

            hero_lbl.configure(cursor="hand2")
            big_lbl.configure(cursor="hand2")
            hero_lbl.bind("<Button-1>", _hero_open)
            big_lbl.bind("<Button-1>", _hero_open)

            def _xl_dismiss_if_left(_e):
                # <Leave> also fires when the pointer crosses onto the caption —
                # only dismiss once it is truly outside the frame
                px, py = xl_frame.winfo_pointerx(), xl_frame.winfo_pointery()
                fx, fy = xl_frame.winfo_rootx(), xl_frame.winfo_rooty()
                if not (fx <= px < fx + xl_frame.winfo_width()
                        and fy <= py < fy + xl_frame.winfo_height()):
                    xl_frame.place_forget()

            # mouse wandering off the big art (or a click anywhere on it) dismisses it
            xl_frame.bind("<Leave>", _xl_dismiss_if_left)
            for child in xl_frame.winfo_children():
                child.bind("<Leave>", _xl_dismiss_if_left)
                child.bind("<Button-1>", lambda e: xl_frame.place_forget())
            xl_frame.bind("<Button-1>", lambda e: xl_frame.place_forget())
        else:  # Cobb-proof fallback: the drawn mini-hero
            hero = tk.Canvas(header, width=48, height=30, bg=BG, highlightthickness=0)
            hero.pack(side="left", padx=(0, 8))
            self._draw_hero(hero)
        self._draw_retro_title(header)
        self.state_label = tk.Label(header, text="● STARTING…", bg=BG, fg=AMBER,
                                    font=("Segoe UI", 11, "bold"))
        self.state_label.pack(side="right")
        self.joke_label = tk.Label(self.root, text=f"“{jokes.pick()}”", bg=BG, fg=GOLD,
                                   anchor="w", justify="left", wraplength=580,
                                   font=("Segoe UI", 11, "italic"))
        self.joke_label.pack(fill="x", padx=16, pady=(0, 4))
        self.joke_label.bind("<Button-1>",
                             lambda e: self.joke_label.configure(text=f"“{jokes.pick()}”"))
        self.device_label = tk.Label(self.root, text="starting engine…", bg=BG, fg=DIM,
                                     anchor="w", font=("Segoe UI", 9))
        self.device_label.pack(fill="x", padx=16)

        toolbar = tk.Frame(self.root, bg=BG)
        toolbar.pack(fill="x", padx=16, pady=(10, 0))
        self.setup_btn = RoundButton(toolbar, "🛠️  SETUP INSTRUCTION", fg=AMBER,
                                     border="#6b5a2a", command=self._open_setup)
        self.setup_btn.pack(side="left")
        self.trainer_btn = RoundButton(toolbar, "🎯  VOICE TRAINER", fg=GREEN,
                                       border="#3a6b4d", command=self._toggle_trainer)
        self.trainer_btn.pack(side="left", padx=(8, 0))
        self.guide_btn = RoundButton(toolbar, "📖  FLIGHT VOICE GUIDE", fg=BLUE,
                                     border="#3d5a7a", command=self._open_cheatsheet)
        self.guide_btn.pack(side="left", padx=(8, 0))
        self.trouble_btn = RoundButton(toolbar, "🚑  TROUBLESHOOT", fg=RED,
                                       border="#8a3a2e", hover="#3a2622",
                                       command=self._open_troubleshoot)
        self.trouble_btn.pack(side="left", padx=(8, 0))

        # --- Activity feed ---
        # height=8: request few rows so the teach bar below always fits; expand=True
        # grows the feed to fill whatever space the window actually has.
        def build_feed(parent):
            inner = tk.Frame(parent, bg=PANEL)
            self.feed = tk.Text(inner, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                                relief="flat", wrap="word", font=self.mono, height=8,
                                padx=10, pady=8, cursor="arrow", state="disabled")
            style = ttk.Style(self.root)
            style.theme_use("clam")  # the only built-in theme that honors scrollbar colors
            style.configure("Cobb.Vertical.TScrollbar", background="#34455a",
                            troughcolor=PANEL, bordercolor=PANEL, lightcolor="#34455a",
                            darkcolor="#34455a", arrowcolor=PANEL, relief="flat",
                            width=26, arrowsize=0)
            style.map("Cobb.Vertical.TScrollbar",
                      background=[("active", "#3a4c5e"), ("pressed", "#46596d")])
            scroll = ttk.Scrollbar(inner, command=self.feed.yview,
                                   style="Cobb.Vertical.TScrollbar")
            self.feed.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            self.feed.pack(fill="both", expand=True)
            return inner

        # --- Voice trainer panel (hidden until 🎯 is clicked) ---
        def build_trainer(parent):
            inner = tk.Frame(parent, bg=PANEL)
            top = tk.Frame(inner, bg=PANEL)
            top.pack(fill="x", padx=10, pady=(6, 0))
            tk.Label(top, text="Say (on your talk button):", bg=PANEL, fg=DIM,
                     font=("Segoe UI", 9)).pack(side="left")
            self.tr_progress = tk.Label(top, text="", bg=PANEL, fg=DIM,
                                        font=("Segoe UI", 9))
            self.tr_progress.pack(side="right")
            self.tr_phrase = tk.Label(inner, text="", bg=PANEL, fg=AMBER,
                                      font=("Consolas", 15, "bold"), anchor="w")
            self.tr_phrase.pack(fill="x", padx=10, pady=(2, 2))
            self.tr_result = tk.Label(inner, text="ready when you are — hold PTT and speak",
                                      bg=PANEL, fg=DIM, font=("Segoe UI", 10), anchor="w")
            self.tr_result.pack(fill="x", padx=10, pady=(0, 4))
            row = tk.Frame(inner, bg=PANEL)
            row.pack(fill="x", padx=6, pady=(0, 6))
            self.tr_teach_btn = RoundButton(row, "TEACH FIX", fg=GREEN, border="#3a6b4d",
                                            command=self._tr_teach_fix,
                                            font=("Segoe UI", 9, "bold"), pad_x=12, pad_y=4)
            self.tr_skip_btn = RoundButton(row, "SKIP ▸", fg=BLUE, border="#3d5a7a",
                                           command=self._tr_next,
                                           font=("Segoe UI", 9, "bold"), pad_x=12, pad_y=4)
            self.tr_end_btn = RoundButton(row, "END", fg=RED, border="#6b3a33",
                                          command=self._toggle_trainer,
                                          font=("Segoe UI", 9, "bold"), pad_x=12, pad_y=4)
            self.tr_skip_btn.pack(side="left", padx=(4, 6))
            self.tr_end_btn.pack(side="left")
            # TEACH FIX only appears after a miss
            return inner

        self.trainer_box = RoundBox(self.root, build_trainer, fill=PANEL,
                                    border="#3a6b4d", padding=6, radius=14)
        # not packed yet — _toggle_trainer shows it

        feed_box = RoundBox(self.root, build_feed, fill=PANEL, border="#2e3946",
                            padding=8, radius=14)
        feed_box.pack(fill="both", expand=True, padx=16, pady=(10, 8))
        self._feed_box = feed_box
        for tag, color in (("dim", DIM), ("green", GREEN), ("amber", AMBER),
                           ("red", RED), ("blue", BLUE), ("text", TEXT)):
            self.feed.tag_configure(tag, foreground=color)
        self.feed.tag_configure("heard", foreground=BLUE, underline=False)
        self.feed.tag_configure("why", foreground=BLUE, underline=True)
        self.feed.tag_bind("why", "<Button-1>", lambda e: self._open_troubleshoot())
        self.feed.tag_bind("why", "<Enter>", lambda e: self.feed.configure(cursor="hand2"))
        self.feed.tag_bind("why", "<Leave>", lambda e: self.feed.configure(cursor="arrow"))
        # release (not press) so drag-selecting words in a heard line still works
        self.feed.tag_bind("heard", "<ButtonRelease-1>", self._click_word)
        self.feed.tag_bind("heard", "<Enter>", lambda e: self.feed.configure(cursor="hand2"))
        self.feed.tag_bind("heard", "<Leave>", lambda e: self.feed.configure(cursor="arrow"))
        self.feed.bind("<Button-3>", self._feed_menu)

        # --- Teach-a-word panel ---
        teach = tk.Frame(self.root, bg=PANEL)
        teach.pack(fill="x", padx=16, pady=(0, 6))
        tk.Label(teach,
                 text="Teach it — click a wrong word in a blue line (or drag across two words to fix a phrase), or type here:",
                 bg=PANEL, fg=DIM, anchor="w", font=("Segoe UI", 9)).grid(
                 row=0, column=0, columnspan=4, sticky="we", padx=10, pady=(6, 2))
        entry_font = tkfont.Font(family="Consolas", size=10)
        tk.Label(teach, text="It heard", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).grid(row=1, column=0, padx=(10, 6), pady=(0, 12))
        def build_entry(parent):
            return tk.Entry(parent, bg=FIELD, fg=TEXT, insertbackground=TEXT,
                            relief="flat", font=entry_font, bd=0)

        wrong_box = RoundBox(teach, build_entry, fill=FIELD, border="#34455a",
                             focus_border=BLUE, padding=6, radius=10, height=34)
        wrong_box.grid(row=1, column=1, sticky="we", padx=4, pady=(0, 8))
        self.wrong_entry = wrong_box.child
        tk.Label(teach, text="should be", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10)).grid(row=1, column=2, padx=6, pady=(0, 12))
        right_box = RoundBox(teach, build_entry, fill=FIELD, border="#34455a",
                             focus_border=BLUE, padding=6, radius=10, height=34)
        right_box.grid(row=1, column=3, sticky="we", padx=4, pady=(0, 8))
        self.right_entry = right_box.child
        self.add_btn = RoundButton(teach, "Add", fg=GREEN, border="#3a6b4d",
                                   command=self._teach, hover="#243b2e",
                                   font=("Segoe UI", 10, "bold"), pad_x=18, pad_y=5)
        self.add_btn.grid(row=1, column=4, padx=(6, 10), pady=(0, 8))
        teach.grid_columnconfigure(1, weight=1)
        teach.grid_columnconfigure(3, weight=1)
        self.right_entry.bind("<Return>", lambda e: self._teach())

        # --- 🔗 VoiceAttack link (off = the two apps live their own lives) ---
        self.valink_var = tk.BooleanVar(value=bool(valink_on))
        valink_row = tk.Frame(self.root, bg=BG)
        valink_row.pack(fill="x", padx=16, pady=(0, 10))
        tk.Checkbutton(
            valink_row,
            text="🔗 Start & close VoiceAttack together with CobbAttack",
            variable=self.valink_var, command=self._valink_toggled,
            bg=BG, fg=DIM, activebackground=BG, activeforeground=TEXT,
            selectcolor=FIELD, highlightthickness=0, bd=0, anchor="w",
            font=("Segoe UI", 9)).pack(side="left")

        self.root.after(100, self._drain)

    def _valink_toggled(self):
        self.on_valink(self.valink_var.get())

    @staticmethod
    def _draw_retro_title(parent):
        # 1980s-arcade wordmark: italic chunky letters, neon color cycle per letter,
        # magenta-to-purple 3D extrusion.
        text = "COBBATTACK"
        font = ("Impact", 22, "italic")
        f = tkfont.Font(family="Impact", size=22, slant="italic")
        # gradient swept across the word in theme colors: pale corn gold -> amber
        stops = [(255, 217, 122), (242, 193, 78), (232, 160, 75)]

        def sweep(t):
            seg = min(int(t * (len(stops) - 1)), len(stops) - 2)
            lo, hi = stops[seg], stops[seg + 1]
            k = t * (len(stops) - 1) - seg
            return "#%02x%02x%02x" % tuple(
                round(a + (b - a) * k) for a, b in zip(lo, hi))

        w = f.measure(text) + 24
        c = tk.Canvas(parent, width=w, height=42, bg=BG, highlightthickness=0)
        c.pack(side="left")
        x = 6
        for idx, ch in enumerate(text):
            for i in range(5, 0, -1):  # extruded shadow, back to front
                shade = "#10141a" if i > 3 else "#2e3f52"
                c.create_text(x + i, 8 + i, text=ch, font=font, fill=shade, anchor="nw")
            c.create_text(x, 8, text=ch, font=font,
                          fill=sweep(idx / (len(text) - 1)), anchor="nw")
            x += f.measure(ch)

    @staticmethod
    def _draw_hero(c):
        # Tiny flying superhero with shades — drawn with shapes so it renders
        # identically everywhere (tk emoji support is unreliable on Windows).
        c.create_line(2, 8, 13, 8, fill=DIM)                                    # speed lines
        c.create_line(0, 14, 11, 14, fill=DIM)
        c.create_line(2, 20, 13, 20, fill=DIM)
        c.create_polygon(16, 10, 7, 4, 13, 15, 7, 26, 16, 20, fill="#d05a4a")   # cape
        c.create_polygon(12, 17, 23, 13, 23, 20, 12, 24, fill="#3a6ea8")        # legs
        c.create_rectangle(17, 10, 31, 20, fill=BLUE, outline="")               # torso
        c.create_oval(29, 4, 40, 15, fill="#f0c29a", outline="")                # head
        c.create_rectangle(31, 7, 39, 10, fill="#101418", outline="")           # shades
        c.create_rectangle(34, 7, 35, 10, fill="#2a333e", outline="")           # bridge
        c.create_rectangle(31, 18, 44, 21, fill="#f0c29a", outline="")          # arm out front
        c.create_oval(43, 17, 48, 22, fill="#f0c29a", outline="")               # fist
        c.create_polygon(17, 10, 17, 20, 13, 15, fill="#4b90c8")                # shoulder shade

    def _darken_title_bar(self):
        # Windows 10 1809+ immersive dark mode for the title bar; harmless no-op
        # elsewhere. Attribute 20 on current builds, 19 on older ones.
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1)
            for attr in (20, 19):
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                ) == 0:
                    break
            # Windows 11: paint the caption in the exact theme color (COLORREF is
            # 0x00BBGGRR — BG "#14181d" → 0x1d1814) and match the title text.
            caption = ctypes.c_int(0x1D1814)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption), 4)
            text = ctypes.c_int(0xE3DDD7)  # TEXT "#d7dde3"
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(text), 4)
            # Nudge Windows to repaint the frame with the new attributes.
            self.root.withdraw()
            self.root.deiconify()
        except Exception:
            pass

    # ---- called from any thread ----
    def post(self, kind, **data):
        self.events.put((kind, data))

    # ---- Tk-thread only ----
    def _drain(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                getattr(self, f"_ev_{kind}", lambda **k: None)(**data)
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _ev_state(self, state):
        text, color = STATE_STYLES.get(state, ("● …", DIM))
        self.state_label.configure(text=text, fg=color)

    def _ev_device(self, line):
        self.device_label.configure(text=line)
        self._device_line = line
        on_gpu = "GPU" in line and "no GPU" not in line
        self._append([("engine: ", "dim"), (line + "\n", "green" if on_gpu else "amber")])

    def _ev_learned_dup(self, wrong, right):
        self._append([("learned ", "dim"),
                      (f"“{wrong}” → “{right}” was already taught — it's active\n",
                       "amber")])

    def _ev_profile(self, count):
        if count > 0:
            self._append([("profile ", "dim"),
                          (f"imported — {count} of your commands now pass the filter\n",
                           "green")])
        else:
            self._append([("profile ", "dim"),
                          ("imported, but no custom commands found in it\n", "amber")])

    def _ev_heard(self, raw, ms):
        self._append([("heard  ", "dim"), (raw, "heard"), (f"   ({ms:.0f} ms)\n", "dim")])

    def _ev_sent(self, text, total_ms):
        self._append([("sent   ", "dim"), (text, "green"), (f"   ({total_ms:.0f} ms total)\n", "dim")])

    def _ev_dropped(self, reason):
        self._append([("       ", "dim"), (reason + "\n", "amber")])

    # Why-lines for a refused call. Deliberately loud: the old feed said
    # "dropped — silence/noise" for every cause, which explained nothing.
    REJECT_DETAIL = {
        "blank": "there was no speech in that clip — check your microphone",
        "hallucination": "that was silence, not words — check your microphone",
        "too_short": "the talk button was released too fast",
    }

    def _ev_rejected(self, reason, raw="", cleaned="", best=None, score=0,
                     threshold=85):
        if reason == "no_match":
            detail = f"nothing in your profile matches “{cleaned or raw}”"
            if best:
                detail += f"  ·  closest: “{best}” {score}/{threshold}"
        else:
            detail = self.REJECT_DETAIL.get(reason, "refused by the safety filter")
        self._append([("       ", "dim"),
                      ("✗  NOT A COMMAND — nothing sent\n", "red"),
                      ("       ", "dim"), (detail + "  ", "amber"),
                      ("why?\n", "blue")])
        # tag the trailing "why?" so clicking it opens the troubleshoot page
        # ("why?\n" = 5 chars back from the end of the inserted text)
        self.feed.configure(state="normal")
        self.feed.tag_add("why", "end-1c -5c", "end-1c -1c")
        self.feed.configure(state="disabled")
        winsound.MessageBeep(winsound.MB_ICONHAND)

    def _ev_error(self, message):
        self._append([("error  ", "red"), (message + "\n", "red")])

    def _ev_learned(self, wrong, right):
        self._append([("learned ", "dim"), (f"“{wrong}” → “{right}”\n", "blue")])

    # ---- voice trainer ----
    def _toggle_trainer(self):
        if self._tr_active:
            self._tr_finish()
            return
        if not self.practice_phrases:
            self._append([("trainer ", "dim"),
                          ("no command list yet — do the “Teach it” setup step first\n", "amber")])
            return
        self._tr_active = True
        self._tr_i = 0
        self._tr_hits = 0
        self._tr_taught = 0
        self._tr_joked = False
        self._tr_joke_mode = False
        self.on_practice(True)
        self.trainer_box.pack(fill="x", padx=16, pady=(10, 0),
                              before=self._feed_box)
        self._append([("trainer ", "dim"),
                      ("started — say each phrase on your talk button; "
                       "nothing is sent to VoiceAttack\n", "green")])
        self._tr_show()

    TR_JOKE = "Kirk's kneeboard is just DoorDash receipts"

    def _tr_show(self):
        # one-off bonus round two-thirds in: you have to SAY it, but it never
        # counts — not scored, not teachable, not sent anywhere
        if (not self._tr_joked
                and self._tr_i == (2 * len(self.practice_phrases)) // 3):
            self._tr_joke_mode = True
            self.tr_phrase.configure(text=f"“{self.TR_JOKE}”")
            self.tr_progress.configure(text="bonus round 🌯")
            self.tr_result.configure(text="ready when you are — hold PTT and speak",
                                     fg=DIM)
            self.tr_teach_btn.pack_forget()
            self._tr_last_raw = None
            return
        target = self.practice_phrases[self._tr_i]
        self.tr_phrase.configure(text=f"“{target}”")
        self.tr_progress.configure(text=f"{self._tr_i + 1} / {len(self.practice_phrases)}")
        self.tr_result.configure(text="ready when you are — hold PTT and speak", fg=DIM)
        self.tr_teach_btn.pack_forget()
        self._tr_last_raw = None

    def _tr_joke_done(self):
        if not self._tr_active:
            return
        self._tr_joked = True
        self._tr_joke_mode = False
        self._tr_show()

    def _tr_next(self):
        if not self._tr_active:
            return
        if self._tr_joke_mode:  # skipping the gag just reveals the real phrase
            self._tr_joke_done()
            return
        self._tr_i += 1
        if self._tr_i >= len(self.practice_phrases):
            self._tr_finish()
        else:
            self._tr_show()

    def _tr_finish(self):
        self._tr_active = False
        self.on_practice(False)
        self.trainer_box.pack_forget()
        done = min(self._tr_i, len(self.practice_phrases))
        if done:
            self._append([
                ("trainer ", "dim"),
                (f"done — {self._tr_hits}/{done} heard right first try, "
                 f"{self._tr_taught} fix(es) taught\n", "green")])

    def _ev_practice(self, raw, text):
        if not self._tr_active:
            return
        if self._tr_joke_mode:
            self.tr_result.configure(text="so true :)", fg=AMBER)
            self.tr_teach_btn.pack_forget()
            self.root.after(2600, self._tr_joke_done)
            return
        target = self.practice_phrases[self._tr_i]
        cleaned = re.sub(r"[^\w\s'-]", " ", raw.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        heard = f"heard: “{raw.strip()}”"
        if cleaned == target:
            # word-perfect: no mappings or fuzzy rescue needed
            self._tr_hits += 1
            self.tr_result.configure(text=f"✓  perfect — {heard}", fg=GREEN)
            self.tr_teach_btn.pack_forget()
            self.root.after(900, self._tr_next)
        elif text == target:
            # it worked, but only because the firewall/word-fixes rescued it
            self.tr_result.configure(
                text=f"◐  close enough (auto-corrected) — {heard}", fg=AMBER)
            self.tr_teach_btn.pack_forget()
            self.root.after(1400, self._tr_next)
        else:
            self.tr_result.configure(text=f"✗  {heard} — say it again, or teach the fix",
                                     fg=RED)
            self._tr_last_raw = raw
            self.tr_teach_btn.pack(side="left", padx=(4, 6),
                                   before=self.tr_skip_btn)

    def _tr_teach_fix(self):
        if not self._tr_last_raw:
            return
        target = self.practice_phrases[self._tr_i]
        wrong = re.sub(r"[^\w\s'-]", " ", self._tr_last_raw.lower())
        wrong = re.sub(r"\s+", " ", wrong).strip()
        if wrong and self.on_teach(wrong, target):
            self._tr_taught += 1
        self._tr_next()

    def _feed_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                       activebackground="#243b2e", activeforeground=TEXT,
                       relief="flat", bd=0)
        sel = ""
        if self.feed.tag_ranges("sel"):
            sel = self.feed.get("sel.first", "sel.last")
            sel = re.sub(r"[^\w\s'-]", " ", sel.lower())
            sel = re.sub(r"\s+", " ", sel).strip()
        if sel:
            label = sel if len(sel) <= 40 else sel[:37] + "…"
            menu.add_command(label=f"Teach fix for “{label}”",
                             command=lambda: self._teach_selection(sel))
            menu.add_command(label="Copy", command=lambda: self._copy_text(sel))
            menu.add_separator()
        if self._teach_history and self.on_unteach:
            w, r = self._teach_history[-1]
            undo_label = f"{w} → {r}"
            if len(undo_label) > 40:
                undo_label = undo_label[:37] + "…"
            menu.add_command(label=f"Undo fix “{undo_label}”",
                             command=self._undo_teach)
            menu.add_separator()
        menu.add_command(label="Clear window", command=self._clear_feed)
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _teach_selection(self, sel):
        self.wrong_entry.delete(0, "end")
        self.wrong_entry.insert(0, sel)
        self.right_entry.delete(0, "end")
        self.right_entry.focus_set()

    def _copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _clear_feed(self):
        self.feed.configure(state="normal")
        self.feed.delete("1.0", "end")
        self.feed.configure(state="disabled")
        # fresh feed still shows what engine we're on, same as at startup
        line = getattr(self, "_device_line", None)
        if line:
            on_gpu = "GPU" in line and "no GPU" not in line
            self._append([("engine: ", "dim"),
                          (line + "\n", "green" if on_gpu else "amber")])

    def _append(self, parts):
        self.feed.configure(state="normal")
        for text, tag in parts:
            self.feed.insert("end", text, tag)
        self.feed.configure(state="disabled")
        self.feed.see("end")

    def _click_word(self, event):
        if self.feed.tag_ranges("sel"):
            # drag-selected words go straight into the teach box
            phrase = re.sub(r"[^\w\s'-]", " ",
                            self.feed.get("sel.first", "sel.last").lower())
            phrase = re.sub(r"\s+", " ", phrase).strip()
            if phrase:
                self._teach_selection(phrase)
            return "break"
        start = self.feed.index(f"@{event.x},{event.y} wordstart")
        end = self.feed.index(f"@{event.x},{event.y} wordend")
        # Shift+click: grab everything from the previously clicked word through
        # this one ("boat key" → teach box as one phrase to fix)
        if (event.state & 0x0001) and self._last_click:
            s0, e0 = self._last_click
            first = s0 if self.feed.compare(s0, "<", start) else start
            last = end if self.feed.compare(e0, ">", end) else e0
            phrase = re.sub(r"[^\w\s'-]", " ", self.feed.get(first, last).lower())
            phrase = re.sub(r"\s+", " ", phrase).strip()
            self._last_click = None
            self._close_popup()
            if phrase:
                self._teach_selection(phrase)
            return "break"
        self._last_click = (start, end)
        word = self.feed.get(start, end).strip().lower()
        word = "".join(ch for ch in word if ch.isalnum() or ch in "'-")
        if word:
            self._show_popup(word, event.x_root, event.y_root)
        return "break"

    def _show_popup(self, word, x, y):
        self._close_popup()
        pop = self._popup = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.configure(bg=FIELD, padx=1, pady=1)
        inner = tk.Frame(pop, bg=PANEL)
        inner.pack(fill="both", expand=True)
        title = tk.Frame(inner, bg=PANEL)
        title.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(title, text=f"“{word}” should be:", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Button(title, text="✕", command=self._close_popup, relief="flat",
                  bg=PANEL, fg=DIM, activebackground=PANEL, activeforeground=TEXT,
                  bd=0, cursor="hand2", font=("Segoe UI", 9)).pack(side="right")

        def teach(right):
            if self.on_teach(word, right):
                self._close_popup()

        suggestions = self.on_suggest(word)
        if suggestions:
            row = tk.Frame(inner, bg=PANEL)
            row.pack(anchor="w", padx=12, pady=(0, 4))
            for s in suggestions:
                tk.Button(row, text=s, command=lambda s=s: teach(s), relief="flat",
                          bg=FIELD, fg=BLUE, activebackground=BG, activeforeground=BLUE,
                          font=self.mono, cursor="hand2", bd=0, padx=8, pady=3
                          ).pack(side="left", padx=(0, 6))

        entry_row = tk.Frame(inner, bg=PANEL)
        entry_row.pack(fill="x", padx=12, pady=(2, 10))
        entry = tk.Entry(entry_row, bg=FIELD, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=self.mono, width=18)
        entry.pack(side="left", ipady=4)
        tk.Button(entry_row, text=" Add ", command=lambda: teach(entry.get()), relief="flat",
                  bg=GREEN, fg="#10301e", activebackground="#79dfa4",
                  activeforeground="#10301e", font=("Segoe UI", 9, "bold"),
                  cursor="hand2", bd=0).pack(side="left", padx=(6, 0))
        entry.bind("<Return>", lambda e: teach(entry.get()))
        entry.bind("<Escape>", lambda e: self._close_popup())

        pop.geometry(f"+{x + 8}+{y + 10}")
        pop.update_idletasks()
        pop.lift()
        pop.attributes("-topmost", True)
        entry.focus_force()

    def on_teach(self, wrong, right):
        """All teach paths funnel through here so undo knows what was taught."""
        ok = self._on_teach_cb(wrong, right)
        if ok:
            self._teach_history.append(
                (re.sub(r"\s+", " ", wrong.strip().lower()),
                 re.sub(r"\s+", " ", right.strip().lower())))
        return ok

    def _undo_teach(self):
        if not self._teach_history:
            return
        wrong, right = self._teach_history.pop()
        if self.on_unteach and self.on_unteach(wrong, right):
            self._append([("unlearned ", "dim"),
                          (f"“{wrong}” → “{right}” removed\n", "amber")])
        else:
            self._append([("unlearned ", "dim"),
                          ("that fix was already gone\n", "amber")])

    def _close_popup(self):
        if self._popup is not None:
            self._popup.destroy()
            self._popup = None

    def _teach(self):
        wrong = self.wrong_entry.get()
        right = self.right_entry.get()
        if self.on_teach(wrong, right):
            self.wrong_entry.delete(0, "end")
            self.right_entry.delete(0, "end")

    def _open_cheatsheet(self):
        path = os.path.join(config.ROOT, "commands-cheatsheet.html")
        if os.path.exists(path):
            webbrowser.open(path)
        else:
            self.post("error", message="no cheat sheet yet — run tools\\make_cheatsheet.py")

    def _open_setup(self):
        path = os.path.join(config.ROOT, "Setup-Instruction.html")
        if os.path.exists(path):
            webbrowser.open(path)
        else:
            self.post("error", message="no setup manual yet — run tools\\make_setup.py")

    def _open_troubleshoot(self):
        if self.on_troubleshoot is None:
            return
        try:
            path = self.on_troubleshoot()
        except Exception as e:  # a diagnostics page must never take the app down
            self.post("error", message=f"troubleshoot page failed: {e}")
            return
        self._append([("       ", "dim"),
                      ("troubleshoot page opened in your browser\n", "dim")])
        webbrowser.open(path)

    # ---- minimize to tray ----
    def _on_unmap(self, event):
        if event.widget is not self.root or self._hidden:
            return
        if self.root.state() != "iconic":
            return
        if self.tray.show_icon():
            self._hidden = True
            self.root.withdraw()  # off the taskbar; the tray icon is the way back

    def _restore(self):
        self._hidden = False
        self.tray.hide_icon()
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def _close(self):
        self.tray.stop()
        self.on_close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
