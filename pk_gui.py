from __future__ import print_function

import re
import threading
import tkinter as tk
# from collections.abc import MutableMapping
from json import dumps, loads
from os import startfile, environ, listdir
from os.path import exists, join
from random import randint, seed, choice, shuffle
from sys import argv, stdin, stdout, stderr
from tkinter import messagebox as msgbox
from tkinter import ttk
from tkinter.constants import *
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc
from typing import Sequence, Callable, Set, Mapping

import pystray
import time
from PIL import Image

import pk
import simple_tools as st
from pk_misc import help_text, TITLE, resource_path


def get_center(cls: tk.Tk | tk.Toplevel):
    """获取特定窗口相对当前屏幕的中心位置坐标

    @param cls: “特定窗口”，该窗口的大小
    @return: 字符串，+dd+dd 格式
    """
    xOy = "+%d+%d" % (
        (cls.winfo_screenwidth() - cls.winfo_width()) // 2, (cls.winfo_screenheight() - cls.winfo_height()) // 2)
    cls.geometry(xOy)
    return xOy


class CascadeMenu(tk.Menu):
    def __init__(self, menuName):
        super().__init__()

        self.name = menuName
        self.deep = 0
        self.__children = []
        self.parent = None

    def __add_submenu_internal(self, subMenu):
        assert isinstance(subMenu, CascadeMenu)
        subMenu.deep = self.deep + 1
        subMenu.parent = self
        if subMenu not in self.__children:
            self.__children.append(subMenu)
            for node in subMenu.__children:
                CascadeMenu.__add_submenu_internal(subMenu, node)

            return subMenu

    def add_submenu(self, menu_name):
        return self.__add_submenu_internal(CascadeMenu(menu_name))

    def pack_menu(self):
        pass


class Treasure(tk.Tk):
    DEFAULT_K_ENABLED_CONFIG = {
        "msgbox": True, "commandLine": True, "commandBox": True, "sysTerminal": True, "window_dance": True
    }

    def __init__(self):
        super().__init__()

        self.ISDIGIT_FX = self.register(str.isdigit)
        self.SIDE2SIDE = self.register(  # 实际上无法使用，因为 register 封装后，函数就变成了 str
            lambda __d, x=None, y=None: (str.isdigit(__d) and (x is None or x <= __d) and (y is None or __d < y)))
        self.k_enabled = self.__class__.DEFAULT_K_ENABLED_CONFIG

    def get_digit_entry(self, win, cls, **kwargs):
        kwargs_copy: dict = kwargs
        # kwargs_copy.update(validate='key', validatecommand=(
        #     lambda __x: self.SIDE2SIDE(__x, kwargs.get("min", None), kwargs.get("max", None)), "%P"))
        kwargs_copy.update(validate="key", validatecommand=(self.ISDIGIT_FX, "%P"))
        return cls(win, **kwargs_copy)

    def get_side2side_entry(self, win, cls, min_=None, max_=None, **kwargs):
        side2side_fx = self.register(
            lambda __d: (str.isdigit(__d) and (min_ is None or min_ <= int(__d)) and (max_ is None or int(__d) < max_)))
        kwargs_copy = kwargs
        kwargs_copy.update(validate="key", validatecommand=(side2side_fx, "%P"))
        if "min_" in kwargs_copy.keys():
            kwargs_copy.pop("min_")
        if "max_" in kwargs_copy.keys():
            kwargs_copy.pop("max_")
        return cls(win, **kwargs_copy)


class SyncThread(threading.Thread):
    def run(self):
        print("{} started!".format(self.name))
        time.sleep(3)
        print("{} finished!".format(self.name))


class PeekerGui(pk.Peeker, Treasure):
    """为主程序提供 GUI 支持


    Attributes:
        log_list = []
        user_history = {}
        warnings = {}
        topmost = tk.BooleanVar()
        take_focus = tk.BooleanVar()
        show_terminal_warning = tk.BooleanVar()
        log_scroll2end = tk.BooleanVar()
        at_admin_var = tk.StringVar()
        log_insert_mode = tk.StringVar()
        alpha_mode = tk.IntVar()
        theme = tk.StringVar()
        disabledWhenSubWindow = tk.BooleanVar()
        OnQuit = tk.IntVar()  # 0 = 询问，1 = 最小化到托盘，2 = 退出
        truncateTooLongStrings = tk.StringVar()
    """

    GLOBAL_PADX = 10
    GLOBAL_PADY = 5
    TITLE = TITLE
    CONF_FILE_TYPES = ((f"{TITLE} 配置文件", "*.sc_conf"), ("json 文件", "*.json"), ("所有类型的文件", '*'))

    ICON_FP = resource_path("assets/icon.ico")
    WARNING_FP = resource_path("assets/SecurityAndMaintenance_Alert_Resize.png")
    ERROR_FP = resource_path("assets/SecurityAndMaintenance_Error_Resize.png")
    INFO_FP = resource_path("assets/SecurityAndMaintenance_Resize.png")
    QUESTION_FP = resource_path("assets/grequest.gif")

    LOG_COLORS = {
        pk.Peeker.LOG_INFO: "black",
        pk.Peeker.LOG_WARNING: "#C19C00",
        pk.Peeker.LOG_ERROR: "red",
        pk.Peeker.LOG_DEBUG: "green"
    }

    debug = False
    COLOR = ("red", "yellow", "green", "blue", "black", "brown", "white", "orange", "purple", "pink")
    TODAY_QUOTE = (
        (0, "，:("),
        (20, "，呜……"),
        (40, "，勉强还行吧……"),
        (60, "，还好啦，还好啦"),
        (80, "，今天运气不错呢！"),
        (90, "!!!"),
        (100, "！100！100！！！！！"),
    )
    BUTTON_STYLE_USE = "TButton"
    LABEL_STYLE_USE = "TLabel"
    MENU_STYLE_USE = "TMenu"
    COMBOBOX_STYLE_USE = "TCombobox"
    ENTRY_STYLE_USE = "TEntry"

    STYLES = {
        "style1":
            {
                BUTTON_STYLE_USE: {
                    "foreground": "red",
                    # "background": "black",

                },
                LABEL_STYLE_USE: {
                    "foreground": "red",
                    "activebackground": "red",
                },
                MENU_STYLE_USE: {
                    "foreground": "red",
                    # "background": "red",
                },
                COMBOBOX_STYLE_USE: {
                    # "foreground": "red",
                    # "background": "red",
                    "selectbackground": "red"
                },
                ENTRY_STYLE_USE: {
                    "selectbackground": "red"
                }
            },
        "style2":
            {
                BUTTON_STYLE_USE: {
                    "foreground": "green",
                    "background": "blue",
                },
                LABEL_STYLE_USE: {
                    "foreground": "blue",
                    "background": "yellow",
                }
            },
        "debug_style":
            {
                BUTTON_STYLE_USE: {
                    "foreground": "red",
                    "background": "red",
                },
                LABEL_STYLE_USE: {
                    "foreground": "red",
                    "background": "red",
                }
            },
    }

    # def __del__(self):
    #     super().__del__()
    #     self.record_fx("删除实例")

    def __init__(self, syncRoot_fp):
        super().__init__(syncRoot_fp)
        self.record_fx = self.record_register
        self.wait_fx = self.wait2

        self.log_list: list = []
        self.user_history: dict = {}
        self.warnings: dict = {}
        self.topmost = tk.BooleanVar()
        self.take_focus = tk.BooleanVar()
        self.show_terminal_warning = tk.BooleanVar()
        self.log_scroll2end = tk.BooleanVar()
        self.at_admin_var = tk.StringVar()
        self.log_insert_mode = tk.StringVar()
        self.alpha_mode = tk.IntVar()
        self.theme = tk.StringVar()
        self.disabledWhenSubWindow = tk.BooleanVar()
        self.OnQuit = tk.IntVar()  # 0 = 询问，1 = 最小化到托盘，2 = 退出
        self.truncateTooLongStrings = tk.StringVar()

        self.KEY_BOARD: dict[str: tuple[str, str, str, Callable]] = {
            "refresh": ("<F5>", "F5", "刷新", lambda x=None: self.refresh(),),
            "terminate": ("<Control-Alt-F2>", "Ctrl+Alt+F2", "强行终止", lambda x=None: self.join_cmdline(
                lambda: self.destroy(), lambda: pk.sys_exit(-1))()),
            "exit": (
                "<Control-F4>", "Ctrl+F4", "放弃保存并退出", lambda x=None: self.gui_destroy(True, save=False)),
            "save_exit": (
                "<Control-q>", "Ctrl+Q", "保存并退出", lambda x=None: self.gui_destroy(True, save=True)),
            "check_admin": (
                "<Alt-c>", "Alt+C", "检查管理员权限", lambda x=None: self.gui_get_admin(take=False, quiet=False)),
            "take_admin": ("<Alt-KeyRelease-s>", "Alt+S", "以管理员身份运行",
                           lambda x=None: self.gui_get_admin(take=True, quiet=False)),
            "save": ("<Control-s>", "Ctrl+S", "保存", lambda x=None: self.save(ren=False)),
            "save_arc": ("<Control-Shift-S>", "Ctrl+Shift+S", "保存 & 归档", lambda x=None: self.save(ren=True)),
            "minify": ("<Alt-KeyRelease-n>", "Alt+N", "最小化窗口", lambda x=None: self.iconify()),
            "hide_gui": ("<Alt-KeyRelease-h>", "Alt+H", "最小化到系统托盘", lambda x=None: self.withdraw()),
            # "maxify": ("<Alt-m>", "Alt+M", "还原窗口", lambda x=None: self.deiconify()),
            "preset0": ("<Alt-KeyRelease-1>", "Alt+1", "预设：forever", lambda x=None: self.warn_nowindow(True, False)),
            "preset1": ("<Alt-KeyRelease-2>", "Alt+2", "预设：3600times", lambda x=None: self.warn_nowindow(
                True, False, figure=3600)),
            "shut": ("<Shift-Q>", "Shift+Q", "清除同步状态", lambda x=None: self.shut()),
            "terminated_sync": ("<Control-l>", "Ctrl+L", "终止正在进行的同步", lambda x=None: self.terminate_sync()),
            "reset_warnings": ("<Control-KeyRelease-2>", "Ctrl+2", "重置所有警告", lambda x=None: self.gui_clear_list(
                self.warnings, "重置所有警告. . . 完成！")),
        }
        self.gui_live = True
        self.log_scroll2end.set(True)
        print(self.log_scroll2end.get())

        # 以下的赋值并不重要，具体可参考 Peeker 的  __init__ 函数末尾和 extract_config() 函数
        # null
        # 以上
        if PeekerGui.debug:
            self.log_box_color = "red"
            self.sync_box_color = "red"
        else:
            self.log_box_color = "black"
            self.sync_box_color = "black"

        self.iconbitmap(self.ICON_FP)
        self.title(self.TITLE + "（测试版本）" if PeekerGui.debug else self.TITLE)
        self.minsize(600, 420)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: self.gui_destroy(None, slide=True, save=True))
        self.attributes("-topmost", self.topmost.get())

        self.logBox_Listbox = tk.Listbox(self, width=40, height=20, takefocus=False, selectmode=BROWSE,
                                         fg=self.log_box_color)
        self.logBox_Text = tk.Text(self, width=40, height=27, takefocus=False, fg=self.log_box_color, wrap=NONE)
        self.log_box = self.logBox_Text

        self.log_scroll_Y = ttk.Scrollbar(self, command=self.log_box.yview, orient=VERTICAL, takefocus=False)
        self.log_scroll_X = ttk.Scrollbar(self, command=self.log_box.xview, orient=HORIZONTAL, takefocus=False)
        self.sync_box = tk.Listbox(self, width=35, height=11, takefocus=True, selectmode=BROWSE,
                                   fg=self.sync_box_color)
        self.sync_scroll = ttk.Scrollbar(self, command=self.sync_box.yview, orient=VERTICAL, takefocus=False)
        self.menu_bar = tk.Menu(self, tearoff=False)

        self.config(menu=self.menu_bar)
        self.log_box.config(yscrollcommand=self.log_scroll_Y.set, xscrollcommand=self.log_scroll_X.set, state=NORMAL)
        self.sync_box.config(yscrollcommand=self.sync_scroll.set, state=NORMAL)

        # self.extract_config()

        self.global_style = ttk.Style(self)
        self.button_style = ttk.Style(self)
        self.button_style.configure(self.BUTTON_STYLE_USE, **self.STYLES["style2"][self.BUTTON_STYLE_USE])

    def wait2(self, seconds: float | int, quiet=True):
        if not quiet:
            self.record_fx(f"wait2 等待 {seconds} 秒")
        # for i in range(int(elapsed_ms)):
        #     st.wait(0.001, busy_loop=True)
        #     # self.after(1)
        #     self.update()
        elif self.wait_busy_loop or (self.wait_busy_loop is None and seconds <= 0.1):
            elapsed = time.time() + seconds
            while time.time() < elapsed:
                st.wait(0.05, busy_loop=True)
                # self.update_idletasks()
                self.update()
        else:
            # time.sleep(seconds)
            self.after(int(seconds * 1000))

    def setup(self):
        super().setup()
        self.record_fx("接收参数", argv)
        self.record_fx("窗口定位", get_center(self))
        self.topmost_tm(self, None, True)
        self.record_fx("已装载", len(self.global_style.theme_names()), "个主题")
        self.record_fx(", ".join(self.global_style.theme_names()))
        self.global_style.theme_use(self.theme.get() if self.theme.get() else "vista")

    def record_register_old(self, *text, sep=" ", end="\n"):
        """DEPRECATED"""
        self.record_ln(*text, sep=sep, end=end)
        text_1 = f"[{time.strftime('%H:%M:%S', time.localtime(time.time()))}]{sep.join(map(str, text))}"
        self.log_list.append(text_1)
        try:
            if self.gui_live:
                self.log_box.insert(self.log_insert_mode.get(), text_1)
                if self.log_scroll2end.get():
                    self.log_box.see(self.log_insert_mode.get())
        except AttributeError:
            print(f"AttributeError!    {text_1}")
            print(format_exc())
        except tk.TclError:
            print(f"TclError!    {text_1}")
            print(format_exc())
        self.log_box.update()

    def record_register(self, *text, sep=" ", end="\n", tag=pk.Peeker.LOG_INFO):
        self.record_ln(*text, sep=sep, end=end, tag=tag)
        tmp_text = (
            "[" + time.strftime('%H:%M:%S', time.localtime(time.time())) + "]", tag + ": ",
            sep.join(map(str, text)) + end)
        text_1 = "".join(tmp_text)
        try:
            if self.gui_live:
                self.log_box.see(self.log_insert_mode.get())
        except AttributeError:
            print(f"AttributeError!    {text_1}")
            # print(format_exc())
        except tk.TclError:
            print(f"TclError!    {text_1}")
            # print(format_exc())
        else:
            if self.gui_live:
                self.log_box.config(state=NORMAL)
                self.log_list.append(text_1)
                self.log_box.insert(self.log_insert_mode.get(), text_1)
                tmp_tag = str(time.time_ns())
                self.log_box.tag_add(
                    tmp_tag, str(len(self.log_list)) + ".0", str(len(self.log_list)) + ".0 lineend")
                self.log_box.tag_config(tmp_tag, foreground=self.LOG_COLORS.get(tag, ""))
                if self.log_scroll2end.get():
                    self.log_box.see(self.log_insert_mode.get())
                self.log_box.config(state=DISABLED)
            self.log_box.update()

    def refresh(self):
        self.record_fx(
            f"置顶: {self.topmost.get()}，超级置顶: {self.take_focus.get()}，日志自动滚屏: {self.log_scroll2end.get()}")
        tmp_view = self.log_box.yview()
        if self.take_focus.get():
            self.topmost.set(True)
            self.bind("<FocusOut>", lambda x: self.topmost_tm(self, self.topmost.get(), self.take_focus.get()))
        else:
            self.unbind("<FocusOut>")
        self.attributes("-topmost", self.topmost.get())
        self.log_box.config(state=NORMAL, wrap=self.truncateTooLongStrings.get())
        for tmp in self.log_box.tag_names():
            self.log_box.tag_remove(tmp, "1.0", END)
        self.log_box.delete(1.0, END)
        for i in range(len(self.log_list)):
            self.log_box.insert(self.log_insert_mode.get(), self.log_list[i])
            # tmp = re.match(r"(\[\d{4}-\d{2}-\d{2}T\d{2}\.\d{2}\.\d{2}Z])(\b(info|warning|error)\b): ", i)
            # 此为 [xxxx-xx-xxTxx.xx.xxZ] 格式，是控制台输出的格式
            tmp = re.match(r"(\[\d{2}:\d{2}:\d{2}])(\b(%s)\b): " % "|".join(self.LOG_COLORS.keys()), self.log_list[i])
            # 此为 log_box 输出的格式
            if tmp is not None:
                tmp_tag = tmp.group(1) + str(i)
                self.log_box.tag_add(tmp_tag, str(i + 1) + ".0", str(i + 1) + ".0" + " lineend")
                self.log_box.tag_config(tmp_tag, foreground=self.LOG_COLORS.get(tmp.group(2), ""))
        self.log_box.config(state=DISABLED)
        self.sync_box.delete(0, END)
        for i in self.cursors.keys():
            type_ = self.cursors[i].get("type", "Unknown")
            if type_ == self.REP:
                self.sync_box.insert(END, f"[替换]{i} <===> {self.cursors[i]['dst']}")
            elif type_ == self.SOL:
                self.sync_box.insert(END, f"[固定分配]{i} <===> {self.cursors[i]['dst']}")
            elif type_ == self.DEVICE:
                self.sync_box.insert(END, f"[驱动器同步增强]{i} <===> {self.cursors[i]['dst']}")
            elif type_ == self.CUR:
                self.sync_box.insert(END, f"[游标同步]{i} <===> {self.cursors[i]['dst']}")
            else:
                self.sync_box.insert(END, f"[未知]{i} <===> {self.cursors[i]['dst']}")

        if self.log_scroll2end.get():
            self.log_box.see(self.log_insert_mode.get())
        else:
            print(tmp_view)
            self.log_box.see(tmp_view[1])
            self.log_box.see()

    def topmost_tm(self, name, top, focus):
        self.record_fx(f"调用 {self.topmost_tm.__name__} 函数：{name=}, {top=}, {focus=}")
        # topmost_st(name, top, focus)

        if top is not None:
            name.attributes("-topmost", top)
        if focus:
            name.deiconify()

    def upgrade_config(self):
        super().upgrade_config()
        self.userdata.update({
            "log_scroll2end": self.log_scroll2end.get(),
            "take_focus": self.take_focus.get(),
            "topmost": self.topmost.get(),
            "history": self.user_history,
            "log_insert_mode": self.log_insert_mode.get(),
            "theme": self.theme.get(),
            "alpha_mode": self.alpha_mode.get(),
            "disabledWhenSubWindow": self.disabledWhenSubWindow.get(),
            "truncateTooLongStrings": self.truncateTooLongStrings.get(),
        })
        self.conf_config.update({"userdata": self.userdata})
        self.warnings.update({
            "show_terminal_warning": self.show_terminal_warning.get(),
            "OnQuit": self.OnQuit.get()
        })
        self.conf_config.update({"warnings": self.warnings})

    def extract_config(self):
        super().extract_config()
        self.user_history = self.userdata.get("history", {})
        self.log_scroll2end.set(self.userdata.get("log_scroll2end", True))
        self.show_terminal_warning.set(self.warnings.get("show_terminal_warning", False))
        self.take_focus.set(self.userdata.get("take_focus", False))
        self.topmost.set(self.userdata.get("topmost", False))
        self.log_insert_mode.set(self.userdata.get("log_insert_mode", END))
        self.theme.set(self.userdata.get("theme", "vista"))
        self.alpha_mode.set(self.userdata.get("alpha_mode", 100))
        self.disabledWhenSubWindow.set(self.userdata.get("disabledWhenSubWindow", False))
        self.warnings = self.conf_config.get("warnings", {})
        self.OnQuit.set(self.warnings.get("OnQuit", 0))
        self.truncateTooLongStrings.set(self.userdata.get("truncateTooLongStrings", NONE))

    def clear_config(self):
        title = f"重置 {self.SYNC_ROOT_FP} 的配置信息"
        if msgbox.askokcancel(title,
                              "此操作将抹去所有配置信息。\n包括同步的目录、记录的存档等，且无法恢复。\n你确定继续吗？",
                              icon="warning"):
            self.record_fx(title)
            self.conf_config.clear()
            self.extract_config()
            self.save(ren=True)
            self.log_list.clear()
            msgbox.showinfo(title, f"配置信息已恢复为初始状态", icon="info")
            self.refresh()
            # self.gui_destroy(destroy2=True, save=False)

    def terminate_sync(self):
        super().terminate_sync()
        # self

    def remove_empty_in_bw_list(self) -> None:
        key_words = ("volumeId_blacklist", "volumeId_whitelist", "label_blacklist", "label_whitelist")
        for i_ in key_words:
            ch = 0
            tmp = self.profileSettings.get(i_, [])
            for j in range(len(tmp), 0, -1):
                if not tmp[j - 1]:
                    tmp.pop(j - 1)
                    ch += 1
            self.profileSettings.update({i_: tmp})
            self.record_fx(f"在 {i_} 中移除了 {ch} 个空值")

    def seq_expand_gen(self, seq: Sequence | Mapping | Set, key_: Callable = lambda x: x,
                       tab: str = "    ", keepends=True, keepsign=False, _deep=0) -> tuple[str, int]:
        if isinstance(seq, Mapping):
            dict_copy = seq
            sign = "{},"
        else:
            if _deep == 0:
                self.record_fx("数据类型不规范：", type(seq), tag=self.LOG_WARNING)
            sign = "[],"
            dict_copy = dict()
            for i, j in enumerate(seq):
                dict_copy.update({i: j})

        if keepsign:
            yield sign[0] + ("\n" if keepends else ""), _deep
        for i in dict_copy.keys():
            if isinstance(dict_copy[i], Sequence | Mapping | Set) and not isinstance(dict_copy[i], str):
                yield (tab if keepsign else "") + str(i) + ":" + ("\n" if keepends else ""), _deep
                for j in self.seq_expand_gen(
                        dict_copy[i], key_=key_, tab=tab, keepends=keepends, keepsign=keepsign, _deep=_deep + 1):
                    yield (tab if keepsign else "") + tab + j[0], j[1]
            else:
                yield ((tab if keepsign else "") + str(i) + ": " + str(key_(dict_copy[i])) +
                       (sign[2] if keepsign else "") + ("\n" if keepends else ""), _deep)
        if keepsign:
            yield sign[1] + ("\n" if keepends else ""), _deep

    # ---------------------------
    def global_window_initialize(self, cls: tk.Toplevel, title="", parent=None):
        self.record_fx(f"初始化窗口：{cls=}, {title=}")
        cls.geometry(f"+{int(self.winfo_x() + self.winfo_width() / 6)}+{int(self.winfo_y() + self.winfo_height() / 6)}")
        if title:
            cls.title(title)
        if self.disabledWhenSubWindow.get():
            self.attributes("-disabled", True)
        cls.wm_resizable(False, False)
        cls.iconbitmap(self.ICON_FP)
        cls.attributes("-topmost", self.topmost.get())
        # cls.attributes("-toolwindow", True)
        cls.attributes("-alpha", self.alpha_mode.get() / 100)
        cls.protocol("WM_DELETE_WINDOW", lambda: self.global_window_destroyed(cls, title, parent))
        self.topmost_tm(cls, self.topmost.get(), True)
        if parent is None:
            temp_self = self
            self.record_fx("parent 为根窗口")
        else:
            self.record_fx("parent 为子窗口")
            temp_self = parent
        temp_self.bind("<FocusIn>", lambda x: self.topmost_tm(cls, self.topmost.get(), True))

        # cls.bind("<Destroy>", lambda x: self.global_window_destroyed(cls, title))
        # 绑定 Destroy 有一个弊端，就是销毁窗口时，该事件会被连续触发约七八次
        if self.take_focus.get():
            self.take_focus.set(False)
            self.record_fx("警告！触发递归绑定。")
            self.refresh()
            cls.bind("<Destroy>", lambda x: self.take_focus.set(True))
        cls.update()

    def global_window_destroyed(self, cls: tk.Toplevel, title="", parent=None):
        self.record_fx(f"『{title}』窗口被销毁 - {cls}")
        if parent is None:
            self.unbind("<FocusIn>")
        else:
            parent.unbind("<FocusIn>")
        cls.destroy()
        del cls
        if self.disabledWhenSubWindow.get():
            self.attributes("-disabled", False)
        self.deiconify()
        self.refresh()

    def warn_nowindow(self, destroy_ui=True, fake=False, time_=None, figure=None):
        if time_ is None:
            time_ = self.INF
        if figure is None:
            figure = self.INF

        if destroy_ui:
            self.gui_destroy(True, save=True)
        if fake:
            msgbox.showerror("Fatal Error!", f"""Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
PermissionError: [WinError 5] 拒绝访问。: '{environ.get("USERPROFILE")}'
""")
        self.run_until(figures=figure, end_time=time_, delay=1.0, save=True)
        self.shut()
        self.record_fx("gui_run 命令成功完成")
        self.save()

    # ---------------------------
    def template_run_command(self, win_: tk.Toplevel, cmd_: tk.Text, fx, each=False, strip=False):
        cmd_get = cmd_.get(1.0, END)
        if each:
            for i in cmd_get.split("\n"):
                if (not strip) or (i and i != "\n"):
                    self.record_fx(f"分条执行命令：{i}")
                    try:
                        fx(i)
                    except Exception as e:
                        self.record_fx(f"执行 {i} 时报错：\n{format_exc()}")
                else:
                    self.record_fx(f"跳过空行 - {i}")
        else:
            self.record_fx(f"执行命令：")
            self.record_fx(f"{cmd_get}")
            try:
                fx(cmd_get)
            except Exception as e:
                self.record_fx(f"执行命令时报错：\n{format_exc()}")
        self.conf_config["userdata"]["history"].update({"terminal_text": cmd_get})
        self.upgrade_config()
        self.global_window_destroyed(win_)

    def template_sysTerminal(self, fx, each=False, name="", initialvalue: str = "", strip=False, show_ter_warning=None):
        self.record_fx(f"{show_ter_warning=}, {self.show_terminal_warning.get()=}")
        if (show_ter_warning is not None and show_ter_warning) or (
                show_ter_warning is None and not self.show_terminal_warning.get()):
            msgbox.showwarning("警告", "本窗口缺少报错和输出显示的功能，因此并不能代替你的 Terminal 终端")
            msgbox.showinfo(
                "注意", (
                    "在 Windows 系统中，要打开 Terminal 终端，\n"
                    "请按下 Win徽标+R 键，在弹出的窗口中输入 cmd，然后回车"),
            )
            msgbox.showinfo(
                "注意", (
                    "在 Linux 系统中，请按下 Alt+F2 键，\n在弹出的窗口中输入 gnome-terminal，然后回车\n"
                    "本方法不一定适用于所有的 Linux 发行版"
                ),
            )
            msgbox.showinfo("注意", "要不再显示警告，请勾选命令窗口左下角的“不再显示警告”复选框")
            if not msgbox.askokcancel("警告", "你确定要继续吗？"):
                return
        win = tk.Toplevel(self)
        self.global_window_initialize(win, title=f"执行命令 - {fx.__name__ if not name else name}")

        cmd = tk.Text(win, width=60, height=19, undo=True, bd=3)
        scroll_bar = ttk.Scrollbar(win, command=cmd.yview, orient=VERTICAL, takefocus=False)
        cmd.config(yscrollcommand=scroll_bar.set, state=NORMAL)
        cmd.delete(1.0, END)
        cmd.insert(1.0, initialvalue if initialvalue else self.user_history.get("terminal_text", ""))
        cmd.grid(row=0, column=0, columnspan=2, sticky=E, padx=1, pady=self.GLOBAL_PADY)
        scroll_bar.grid(row=0, column=2, ipady=100, sticky=W, padx=0, pady=self.GLOBAL_PADY)
        if show_ter_warning is not False:
            show_terminal_warning_gui = ttk.Checkbutton(win, text="不再显示警告", variable=self.show_terminal_warning)
            show_terminal_warning_gui.grid(
                row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="执行", style=self.BUTTON_STYLE_USE, width=20,
                   command=lambda: self.template_run_command(
                       win_=win, cmd_=cmd, fx=fx, each=each, strip=strip)).grid(
            row=1, column=0 if show_ter_warning is False else 1, columnspan=2 if show_ter_warning is False else 1,
            padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    # ---------------------------
    def tr_choose(self):
        win = tk.Toplevel(self)
        self.global_window_initialize(win, title="帮我选择")
        choice_a = ttk.Entry(win, width=25, style=self.ENTRY_STYLE_USE)
        choice_b = ttk.Entry(win, width=25, style=self.ENTRY_STYLE_USE)
        choice_c = ttk.Entry(win, width=25, style=self.ENTRY_STYLE_USE)
        choice_a.grid(row=0, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        choice_b.grid(row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        choice_c.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="是").grid(row=0, column=0, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="还是").grid(row=1, column=0, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="抑或是").grid(row=2, column=0, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="？").grid(row=0, column=2, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="？").grid(row=1, column=2, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="？").grid(row=2, column=2, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="帮助", style=self.BUTTON_STYLE_USE, command=lambda: self.gui_help("choose", win)).grid(
            row=3, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="帮我选择", style=self.BUTTON_STYLE_USE, width=12, command=lambda: msgbox.showinfo(
            "随机选择的结果",
            "应该是 " + choice([choice_a.get(), choice_b.get()] + ([choice_c.get()] if choice_c.get() else [])),
            parent=win)).grid(row=3, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def tr_msgbox(self):
        local_title = "弹出窗口"

        def tan():
            self.conf_config["userdata"]["history"].update({
                "msgbox_ch01": title_entry.get(),
                "msgbox_ch02": prompt_entry.get(),
                "msgbox_ch03": icon_var.get(),
            })
            self.record_fx(self.tr_msgbox.__name__, prompt_entry.get(), icon_tup[icon_var.get()][2],
                           tag=icon_tup[icon_var.get()][2])
            msgbox.showinfo(title_entry.get(), prompt_entry.get(), icon=icon_tup[icon_var.get()][0], parent=win)
            self.global_window_destroyed(win, local_title)

        def ref(x=None):
            label_ico.config(image=icon_tup[icon_var.get()][1], width=32, height=32)
            self.record_fx(f"传递参数: {x}")
            # label_ico.config(image=icon_tup[x][1])

        win = tk.Toplevel()
        self.global_window_initialize(win, title=local_title)
        icon_tup = {
            "显示": ("info", tk.PhotoImage(file=self.INFO_FP), self.LOG_INFO),
            "警告": ("warning", tk.PhotoImage(file=self.WARNING_FP), self.LOG_WARNING),
            "错误": ("error", tk.PhotoImage(file=self.ERROR_FP), self.LOG_ERROR),
            "询问": ("question", tk.PhotoImage(file=self.QUESTION_FP), self.LOG_INFO),
        }
        icon_var = tk.StringVar()
        icon_var.set(self.user_history.get("msgbox_ch03", tuple(icon_tup.keys())[0]))

        title_entry = ttk.Entry(win, style=self.ENTRY_STYLE_USE)
        prompt_entry = ttk.Entry(win, style=self.ENTRY_STYLE_USE)
        # icon_mode = ttk.OptionMenu(win, icon_var, *tuple(icon_tup.keys()), command=lambda x: ref(x))
        icon_mode = ttk.Combobox(
            win, style=self.COMBOBOX_STYLE_USE, textvariable=icon_var, width=7, values=tuple(icon_tup.keys()),
            state="readonly", validatecommand=lambda x: ref(x), invalidcommand=lambda x: ref(x))
        icon_mode.bind("<<ComboboxSelected>>", lambda x: ref(x))
        title_entry.insert(0, self.user_history.get("msgbox_ch01", ""))
        prompt_entry.insert(0, self.user_history.get("msgbox_ch02", ""))

        title_entry.grid(row=0, column=1, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        prompt_entry.grid(row=1, column=1, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        icon_mode.grid(row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="title: ", width=12).grid(row=0, column=0, sticky=NSEW, padx=self.GLOBAL_PADX,
                                                     pady=self.GLOBAL_PADY)
        tk.Label(win, text="prompt: ", width=12).grid(row=1, column=0, sticky=NSEW, padx=self.GLOBAL_PADX,
                                                      pady=self.GLOBAL_PADY)
        label_ico = tk.Label(win)
        ref()
        label_ico.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="ok", style=self.BUTTON_STYLE_USE, width=10, command=tan).grid(
            row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def tr_today(self):
        today_l = time.localtime(time.time())
        today_s = time.strftime("%Y/%m/%d", today_l)
        seed(today_s + f"{environ.get('USERDOMAIN')}\\\\{environ.get('USERPROFILE')}")
        today_q = self.TODAY_QUOTE
        today_d = randint(10, 100)
        i = today_q[0]
        for i in today_q[::-1]:
            if i[0] <= today_d:
                break
        string = (f"今日人品 - {today_s}", f"你今天的人品是：{today_d}{i[1]}")
        self.record_fx(string[0])
        self.record_fx(string[1])
        msgbox.showinfo(string[0], string[1])  # 也可以是 0-100

    def tr_window_move(self, count: int = 1, step_x=5, step_y=5, delay=0.01, show_warning=True, edge_x3=30, edge_y3=30,
                       dance_3=None, fallen_step4=20, gravity_y5=-1, fallen_max5=25, fallen_step5=-1,
                       change_color=False):
        def fix_xOy():
            return (((self.winfo_x() + self.winfo_width() // 2) %
                     self.winfo_screenwidth()) - self.winfo_width() // 2,
                    ((self.winfo_y() + self.winfo_height() // 2) %
                     self.winfo_screenheight()) - self.winfo_height() // 2)

        content0 = f"{self.TITLE} 作者不会受理由于点击千万别点造成的任何 Bug。\n这是最后的警告，是否继续操作？"
        content1 = f"""当暴露在点击确定后的场景时，有极小部分人群会引发癲痫。
            这种情形可能是由于某些未查出的癫病症状引起，即使该人员并没有患癫痫病史也有可能造成此类病症。
            如果您的家人或任何家庭成员曾有过类似症状，请在点击确定前咨询您的医生或医师。
            如果您在稍后出现任何症状，包括头晕、目眩、眼部或肌肉抽搐、失去意识、失去方向感、抽搐或出现任何自己无法控制的动作，
            请立即关闭 {self.TITLE} 并咨询您的医生或医师。\n
            这是最后的警告，是否继续操作？ """
        choice_1 = randint(1, 5)
        dian_xian_list = (3, 4, 5)
        if dance_3 is None:
            dance_3 = choice([True, False])
        self.record_fx(f"{choice_1=}, {change_color=}, {dance_3=}")
        if not (show_warning and (msgbox.askokcancel("似是而非的警告", content0, icon="warning") and not (
                (choice_1 in dian_xian_list or change_color) and not msgbox.askokcancel(
            "最后的警告", content1, icon="warning")))):
            return -1
        else:
            self.attributes("-topmost", True)
            self.protocol("WM_DELETE_WINDOW", lambda: self.KEY_BOARD["terminate"][3])
            ch = 0
            next_y = 0
            teleport_elapsed = 0
            while count == -1 or ch < count:
                ch += 1
                current_x, current_y = fix_xOy()
                if change_color:
                    self.config(bg=self.COLOR[randint(0, len(self.COLOR) - 1)])
                if choice_1 == 1:
                    current_x += step_x
                    current_y += step_y
                elif choice_1 == 2:
                    current_x += randint(-step_x * 2, step_x * 2)
                    current_y += randint(-step_y * 2, step_y * 2)
                elif choice_1 == 3:
                    if dance_3:
                        current_x += randint(-step_x * 2, step_x * 2)
                        current_y += randint(-step_y * 2, step_y * 2)
                    teleport_elapsed -= 1
                    if teleport_elapsed <= 0:
                        current_x = randint(0 + edge_x3, self.winfo_screenwidth() - edge_x3)
                        current_y = randint(0 + edge_y3, self.winfo_screenheight() - edge_y3)
                        if dance_3:
                            teleport_elapsed = randint(0, randint(0, 300))
                        else:
                            teleport_elapsed = randint(0, 30)
                elif choice_1 == 4:
                    current_x += 1
                    current_y += fallen_step4
                elif choice_1 == 5:
                    current_x += step_x
                    current_y += next_y
                    next_y -= gravity_y5
                    if next_y >= fallen_max5:
                        next_y = -next_y + 1 - fallen_step5
                else:
                    break
                self.wm_geometry(f"+{current_x}+{current_y}")
                self.update()
                st.wait(delay, busy_loop=True)

    def tr_window_scale(self):
        pass

    # ---------------------------
    def gui_destroy(self, destroy2=None, slide=False, save=True):
        self.record_fx(f"{self.gui_destroy.__name__} 销毁主窗口")
        if destroy2 is None:
            destroy_mode = self.OnQuit.get()
        elif not destroy2:
            destroy_mode = 1
        else:
            destroy_mode = 2

        # 当 destroy2 显式设置为 True/False 时， self.OnQuit 的值会被直接绕过
        if destroy_mode == 2:
            if slide and not msgbox.askokcancel("确认关闭", "这么好的程序你舍得关闭吗"):
                return
            else:
                self.gui_live = False
                self.destroy()
        elif destroy_mode == 1:
            self.withdraw()
        elif destroy_mode == 0:
            # user_ch = askyesnocancel("", "")
            win = tk.Toplevel(self)
            local_title = "退出" + self.TITLE
            self.global_window_initialize(win, local_title)
            ttk.Label(win, text="当退出时：").grid(
                row=0, column=0, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            radio_btn1 = ttk.Radiobutton(win, variable=self.OnQuit, value=1, text="最小化到系统托盘")
            radio_btn2 = ttk.Radiobutton(win, variable=self.OnQuit, value=2, text="退出程序")
            radio_btn1.grid(row=1, columnspan=2, sticky=W, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            radio_btn2.grid(row=2, columnspan=2, sticky=W, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            ttk.Button(win, text="确定", style=self.BUTTON_STYLE_USE, command=self.gui_destroy).grid(
                row=3, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            ttk.Button(win, text="取消", style=self.BUTTON_STYLE_USE,
                       command=lambda: self.global_window_destroyed(win, local_title)).grid(
                row=3, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        else:
            content = f"{self.OnQuit.get()=} 赋值错误"
            self.record_fx(content)
            msgbox.showinfo("", content)
        # self.quit()
        if save:
            self.save(ren=True)
        if self.destroyWhenExit:
            self.clear_config()
            self.logout(arc_mode=1, del_log=True, del_conf=False, del_subfile=True)

    def gui_get_admin(self, take, quiet):
        self.at_admin_var.set(self.get_admin(take=take, quiet=quiet))
        self.update()

    def gui_help(self, page_="initial", parent=None):
        local_title = "帮助页面"

        def ref_page(page):
            page_var.set(page)
            header_t.config(text="本页面的索引为 " + page_var.get())
            help_t.config(state=NORMAL)
            help_t.delete(1.0, END)
            help_t.insert(1.0, help_text.get(page_var.get(), "找不到文本"), CENTER)
            help_t.config(state=DISABLED)
            if not page_var.get() in help_text.keys():
                self.record_fx(f"help - 找不到该索引: {page_var.get()}")
                page_var.set("initial")
                return -1
            if helpt_in.index(page_var.get()) == len(helpt_in) - 1:
                btn_n.config(state=DISABLED)
            else:
                btn_n.config(state=NORMAL)
            if helpt_in.index(page_var.get()) == 0:
                btn_p.config(state=DISABLED)
            else:
                btn_p.config(state=NORMAL)

        win = tk.Toplevel(self)
        self.global_window_initialize(win, local_title, parent)

        page_var = tk.StringVar()
        page_var.set(page_)
        helpt_in = tuple(help_text.keys())
        frame0 = ttk.LabelFrame(win, text=local_title, )
        frame0.grid(row=0, column=0, columnspan=4, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        header_t = tk.Label(frame0, text="", width=85, height=2)
        header_t.grid(row=0, column=0, columnspan=4, padx=self.__class__.GLOBAL_PADX, pady=self.__class__.GLOBAL_PADY)
        help_t = tk.Text(frame0, width=85, height=30, state=DISABLED)
        help_t.tag_config(CENTER, justify=CENTER)
        help_t.grid(row=1, column=0, columnspan=4, padx=self.__class__.GLOBAL_PADX, pady=self.__class__.GLOBAL_PADY)
        search_box = ttk.Combobox(win, style=self.COMBOBOX_STYLE_USE, width=57, values=helpt_in)
        search_box.bind("<Return>", lambda x=None: ref_page(search_box.get()))
        search_box.bind("<<ComboboxSelected>>", lambda x=None: ref_page(search_box.get()))
        search_box.grid(row=1, column=0, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="搜索！", style=self.BUTTON_STYLE_USE, command=lambda: ref_page(search_box.get()),
                   width=10).grid(
            row=1, column=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="首页", style=self.BUTTON_STYLE_USE, command=lambda: ref_page(helpt_in[0]),
                   width=10).grid(
            row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        btn_p = ttk.Button(win, text="上一页", style=self.BUTTON_STYLE_USE, width=10,
                           command=lambda: ref_page(helpt_in[helpt_in.index(page_var.get()) - 1]))
        btn_p.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        btn_n = ttk.Button(win, text="下一页", style=self.BUTTON_STYLE_USE, width=10,
                           command=lambda: ref_page(helpt_in[helpt_in.index(page_var.get()) + 1]))
        btn_n.grid(row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="尾页", width=10, style=self.BUTTON_STYLE_USE,
                   command=lambda: ref_page(helpt_in[len(helpt_in) - 1])).grid(
            row=2, column=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ref_page(page_var.get())

    def gui_key_view(self, dict_=None, key_: callable = None):
        dict_copy = dict_
        # dict: 原始内容，dict_copy: 处理数据后的内容
        if dict_ is None:
            dict_copy = self.KEY_BOARD
        if key_ is None:
            # key_ = lambda x: dict_copy[x][2] + ": " + dict_copy[x][1]
            key_ = lambda x: str(x)

        def refresh():
            self.record_fx(f"当前模式：{select_var.get()}")
            if select_var.get() == "TextView":
                key_view_gui.grid_forget()
                scroll_gui.grid_forget()
                key_view_text.grid(row=0, column=0, columnspan=2, padx=1, pady=self.GLOBAL_PADY)
                scroll_text.grid(row=0, column=2, sticky=W, ipady=175, padx=0, pady=self.GLOBAL_PADY)
            elif select_var.get() == "ListView":
                key_view_text.grid_forget()
                scroll_text.grid_forget()
                key_view_gui.grid(row=0, column=0, columnspan=2, padx=1, pady=self.GLOBAL_PADY)
                scroll_gui.grid(row=0, column=2, sticky=W, ipady=155, padx=0, pady=self.GLOBAL_PADY)
            else:
                self.record_fx(f"传入参数出错 - {select_var.get()}")

        win = tk.Toplevel(self)
        self.global_window_initialize(win, "检查已绑定的按键")

        select_var = tk.StringVar()
        select_var.set("ListView")
        key_view_gui = tk.Listbox(win, width=80, height=20)
        key_view_text = tk.Text(win, wrap=WORD, undo=True, width=80, height=30)
        scroll_gui = ttk.Scrollbar(win, command=key_view_gui.yview, orient=VERTICAL, takefocus=False)
        scroll_text = ttk.Scrollbar(win, command=key_view_text.yview, orient=VERTICAL, takefocus=False)
        key_view_gui.config(yscrollcommand=scroll_gui.set)
        key_view_text.config(yscrollcommand=scroll_text.set)
        key_view_text.delete(1.0, END)

        ttk.Radiobutton(win, variable=select_var, text="文本视图", value="TextView", command=refresh).grid(
            row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Radiobutton(win, variable=select_var, text="列表视图", value="ListView", command=refresh).grid(
            row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        for i in self.seq_expand_gen(dict_copy, key_=key_):
            key_view_gui.insert(END, i[0])
            key_view_text.insert(END, i[0])
        refresh()
        key_view_text.config(state=DISABLED)

    def gui_export_conf(self):
        ask_fp = asksaveasfilename(
            title="导出配置文件...", initialdir=self.SYNC_ROOT_FP, initialfile=self.DEFAULT_CONFIG_FNAME,
            defaultextension=".sc_conf", filetypes=self.CONF_FILE_TYPES)
        if ask_fp and ask_fp is not None:
            with open(ask_fp, "w", encoding="utf-8") as file:
                # file.write(temp_text.get())
                file.write(dumps(self.conf_config))
            self.record_fx("配置文件已导出为", ask_fp)
        else:
            self.record_fx(f"导出操作 - 已取消")

    def gui_import_conf(self):
        ask_fp = askopenfilename(
            title="导入配置文件...", initialdir=self.SYNC_ROOT_FP, initialfile=self.DEFAULT_CONFIG_FNAME,
            defaultextension=".json", filetypes=self.CONF_FILE_TYPES)
        if ask_fp and ask_fp is not None:
            with open(ask_fp, "r", encoding="utf-8") as file:
                # file.write(temp_text.get())
                self.conf_config = loads(file.read())
            self.extract_config()
            self.record_fx("已从", ask_fp, "导入完成！")
            msgbox.showinfo("导入文件", f"配置文件已导入为 {ask_fp}，\n请重启 {self.TITLE}")
        else:
            self.record_fx("导入操作 - 已取消")
        self.refresh()

    def gui_logout(self):
        local_title = "Logout Wizard"
        title_dice = ("注销实例", "删除确认", "解锁存档", "删除配置文件", "删除其他文件", "完成注销")
        del_arc = tk.IntVar()
        del_log = tk.BooleanVar()
        del_conf = tk.BooleanVar()
        del_subfile = tk.BooleanVar()

        def set_var(var: tk.Variable, val, page=None):
            var.set(val)
            if page is not None:
                refresh(movement=page)

        def fix_btn(prev, next_):
            if isinstance(prev, bool):
                prev = NORMAL if prev else DISABLED
            if isinstance(next_, bool):
                next_ = NORMAL if next_ else DISABLED
            self.record_fx(f"{prev=}, {next_=}")
            btn_prev.config(state=prev)
            btn_next.config(state=next_)

        def verify_del(user_input, choice_):
            self.record_fx(f"{user_input=}, {choice_=}")
            if str(choice_[choice_[-1]]) == user_input:
                # refresh(movement=1)
                fix_btn(prev=None, next_=True)
                temp_entry.config(state=DISABLED)
                temp_btn1.config(state=DISABLED)
                msgbox.showinfo("ok.", "验证通过", parent=win)
            else:
                msgbox.showerror("Error", "验证错误", parent=win)

        def forget_anyone():
            nonlocal temp_btn1, temp_btn2, temp_btn3, temp_text, temp_list, temp_entry, temp_comb, temp_msg
            temp_list.delete(0, END)
            temp_btn1.config(state=NORMAL)
            temp_btn1.grid_forget()
            temp_btn2.grid_forget()
            temp_btn3.grid_forget()
            temp_text.grid_forget()
            temp_list.grid_forget()
            temp_entry.config(takefocus=True, state=NORMAL)
            temp_entry.grid_forget()
            temp_comb.unbind("<<ComboboxSelected>>")
            temp_comb.grid_forget()
            temp_msg.grid_forget()

        def refresh(step_=None, movement=0, header=""):
            forget_anyone()
            step.set((step_ if step_ is not None else step.get()) + movement)
            label_frame.config(
                text=f"{local_title}: step {step.get()} - {header if header else (title_dice[step.get()] if step.get() + 1 <= len(title_dice) else local_title)}")
            self.record_fx(f"{step_=}, {movement=}")
            val = ("解锁", "删除", "保留")
            if step.get() == 0:
                # step 0
                tip_label.config(text=f"这个向导将引导你删除 {self.SYNC_ROOT_FP} 实例\n"
                                      f"点击“下一步”继续，点击“取消”退出本向导", height=20)
                fix_btn(False, True)
            elif step.get() == 1:
                RD_RANGE = 10
                fix_btn(True, False)
                temp_entry.config(width=30, takefocus=False)
                choice_ment = list(range(RD_RANGE))
                shuffle(choice_ment)
                choice_ment.append(randint(0, len(choice_ment) - 1))
                tip_label.config(
                    text=f"确认删除 {self.SYNC_ROOT_FP} 实例吗？\n"
                         f"如果确定，请在下面的文本框中输入 {choice_ment[0: -1]} 的第 {choice_ment[-1] + 1} 项",
                    height=20)
                temp_entry.grid(row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                temp_btn1.config(text="验证", state=NORMAL, command=lambda: verify_del(temp_entry.get(), choice_ment))
                temp_btn1.grid(row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

            elif step.get() == 2:
                # step 2
                temp_comb.config(values=val, width=40)
                temp_comb.insert(0, val[0])
                temp_comb.bind("<<ComboboxSelected>>", lambda x=None: set_var(del_arc, val.index(temp_comb.get())))
                temp_btn1.config(text=self.KEY_BOARD["read_arc"][2], command=self.KEY_BOARD["read_arc"][3])
                temp_btn2.config(text=self.KEY_BOARD["unlock_arc_r"][2], command=self.KEY_BOARD["unlock_arc_r"][3])
                # comb_box_.grid(row=0, column=0, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                temp_btn1.grid(row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                temp_comb.grid(row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                temp_btn2.grid(row=1, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                tip_label.config(height=20)
                fix_btn(True, True)
                if not self.conf_config.get("synced_archives", []):
                    tip_label.config(text="没有未解锁的存档，可直接跳转至下一步")
                    temp_btn1.config(state=DISABLED)
                    temp_btn2.config(state=DISABLED)
                    temp_comb.config(state=DISABLED)
                else:
                    tip_label.config(text=f"你有 {len(self.conf_config.get("synced_archives", []))} 个存档未解锁")
                    temp_btn1.config(state=NORMAL)
                    temp_btn2.config(state=NORMAL)
                    temp_comb.config(state="readonly")
            elif step.get() == 3:
                fix_btn(True, True)
                set_var(del_log, True)
                set_var(del_conf, True)
                if exists(self.conf_fp):
                    temp_btn1.config(state=NORMAL)
                    tip_label.config(height=1, text="警告，在这里编辑的配置文件，任何改动将不会被保存")
                    temp_text.insert(1.0, dumps(self.conf_config))
                    temp_text.config(state=DISABLED, width=40, height=21)
                    temp_text.grid(row=1, column=0, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                else:
                    tip_label.config(height=20, text=f"配置信息和日志已删除 :)")
                    temp_btn1.config(state=DISABLED)
                if exists(self.log_dirp):
                    temp_list.bind("<Double-1>", lambda x: startfile(temp_list.selection_get()))
                    for i in listdir(self.log_dirp):
                        temp_list.insert(END, join(self.log_dirp, i))
                    temp_btn2.config(state=NORMAL)
                    temp_list.config(width=40, height=15)
                    temp_list.grid(row=1, column=3, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                else:
                    temp_btn2.config(state=DISABLED)
                temp_btn1.config(text="导出配置信息", command=self.gui_export_conf)
                temp_btn1.grid(row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                temp_btn2.config(text="打开日志文件夹", command=lambda: startfile(self.log_dirp))
                temp_btn2.grid(row=2, column=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            elif step.get() == 4:
                tip_label.config(height=20)
                temp_list.config(width=70, height=8)
                temp_btn1.config(text="删除", command=lambda: set_var(del_subfile, True, 1))
                temp_btn2.config(text="保留", command=lambda: set_var(del_subfile, False, 1))
                fix_btn(True, True)
                self.upgrade_exclude_dir()
                for i in listdir(self.SYNC_ROOT_FP):
                    if join(self.SYNC_ROOT_FP, i) not in self.exclude_in_del:
                        temp_list.insert(END, join(self.SYNC_ROOT_FP, i))
                if temp_list.size() == 0:
                    tip_label.config(text="根目录下已无其他文件，可直接进入下一步")
                    temp_list.grid_forget()
                    temp_btn1.config(state=DISABLED)
                    temp_btn2.config(state=DISABLED)
                else:
                    temp_list.config(width=80, height=15)
                    temp_list.grid(row=1, column=0, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                    tip_label.config(height=2,
                                     text=f"在根目录下发现一些不属于 {self.TITLE} 创建的文件，\n{self.TITLE} 无法辨识其内容")
                    temp_btn1.grid(row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                    temp_btn1.config(state=NORMAL)
                    temp_btn2.grid(row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
                    temp_btn2.config(state=NORMAL)
            elif step.get() == 5:
                fix_btn(True, False)
                tip_label.config(
                    height=20, text=f"确认信息：\n"
                                    F"删除存档：{val[del_arc.get()]},\n"
                                    F"删除配置信息：{del_conf.get()},\n"
                                    F"删除日志：{del_log.get()},\n"
                                    F"删除其他文件：{del_subfile.get()}\n"
                                    F"点击完成按钮，完成注销")
                temp_btn1.config(text="完成", state=NORMAL, command=lambda: self.logout(
                    arc_mode=del_arc.get(), del_log=del_log.get(), del_conf=del_conf.get(),
                    del_subfile=del_subfile.get()))
                temp_btn1.grid(row=1, column=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
            else:
                # step: 越界
                forget_anyone()
                fix_btn(True, True)
                tip_label.config(height=20, text="找不到文本")

        win = tk.Toplevel(self)
        self.global_window_initialize(win, local_title)

        step = tk.IntVar()
        step.set(0)
        label_frame = ttk.LabelFrame(win)
        tip_label = tk.Label(label_frame, width=80, height=20, wraplength=500)
        btn_prev = ttk.Button(win, style=self.BUTTON_STYLE_USE, text="上一步", command=lambda: refresh(movement=-1))
        btn_next = ttk.Button(win, style=self.BUTTON_STYLE_USE, text="下一步", command=lambda: refresh(movement=1))
        btn_cancel = ttk.Button(win, style=self.BUTTON_STYLE_USE, text="取消",
                                command=lambda: self.global_window_destroyed(win, local_title))
        temp_btn1 = ttk.Button(label_frame, style=self.BUTTON_STYLE_USE)
        temp_btn2 = ttk.Button(label_frame, style=self.BUTTON_STYLE_USE)
        temp_btn3 = ttk.Button(label_frame, style=self.BUTTON_STYLE_USE)
        temp_msg = tk.Message(label_frame)
        temp_text = tk.Text(label_frame, undo=True)
        temp_list = tk.Listbox(label_frame)
        temp_entry = ttk.Entry(label_frame, style=self.ENTRY_STYLE_USE)
        temp_comb = ttk.Combobox(label_frame, style=self.COMBOBOX_STYLE_USE)

        label_frame.grid(row=0, column=0, columnspan=4, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tip_label.grid(row=0, column=0, columnspan=100, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        btn_prev.grid(row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        btn_next.grid(row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        btn_cancel.grid(row=1, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        refresh(step.get(), 0)
        win.update()

    def api_style(self, style):
        self.global_style.theme_use(style)
        self.theme.set(style)
        self.upgrade_config()
        # showinfo(local_title, f"主题已切换为 {style_box.get()}", parent=win)
        # self.global_window_destroyed(win, local_title)

    def gui_clear_list(self, list_, text):
        assert hasattr(list_, "__iter__"), f"{type(list_)} 不可遍历"
        list_.clear()
        self.upgrade_config()
        self.record_fx(text)


class Pk_Stray(PeekerGui):
    def __init__(self, syncRoot_fp):
        super().__init__(syncRoot_fp)
        # 添加菜单和图标
        self.create_systray_icon()
        # 绘制界面
        # self.gui_main()

    def create_systray_icon(self):
        """
        使用 Pystray 创建系统托盘图标
        """
        menu = (
            pystray.MenuItem("显示", self.show_window, default=True),
            pystray.MenuItem(self.KEY_BOARD["save_arc"][2], self.KEY_BOARD["save_arc"][3]),
            pystray.Menu.SEPARATOR,  # 在系统托盘菜单中添加分隔线
            pystray.MenuItem(self.KEY_BOARD["save_exit"][2], self.KEY_BOARD["save_exit"][3])
        )
        image = Image.open(self.ICON_FP)
        self.icon = pystray.Icon("icon", image, f"{self.TITLE} - {self.SYNC_ROOT_FP}", menu)
        # self.record_fx("icon.name=", self.icon.name)
        print("icon.name=", self.icon.name)
        threading.Thread(target=self.icon.run, daemon=True).start()

    # 关闭窗口时隐藏窗口，并将 Pystray 图标放到系统托盘中。
    def hide_window(self):
        self.withdraw()

    # 从系统托盘中恢复 Pystray 图标，并显示隐藏的窗口。
    def show_window(self):
        self.icon.visible = True
        self.deiconify()

    def quit_window(self, icon: pystray.Icon):
        """退出程序"""
        icon.stop()  # 停止 Pystray 的事件循环
        self.quit()  # 终止 Tkinter 的事件循环
        self.destroy()  # 销毁应用程序的主窗口和所有活动

    def gui_destroy(self, destroy2=None, slide=False, save=True):
        self.icon.visible = False
        self.icon.stop()
        super().gui_destroy(destroy2, slide, save)
