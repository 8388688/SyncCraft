from os import chdir, getenv
from os.path import dirname, normpath, samefile, exists
from tkinter.filedialog import askdirectory

from pk_gui import *
from pk_misc import update_sc, global_settings_dirp, global_settings_fp
import threading
import pyperclip


# from distutils import *


def get_conf():
    if pk.exists(global_settings_fp):
        gs_fiet = open(global_settings_fp, "r", encoding="utf-8")
        ret = pk.loads(gs_fiet.read())
    else:
        gs_fiet = open(global_settings_fp, "w", encoding="utf-8")
        gs_fiet.write("{}")
        ret = {}
    gs_fiet.close()
    return ret


def put_conf(conf_json: str | dict):
    gs_fiet = open(global_settings_fp, "w", encoding="utf-8")
    gs_fiet.write(pk.dumps(conf_json))
    gs_fiet.close()
    return


def fix_conf(del_invalid_path=False, fix_entry: ttk.Combobox | tk.Entry | ttk.Entry | None = None):
    global gs_config
    gs_config.update({"archives": gs_config.get("archives", ["D:\\BackDT_sh", ])})
    gs_config.update({"maxArchiveHistory": gs_config.get("maxArchiveHistory", -1)})
    gs_config.update({"maxShowArchiveHistory": gs_config.get("maxShowArchiveHistory", 10)})
    if del_invalid_path:
        eaten = []
        for index in gs_config["archives"]:
            if not exists(index):
                eaten.append(index)
        for index in eaten:
            gs_config["archives"].remove(index)
    if fix_entry is not None:
        fix_entry.config(
            values=gs_config["archives"][0: min(len(gs_config["archives"]), gs_config["maxShowArchiveHistory"])]
        )
    gs_config.update({"autoUpdate": gs_config.get("autoUpdate", None)})


def global_settings():
    profile_ch = 0

    def browse():
        file = askdirectory(mustexist=True)
        if file:
            entry.delete(0, END)
            entry.insert(0, normpath(file))

    def save_and_exit():
        nonlocal valid_ui, profile_ch
        valid_ui = True
        for index in gs_config["archives"]:
            if exists(user_input.get()) and exists(index) and samefile(user_input.get(), index):
                gs_config["archives"].remove(index)
        else:
            pass_(quiet=True)
        gs_config["archives"].insert(0, user_input.get())
        if gs_config["maxArchiveHistory"] != -1:
            gs_config["archives"] = gs_config["archives"][
                                    0: min(len(gs_config["archives"]), gs_config["maxArchiveHistory"])]
        else:
            # gs_config["archives"] = gs_config["archives"]
            pass
        put_conf(gs_config)
        if exit_when_launch.get():
            root.destroy()
        else:
            profile_ch += 1
            # root.withdraw()
            if not profile_ch > 1:
                root.quit()
            else:
                root.mainloop()
            # return global_settings()

    if gs_config.get("autoUpdate") is None:
        user_ch = askyesnocancel("自动更新", f"你是否允许 {TITLE} 启动时自动检查更新？")
        if user_ch is None:
            pass
        else:
            gs_config.update({"autoUpdate": user_ch})
        put_conf(gs_config)

    root = tk.Tk()
    root.title(ShadowCraft.TITLE)
    root.iconbitmap(ShadowCraft.ICON_FP)
    root.resizable(False, False)
    get_center(root)
    topmost_st(ShadowCraft.TITLE, None, True)
    # root.minsize(300, 300)

    user_input = tk.StringVar()
    exit_when_launch = tk.BooleanVar()
    valid_ui = False
    # entry = tk.Spinbox(root, textvariable=user_input, width=42, highlightthickness=2, highlightbackground="grey",
    #                    highlightcolor="gold")
    entry = ttk.Combobox(root, textvariable=user_input, width=42)
    fix_conf(fix_entry=entry)
    entry.bind("<Return>", lambda x: save_and_exit())
    entry.insert(0, gs_config["archives"][0])
    entry.grid(row=1, column=0, columnspan=3, padx=10, pady=5)
    label = tk.Label(root, text="输入同步文件夹的根路径")
    label.grid(row=0, column=0, columnspan=3, padx=10, pady=5)
    tk.Button(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
              text="确定≌", command=save_and_exit).grid(row=2, column=0, padx=10, pady=5)
    tk.Button(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
              text="取消", command=root.destroy).grid(row=2, column=1, padx=10, pady=5)
    tk.Button(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
              text="浏览", command=browse).grid(row=2, column=2, padx=10, pady=5)
    tk.Button(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
              text="清理失效路径", command=lambda: fix_conf(del_invalid_path=True, fix_entry=entry)).grid(
        row=3, column=0, padx=10, pady=5)
    tk.Button(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
              text="使用临时身份", command=lambda: user_input.set(pk.join(global_settings_dirp, "TempIdentity"))).grid(
        row=3, column=1, padx=10, pady=5)
    tk.Checkbutton(root, highlightbackground="grey", highlightcolor="green", highlightthickness=1, width=10,
                   text="启动完成后退出", variable=exit_when_launch, command=lambda: None).grid(
        row=3, column=2, padx=10, pady=5)

    if gs_config.get("autoUpdate"):
        label.config(text="[检查更新中]" + label["text"])
        update_th = threading.Thread(target=lambda: update_sc(root), daemon=True)
        update_th.start()
        # update(root, record_fx)

    root.mainloop()
    return valid_ui, user_input.get()


class ShadowCraft(Pk_Stray):
    def __init__(self, syncRoot_fp):
        super().__init__(syncRoot_fp)
        if pk.is_exec():
            self.execute_fp = pk.get_exec()
        else:
            self.execute_fp = __file__

        self.KEY_BOARD.update({
            "add_dir": ("<Control-n>", "Ctrl+N", "添加同步的文件夹", lambda x=None: self.gui_add()),
            "del_dir": ("<Control-d>", "Ctrl+D", "删除同步的文件夹", lambda x=None: self.gui_del()),
            "settings": ("<Control-,>", "Ctrl+,", "基础设置（本地）", lambda x=None: self.gui_settings()),
            "gs_settings": ("<Control-Shift-<>", "Ctrl+Shift+,", "基础设置（全局）", lambda x=None: self.gs_settings()),
        })

    def template_conf_put(self):
        local_title = "编辑设置"

        def conf_save():
            try:
                self.conf_config = pk.loads(text.get(1.0, END))
                self.extract_config()
                # self.upgrade_config()
            except JSONDecodeError:
                showinfo(local_title, "json 格式错误！", parent=win)
            else:
                showinfo(local_title, "已保存", parent=win)
                self.global_window_destroyed(win, local_title)

        win = tk.Toplevel(self)
        self.global_window_initialize(win, title=local_title)

        text = tk.Text(win, width=80, height=23, undo=True, autoseparators=True, wrap=WORD, bd=3, relief=GROOVE)
        scroll_bar = ttk.Scrollbar(win, command=text.yview)
        text.config(yscrollcommand=scroll_bar.set)

        text.delete(1.0, END)
        text.insert(1.0, pk.dumps(self.conf_config))
        text.grid(row=1, column=0, columnspan=3, sticky=E, padx=1, pady=self.GLOBAL_PADY)
        scroll_bar.grid(row=1, column=3, sticky=W, ipady=95, padx=1, pady=self.GLOBAL_PADY)
        tk.Label(win, text=f"更改这些配置可能会使{self.TITLE}停止工作", width=80, height=2,
                 fg="red", bd=3, relief=GROOVE).grid(  # font=("Arial", 10)
            row=0, column=0, columnspan=4, padx=self.GLOBAL_PADY, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="用默认编辑器打开", style=self.BUTTON_STYLE_USE, width=15,
                   command=lambda: startfile(abspath(self.conf_fp))).grid(
            row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="恢复", width=10, style=self.BUTTON_STYLE_USE,
                   command=lambda: self.join_cmdline(
                       lambda: text.delete(1.0, END),
                       lambda: text.insert(1.0, pk.dumps(self.conf_config)))).grid(
            row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        # ttk.Button(win, text="退出", width=10, style=self.BUTTON_STYLE_USE,
        #            command=lambda: self.global_window_destroyed(win, local_title)).grid(
        #     row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="保存", width=10, style=self.BUTTON_STYLE_USE, command=conf_save).grid(
            row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def gui_add(self):
        local_title = "添加"
        reflecting = {"固定分配": self.SOL, "游标同步": self.CUR, "替换": self.REP, "驱动器的增强同步": self.DEVICE}

        def api_add():
            src_ = src_ui.get()
            dst_ = (dst_ui.get() if isabs(dst_ui.get()) else pk.join(self.SYNC_ROOT_FP, dst_ui.get()))
            # if label_var.get() == "solid":
            #     self.solids.append([src_, dst_])
            # else:
            #     self.cursors.append([src_, dst_])
            self.cursors.update(
                {src_: {"dst": dst_, "type": reflecting[label_var.get()], "lastrun": "", "archives": []}})
            self.update_cursor()
            showinfo("添加同步目录", f"{src_} <===> {dst_}\n已成功添加", parent=win)
            src_ui.delete(0, END)
            dst_ui.delete(0, END)
            self.global_window_destroyed(win, local_title)
            self.refresh()

        win = tk.Toplevel(self)
        self.global_window_initialize(win, local_title)
        # win.wm_minsize(600, 400)
        label_var = tk.StringVar()
        label_var.set(list(reflecting.keys())[0])

        src_ui = ttk.Entry(win)
        dst_ui = ttk.Entry(win)
        cursor_btn = ttk.Combobox(win, values=list(reflecting.keys()), textvariable=label_var, state="readonly")

        tk.Label(win, text="source:").grid(row=0, column=0, padx=self.GLOBAL_PADX,
                                           pady=self.GLOBAL_PADY)
        tk.Label(win, text="destination:").grid(
            row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="ok.", style=self.BUTTON_STYLE_USE, width=10, command=api_add).grid(
            row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        src_ui.grid(row=0, column=1, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        dst_ui.grid(row=1, column=1, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        cursor_btn.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def gui_del(self):
        width = 60

        def api_del():
            """
            eaten = self.cursors.keys()
            for index in eaten:
                if index == del_entry.get():
                    self.cursors.pop(index)
                    self.record_fx(f"删除{index}")
                    showinfo("删除", f"{index} 已被删除", parent=win)
            self.record_fx("同步的文件夹已更新")
            # self.cursors = eaten
            self.update_cursor()
            refresh0()
            """
            self.record_fx(f"删除 {del_entry.get()} <===> {self.cursors.pop(del_entry.get())}")
            self.update_cursor()
            refresh0()

        def refresh0():
            del_entry.config(values=self.get_solid_list() + self.get_cursor_list())
            solid_listbox.config(state=NORMAL)
            cursor_listbox.config(state=NORMAL)
            solid_listbox.delete(0, END)
            cursor_listbox.delete(0, END)
            for i in self.get_solid_list():
                solid_listbox.insert(END, i)
            for i in self.get_cursor_list():
                cursor_listbox.insert(END, i)
            solid_listbox.config(state=DISABLED)
            cursor_listbox.config(state=DISABLED)
            self.refresh()

        win = tk.Toplevel(self)
        self.global_window_initialize(win, title="删除")
        # win.wm_minsize(600, 400)
        del_entry = tk.Spinbox(win, fg="green", state="readonly", values=self.get_cursor_list(), width=width, wrap=True)
        solid_listbox = tk.Listbox(win, width=width // 2, takefocus=False, state=DISABLED)
        cursor_listbox = tk.Listbox(win, width=width // 2, takefocus=False, state=DISABLED)

        del_entry.insert(0, "输入【编号】，此文本框没有防误操作的机制")
        refresh0()

        del_entry.grid(row=0, column=0, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        solid_listbox.grid(row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        cursor_listbox.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="固定分配").grid(row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tk.Label(win, text="游标同步").grid(row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(win, text="Delete!", style=self.BUTTON_STYLE_USE, command=api_del, width=width).grid(
            row=3, column=0, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def gs_settings(self):
        def forget_all():
            gs_frame.grid_forget()

        win = tk.Toplevel()
        self.global_window_initialize(win, "全局设置")
        autoupdate_rainbow = {"未配置（每次都询问）": None, "已启用": True, "已禁用": False}
        gs_frame = ttk.Labelframe(win, text="全局设置")

        def save():
            #####################################################
            ret = get_conf()
            ret.update({"autoUpdate": autoupdate_rainbow[update_combobox.get()]})
            put_conf(ret)
            #####################################################

        tip_f = ttk.Label(gs_frame, text="启动时检查更新")
        update_combobox = ttk.Combobox(gs_frame, state="readonly", values=tuple(autoupdate_rainbow.keys()))
        ok_button = ttk.Button(win, text="ok.", style=self.BUTTON_STYLE_USE, command=lambda: self.join_cmdline(
            save, lambda: self.global_window_destroyed(win, "全局设置")))

        update_combobox.set(update_combobox["values"][0])

        gs_frame.grid(row=0, column=0)
        tip_f.grid(row=0, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        update_combobox.grid(row=0, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ok_button.grid(row=30, column=0, columnspan=30, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

    def gui_settings(self):
        def get_log(x, base) -> tuple[int, int]:
            ret = 0
            x_cp = x
            while x_cp >= base:
                x_cp //= base
                ret += 1
            return x_cp, ret

        def forget_all():
            misc_frame.grid_forget()
            view_frame.grid_forget()
            syncFactor_frame.grid_forget()

        def upgrade_bw_box():
            bw_list.delete(1.0, END)
            for j in self.profileSettings.get(bw_list_rainbow[bw_combobox.get()], []):
                bw_list.insert(END, j + "\n")

        def bw_save_zhuanyong(msg=False):
            tmp_key = bw_list_rainbow[bw_combobox.get()]
            tmp_value = bw_list.get(1.0, END).strip("\n").split("\n")
            self.profileSettings.update({tmp_key: tmp_value})
            if msg:
                showinfo("保存", f"已保存 {tmp_key} 的 {len(tmp_value)} 个值", parent=win)

        def save_save():
            self.reserved_size = int(size_box.get()) * 1024 ** rate_list.index(rate_combobox.get())
            self.wait_busy_loop = busy_loop_var.get()
            bw_save_zhuanyong()
            self.remove_empty_in_bw_list()
            self.log_insert_mode.set(log_mode_rainbow[log_mode_box.get()])
            self.OnQuit.set(on_quit_rainbow[on_quit_combobox.get()])
            self.truncateTooLongStrings.set(truncateStr_rainbow[truncateStr_combobox.get()])
            self.upgrade_config()
            self.global_window_destroyed(win)

        win = tk.Toplevel(self)
        self.global_window_initialize(win, "实例设置", self)

        view_frame = ttk.Labelframe(win)
        syncFactor_frame = ttk.Labelframe(win)
        misc_frame = ttk.Labelframe(win)

        mode_rainbow = {"同步": syncFactor_frame, "视图": view_frame, "其他": misc_frame}
        bw_list_rainbow = {
            "卷标黑名单": "label_blacklist", "卷标白名单": "label_whitelist", "卷 ID 黑名单": "volumeId_blacklist",
            "卷 ID 白名单": "volumeId_whitelist",
            "文件列表黑名单": "file_blacklist", "文件列表白名单": "file_whitelist",
        }
        log_mode_rainbow = {"顺序输出": END, "倒序输出": "1.0"}  # 倒序输出理应是整型，但那样就无法装在 StringVar 变量中了
        on_quit_rainbow = {"每次都询问": 0, "最小化到系统托盘": 1, f"退出 {self.TITLE}": 2}
        truncateStr_rainbow = {"按单词换行": WORD, "按字符换行": CHAR, "禁用换行": NONE}

        # win.bind("<KeyRelease-a>", lambda x: view_frame.grid(row=0, column=0))
        # win.bind("<KeyRelease-b>", lambda x: syncFactor_frame.grid(row=0, column=0))
        # win.bind("<KeyRelease-c>", lambda x: gs_frame.grid(row=0, column=0))
        # win.bind("<KeyRelease-d>", lambda x: misc_frame.grid(row=0, column=0))

        tip_a = ttk.Label(syncFactor_frame, text="当硬盘空间小于此数值时，停止同步")
        # tip_b = ttk.Label(win, text="（时间控制更为精准，但同时也会带来更高的 CPU 负担）")
        tip_c = ttk.Label(view_frame, text="主题")
        tip_d = ttk.Label(view_frame, text="窗口透明度")
        tip_e = ttk.Label(view_frame, text="关闭窗口时")
        tip_g = ttk.Label(view_frame, text="日志换行")
        busy_loop_var = tk.StringVar()
        # busy_loop_var = tk.BooleanVar()  # BooleanVar() 无法存储 None 值
        busy_loop_var.set(self.wait_busy_loop)
        busy_loop_chbtn = ttk.Checkbutton(misc_frame, text="使用 busy_loop 时间等待", variable=busy_loop_var, width=20)
        size_box = self.get_side2side_entry(
            syncFactor_frame, ttk.Spinbox, max_=1024, from_=0, to=1024 - 1, width=20, increment=1)
        rate_combobox = ttk.Combobox(syncFactor_frame, values=rate_list, width=4)
        style_combobox = ttk.Combobox(view_frame, values=self.global_style.theme_names(), width=20)
        log_scroll_chbtn = ttk.Checkbutton(view_frame, text="自动滚屏", variable=self.log_scroll2end)
        bw_list = tk.Text(syncFactor_frame, width=80, height=24, wrap=WORD)
        bw_combobox = ttk.Combobox(syncFactor_frame, state="readonly", width=20, values=tuple(bw_list_rainbow.keys()))
        bw_btn = ttk.Button(
            syncFactor_frame, text="更新", style=self.BUTTON_STYLE_USE, command=lambda: bw_save_zhuanyong(msg=True))
        log_mode_label = ttk.Label(view_frame, text="日志输出模式")
        log_mode_box = ttk.Combobox(view_frame, state="readonly", values=tuple(log_mode_rainbow.keys()))
        alpha_scale = ttk.Scale(
            view_frame, from_=15, to=100, variable=self.alpha_mode,  # 为了方便辨认窗口，这里不允许将 -alpha 值由滑杆调整为 0
            length=160, command=lambda x: win.attributes("-alpha", float(x) / 100))
        dis_sub_chbtn = ttk.Checkbutton(
            misc_frame, text="disabledWhenSubWindow", variable=self.disabledWhenSubWindow, state=DISABLED)
        reset_warning_btn = ttk.Button(
            view_frame, text=self.KEY_BOARD["reset_warnings"][2], style=self.BUTTON_STYLE_USE,
            command=self.KEY_BOARD["reset_warnings"][3])
        on_quit_combobox = ttk.Combobox(view_frame, state="readonly", values=tuple(on_quit_rainbow.keys()))
        truncateStr_combobox = ttk.Combobox(view_frame, state="readonly", values=tuple(truncateStr_rainbow.keys()))

        mode_box = ttk.Combobox(win, state="readonly", values=tuple(mode_rainbow.keys()))
        ok_button = ttk.Button(win, text="ok.", style=self.BUTTON_STYLE_USE, command=save_save)

        for i in mode_rainbow:
            mode_rainbow[i].config(text=i)

        size_box.delete(0, END)
        size_box.insert(0, str(get_log(self.reserved_size, 1024)[0]))
        rate_combobox.delete(0, END)
        rate_combobox.insert(0, rate_list[get_log(self.reserved_size, 1024)[1]])
        rate_combobox.config(state="readonly")
        busy_loop_chbtn.config()
        style_combobox.bind("<<ComboboxSelected>>", lambda x: self.api_style(style_combobox.get()))
        style_combobox.insert(0, self.global_style.theme_use())
        style_combobox.config(state="readonly")
        bw_list.delete(1.0, END)
        bw_list.insert(1.0, "\n".join(self.profileSettings.get("volumeId_blacklist")))
        bw_combobox.bind("<<ComboboxSelected>>", lambda x: upgrade_bw_box())
        bw_combobox.set(bw_combobox["values"][0])
        for i in on_quit_rainbow.keys():
            if on_quit_rainbow[i] == self.OnQuit.get():
                on_quit_combobox.set(i)
        for i in log_mode_rainbow.keys():
            if log_mode_rainbow[i] == self.log_insert_mode.get():
                log_mode_box.set(i)
        for i in truncateStr_rainbow.keys():
            if truncateStr_rainbow[i] == self.truncateTooLongStrings.get():
                truncateStr_combobox.set(i)

        mode_box.bind("<<ComboboxSelected>>", lambda x: self.join_cmdline(
            lambda: forget_all(), lambda: mode_rainbow[mode_box.get()].grid(
                row=0, column=0, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)))
        mode_box.set(mode_box["values"][0])

        tip_a.grid(row=0, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        # tip_b.grid(row=2, column=1, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tip_c.grid(row=0, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        size_box.grid(row=0, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        rate_combobox.grid(row=0, column=2, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        busy_loop_chbtn.grid(row=4, column=0, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        style_combobox.grid(row=0, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        log_scroll_chbtn.grid(row=0, column=0, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        bw_list.grid(row=1, column=0, columnspan=3, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        bw_combobox.grid(row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        bw_btn.grid(row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        log_mode_label.grid(row=1, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        log_mode_box.grid(row=1, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        alpha_scale.grid(row=2, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tip_d.grid(row=2, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        dis_sub_chbtn.grid(row=6, column=0, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        reset_warning_btn.grid(row=1, column=0, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tip_e.grid(row=3, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        on_quit_combobox.grid(row=3, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        tip_g.grid(row=4, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        truncateStr_combobox.grid(row=4, column=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)

        mode_box.grid(row=30, column=0, sticky=W, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ok_button.grid(row=30, column=1, sticky=E, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        upgrade_bw_box()

    def gui_main(self):
        def topmost_en_de(en_de):
            view_menu.entryconfig("窗口置顶", state=DISABLED if en_de else NORMAL)
            view_menu.entryconfig(self.KEY_BOARD["minify"][2], state=DISABLED if en_de else NORMAL)
            self.refresh()

        def p_popen(__text):
            ls = popen(__text)
            ls_read = ls.read()
            self.record_fx(ls_read)
            ls.close()
            win2 = tk.Toplevel(self)
            self.global_window_initialize(win2, f"执行结果 - {__text}", self)
            text_box = tk.Text(win2)
            text_box.insert(1.0, ls_read)
            text_box.config(state=DISABLED)
            text_box.pack()

        def export_simplog():
            ask_ = asksaveasfilename(
                title="导出日志...", filetypes=(("日志文件", "*.log"), ("所有类型的文件", "*")),
                initialdir=self.SYNC_ROOT_FP,
                initialfile=f"日志导出_{pk.strftime('%Y_%m_%d_%H_%M_%S', pk.localtime(pk.time()))}.log")
            if ask_ is not None and ask_:
                self.record_fx(f"导出日志. . .")
                with open(ask_, "w") as file:
                    file.write("".join(self.log_list))
                showinfo("导出日志文件", f"日志文件已导出为 {ask_}")
                self.record_fx(f"日志文件已导出为 {ask_}")
            else:
                self.record_fx(f"{export_simplog.__name__} 操作已取消")

        def join_useless():
            self.upgrade_exclude_dir()
            for j in pk.listdir(self.SYNC_ROOT_FP):
                tmp_fp = pk.join(self.SYNC_ROOT_FP, j)
                if pk.isdir(tmp_fp):
                    if tmp_fp not in self.exclude_in_del:
                        self.record_fx(f"添加文件夹 - {tmp_fp}")
                        self.synced_archives.append(tmp_fp)
                    else:
                        self.record_fx(f"{tmp_fp} 位于排除列表中，已自动跳过")
                else:
                    self.record_fx(f"{tmp_fp} 不是文件夹")

        def rightClick_post(x, y):
            selected = self.log_box.tag_ranges(SEL)
            if selected:
                rightClick_menu.entryconfig(
                    "复制", state=NORMAL, command=pyperclip.copy(self.log_box.get(selected[0], selected[1])))
            else:
                rightClick_menu.entryconfig("复制", state=DISABLED)
            rightClick_menu.post(x, y)

        def copy2clipboard():
            pass

        for i in self.KEY_BOARD.keys():
            self.bind(self.KEY_BOARD[i][0], self.KEY_BOARD[i][3])
        self.record_fx(f"绑定 {len(self.KEY_BOARD.keys())} 个热键")

        self.at_admin_var.set(self.get_admin(take=False, quiet=True))

        self.log_box.grid(row=0, column=3, sticky=E, rowspan=100, columnspan=1, padx=0, pady=0)
        self.log_scroll_X.grid(row=100, column=3, sticky=S, columnspan=1, ipadx=115,
                               padx=1, pady=0)
        self.log_scroll_Y.grid(row=0, column=4, sticky=W, rowspan=100, columnspan=1, ipady=155,
                               padx=0, pady=1)
        self.sync_box.grid(row=4, column=0, rowspan=3, columnspan=2, sticky=W, padx=1, pady=self.GLOBAL_PADY)
        self.sync_scroll.grid(row=4, column=1, rowspan=3, columnspan=2, sticky=E, ipady=80, padx=1,
                              pady=self.GLOBAL_PADY)

        sync_menu = tk.Menu(self.menu_bar, tearoff=False)
        edit_menu = tk.Menu(self.menu_bar, tearoff=False)
        tool_menu = tk.Menu(self.menu_bar, tearoff=False)
        help_menu = tk.Menu(self.menu_bar, tearoff=False)
        permission_menu = tk.Menu(self.menu_bar, tearoff=False)
        saving_menu = tk.Menu(self.menu_bar, tearoff=False)
        arc_menu = tk.Menu(self.menu_bar, tearoff=False)
        presets_menu = tk.Menu(self.menu_bar, tearoff=False)
        view_menu = tk.Menu(self.menu_bar, tearoff=False)
        senior_setting_menu = tk.Menu(self.menu_bar, tearoff=False)
        lab_menu = tk.Menu(self.menu_bar, tearoff=False)
        treasure_menu = tk.Menu(self.menu_bar, tearoff=True)

        rightClick_menu = tk.Menu(self.menu_bar, tearoff=False)

        self.menu_bar.add_cascade(label="同步", menu=sync_menu)
        self.menu_bar.add_cascade(label="编辑", menu=edit_menu)
        self.menu_bar.add_cascade(label="工具", menu=tool_menu)
        self.menu_bar.add_cascade(label="视图", menu=view_menu)
        self.menu_bar.add_cascade(label="帮助", menu=help_menu)

        sync_menu.add_command(label="打开同步根目录", command=lambda: startfile(self.SYNC_ROOT_FP))
        sync_menu.add_command(label="打开终端", command=lambda: startfile(environ["COMSPEC"]))
        sync_menu.add_command(label=self.KEY_BOARD["run"][2], command=self.KEY_BOARD["run"][3],
                              accelerator=self.KEY_BOARD["run"][1])
        sync_menu.add_cascade(label="读写", menu=saving_menu)
        saving_menu.add_command(label=self.KEY_BOARD["save"][2], command=self.KEY_BOARD["save"][3],
                                accelerator=self.KEY_BOARD["save"][1])
        saving_menu.add_command(label=self.KEY_BOARD["save_arc"][2], command=self.KEY_BOARD["save_arc"][3],
                                accelerator=self.KEY_BOARD["save_arc"][1])
        saving_menu.add_command(label=self.KEY_BOARD["refresh"][2], command=self.KEY_BOARD["refresh"][3],
                                accelerator=self.KEY_BOARD["refresh"][1])
        sync_menu.add_cascade(label="存档", menu=arc_menu)
        sync_menu.add_cascade(label="预设值", menu=presets_menu)
        presets_menu.add_command(label=self.KEY_BOARD["preset0"][2], command=self.KEY_BOARD["preset0"][3],
                                 accelerator=self.KEY_BOARD["preset0"][1])
        presets_menu.add_command(label=self.KEY_BOARD["preset1"][2], command=self.KEY_BOARD["preset1"][3],
                                 accelerator=self.KEY_BOARD["preset1"][1])
        sync_menu.add_separator()
        sync_menu.add_command(label=self.KEY_BOARD["exit"][2], command=self.KEY_BOARD["exit"][3],
                              accelerator=self.KEY_BOARD["exit"][1])
        sync_menu.add_command(label=self.KEY_BOARD["save_exit"][2], command=self.KEY_BOARD["save_exit"][3],
                              accelerator=self.KEY_BOARD["save_exit"][1])
        sync_menu.add_command(label=self.KEY_BOARD["terminate"][2], foreground="red", activebackground="red",
                              accelerator=self.KEY_BOARD["terminate"][1], command=self.KEY_BOARD["terminate"][3])
        tool_menu.add_command(label=self.KEY_BOARD["settings"][2], command=self.KEY_BOARD["settings"][3],
                              accelerator=self.KEY_BOARD["settings"][1])
        tool_menu.add_command(label=self.KEY_BOARD["gs_settings"][2], command=self.KEY_BOARD["gs_settings"][3],
                              accelerator=self.KEY_BOARD["gs_settings"][1])

        tool_menu.add_separator()
        tool_menu.add_command(label="检查已绑定的按键", command=self.gui_key_view)
        tool_menu.add_command(label="清除历史记录", command=lambda: self.gui_clear_list(
            self.user_history, "清除历史记录. . . 完成！"))
        tool_menu.add_command(label=self.KEY_BOARD["reset_warnings"][2], command=self.KEY_BOARD["reset_warnings"][3],
                              accelerator=self.KEY_BOARD["reset_warnings"][1])
        tool_menu.add_cascade(label="权限", menu=permission_menu)
        tool_menu.add_cascade(label="高级设置", menu=senior_setting_menu)
        senior_setting_menu.bind("<Motion>", lambda x: showinfo(
            "高级设置", "仅限高级用户", icon="warning"))
        senior_setting_menu.add_command(
            label=self.KEY_BOARD["shut"][2], command=self.KEY_BOARD["shut"][3], accelerator=self.KEY_BOARD["shut"][1])
        senior_setting_menu.add_command(
            label=self.KEY_BOARD["terminated_sync"][2], command=self.KEY_BOARD["terminated_sync"][3],
            accelerator=self.KEY_BOARD["terminated_sync"][1])
        senior_setting_menu.add_command(
            label=self.KEY_BOARD["check_for_fakeupdate"][2], command=self.KEY_BOARD["check_for_fakeupdate"][3],
            accelerator=self.KEY_BOARD["check_for_fakeupdate"][1])
        senior_setting_menu.add_command(label="Upgrade Config", command=lambda: self.upgrade_config())
        senior_setting_menu.add_command(label="Extract Config", command=lambda: self.extract_config())
        senior_setting_menu.add_command(label="快速锁定该目录[此操作在退出后不可逆]",
                                        command=lambda: self.preserve(self.SYNC_ROOT_FP, True, True),
                                        foreground="red", activebackground="red")
        senior_setting_menu.add_command(
            label="解锁该目录", command=lambda: self.preserve(self.SYNC_ROOT_FP, None, False))
        senior_setting_menu.add_cascade(label="额外高级设置", menu=lab_menu)
        senior_setting_menu.add_command(label="删除此实例", command=self.gui_logout, foreground="red",
                                        activebackground="red")
        senior_setting_menu.add_command(
            label="[Extremely]快速删除此实例",
            command=lambda: self.logout(arc_mode=1, del_log=True, del_conf=True, del_subfile=True),
            foreground="#AA0000", activebackground="#AA0000")
        lab_menu.bind("<Enter>", lambda x: showinfo(
            "警告", "除非你已经完全明白这些功能的用途，否则请使之保持默认值", icon="warning"))
        lab_menu.add_command(label="py执行任意命令",
                             command=lambda: self.template_sysTerminal(exec, False, strip=True))
        lab_menu.add_command(label="终端执行任意命令(system)", command=lambda: self.template_sysTerminal(
            system, True, strip=True))
        lab_menu.add_command(label="终端执行任意命令(popen)", command=lambda: self.template_sysTerminal(
            p_popen, True, strip=True))
        lab_menu.add_command(label="编辑配置文件", command=self.template_conf_put)
        lab_menu.add_command(label="重置当前配置信息", command=self.clear_config)
        arc_menu.add_command(label=self.KEY_BOARD["read_arc"][2], command=self.KEY_BOARD["read_arc"][3],
                             accelerator=self.KEY_BOARD["read_arc"][1])
        arc_menu.add_command(label=self.KEY_BOARD["unlock_arc_r"][2], command=self.KEY_BOARD["unlock_arc_r"][3],
                             accelerator=self.KEY_BOARD["unlock_arc_r"][1])
        arc_menu.add_command(label=self.KEY_BOARD["unlock_arc"][2], command=self.KEY_BOARD["unlock_arc"][3],
                             accelerator=self.KEY_BOARD["unlock_arc"][1])
        arc_menu.add_command(label=self.KEY_BOARD["delete_arc"][2], command=self.KEY_BOARD["delete_arc"][3],
                             accelerator=self.KEY_BOARD["delete_arc"][1])
        arc_menu.add_command(label=self.KEY_BOARD["untie_arc"][2], command=self.KEY_BOARD["untie_arc"][3],
                             accelerator=self.KEY_BOARD["untie_arc"][1])
        arc_menu.add_command(label=self.KEY_BOARD["unlockall_arc"][2], command=self.KEY_BOARD["unlockall_arc"][3],
                             accelerator=self.KEY_BOARD["unlockall_arc"][1])
        arc_menu.add_command(label=self.KEY_BOARD["deleteall_arc"][2], command=self.KEY_BOARD["deleteall_arc"][3],
                             accelerator=self.KEY_BOARD["deleteall_arc"][1], activebackground="red", foreground="red")
        arc_menu.add_command(label=self.KEY_BOARD["untieall_arc"][2], command=self.KEY_BOARD["untieall_arc"][3],
                             accelerator=self.KEY_BOARD["untieall_arc"][1], activebackground="red", foreground="red")
        permission_menu.add_command(label=self.KEY_BOARD["check_admin"][2], command=self.KEY_BOARD["check_admin"][3],
                                    accelerator=self.KEY_BOARD["check_admin"][1])
        permission_menu.add_checkbutton(label=self.KEY_BOARD["take_admin"][2], command=self.KEY_BOARD["take_admin"][3],
                                        variable=self.at_admin_var, accelerator=self.KEY_BOARD["take_admin"][1])
        edit_menu.add_command(label=self.KEY_BOARD["add_dir"][2], command=self.KEY_BOARD["add_dir"][3],
                              accelerator=self.KEY_BOARD["add_dir"][1])
        edit_menu.add_command(label=self.KEY_BOARD["del_dir"][2], command=self.KEY_BOARD["del_dir"][3],
                              accelerator=self.KEY_BOARD["del_dir"][1])
        edit_menu.add_separator()
        edit_menu.add_command(label="导入配置文件", command=self.gui_import_conf)
        edit_menu.add_command(label="导出配置文件", command=self.gui_export_conf)
        edit_menu.add_separator()
        edit_menu.add_command(label="附加存档", command=lambda: self.template_sysTerminal(
            fx=lambda x: self.synced_archives.append(x), each=True, name="附加存档", strip=True,
            initialvalue="Type the archives you added. One per line. . .", show_ter_warning=False))
        edit_menu.add_command(label="将根目录下的无关文件加入存档", command=join_useless)
        edit_menu.add_command(label="移除黑白名单中的空值", command=self.remove_empty_in_bw_list)
        view_menu.add_command(
            label="清空日志", command=lambda: self.join_cmdline(self.log_list.clear, self.refresh))
        view_menu.add_checkbutton(label="自动滚屏", variable=self.log_scroll2end, command=self.refresh)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="窗口置顶", variable=self.topmost, command=self.refresh)
        view_menu.add_checkbutton(label="窗口置顶（超级置顶）", activebackground="navy", foreground="navy",
                                  variable=self.take_focus, command=lambda: topmost_en_de(self.take_focus.get()))
        view_menu.add_command(label=self.KEY_BOARD["minify"][2], command=self.KEY_BOARD["minify"][3],
                              accelerator=self.KEY_BOARD["minify"][1])
        help_menu.add_command(
            label=self.KEY_BOARD["help"][2], command=self.KEY_BOARD["help"][3], accelerator=self.KEY_BOARD["help"][1])
        help_menu.add_command(
            label=self.KEY_BOARD["check_for_update"][2], command=self.KEY_BOARD["check_for_update"][3],
            accelerator=self.KEY_BOARD["check_for_update"][1])
        help_menu.add_separator()
        help_menu.add_cascade(
            label="百宝箱", menu=treasure_menu, activebackground=choice(self.COLOR), foreground=choice(self.COLOR))
        treasure_menu.add_command(
            label="今日人品", command=self.tr_today, activebackground="purple", foreground="purple")
        treasure_menu.add_command(label="临时文本框", command=lambda: self.template_sysTerminal(
            pass_, False, "temporary_text", show_ter_warning=False), activebackground="pink", foreground="pink")
        treasure_menu.add_command(
            label="弹出消息框", command=self.tr_msgbox, activebackground="blue", foreground="blue")
        treasure_menu.add_command(
            label="帮我选择", command=self.tr_choose, activebackground="cyan", foreground="cyan")
        treasure_menu.add_command(label="md5值计算", command=lambda: self.template_sysTerminal(
            lambda x: showinfo("md5生成", "md5值为：\n" + pk.get_md5(x)), False, "md5sum",
            # initialvalue="Type the string you want to calculate. . .",
            show_ter_warning=False), activebackground="green", foreground="green")
        treasure_menu.add_command(
            label="随机ABCD选项生成（1次）", activebackground="gold", foreground="gold",
            command=lambda: showinfo("随机选项生成", f"生成的随机选项：{choice(['A', 'B', 'C', 'D'])}"))
        treasure_menu.add_command(
            label="随机ABCD选项生成（10次）", activebackground="orange", foreground="orange",
            command=lambda: showinfo("随机选项生成", f"生成的随机选项：{list2str([choice(
                ['A', 'B', 'C', 'D']) for _ in range(10)], sep=',')}"))
        treasure_menu.add_separator()
        treasure_menu.add_command(
            label="千万别点会爆炸", foreground="red", activebackground="red", command=lambda: self.tr_window_move(
                count=-1, show_warning=True, fallen_step5=2, change_color=not bool(randint(0, 4))))

        rightClick_menubar = (
            dict(label="复制", state=DISABLED, command=pass_),
            dict(label="导出日志文件", command=export_simplog),
        )
        for menu in rightClick_menubar:
            rightClick_menu.add_command(**menu)

        ttk.Button(self, text=self.KEY_BOARD["run"][2], style=self.BUTTON_STYLE_USE, width=15,
                   command=self.KEY_BOARD["run"][3]).grid(
            row=0, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text=self.KEY_BOARD["read_arc"][2], style=self.BUTTON_STYLE_USE, width=15,
                   command=self.KEY_BOARD["read_arc"][3]).grid(
            row=0, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text=self.KEY_BOARD["save_arc"][2], style=self.BUTTON_STYLE_USE, width=15,
                   command=self.KEY_BOARD["save_arc"][3]).grid(
            row=1, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text="预设: forever", style=self.BUTTON_STYLE_USE, width=15,
                   command=lambda: self.warn_nowindow(True, True)).grid(
            row=1, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text=self.KEY_BOARD["settings"][2], style=self.BUTTON_STYLE_USE, width=15,
                   command=self.KEY_BOARD["settings"][3]).grid(
            row=2, column=0, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        # ttk.Button(self, text="temp.logout", style=self.BUTTON_STYLE_USE, width=15,
        #            command=lambda: self.logout(arc_mode=2, del_log=True, del_conf=True, del_subfile=False)).grid(
        #     row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text="最小化到系统托盘", style=self.BUTTON_STYLE_USE, width=15,
                   command=self.withdraw, state=NORMAL).grid(
            row=2, column=1, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        ttk.Button(self, text=self.KEY_BOARD["save_exit"][2], command=self.KEY_BOARD["save_exit"][3],
                   style=self.BUTTON_STYLE_USE, width=30).grid(
            row=3, column=0, columnspan=2, padx=self.GLOBAL_PADX, pady=self.GLOBAL_PADY)
        self.bind("<Button-3>", lambda event: rightClick_post(event.x_root, event.y_root))
        self.update()


if __name__ == '__main__':
    gs_config = get_conf()
    fix_conf(del_invalid_path=False)

    debug = "/debug" in argv
    no_gui = "/no_gui" in argv
    build = "/build" in argv
    # debug = True
    chdir(dirname(__file__))
    # print(__file__)
    # print(argv)
    # if __file__ in argv:
    #     index_ = argv.index(__file__) + 1
    #     print(index_, len(argv) > index_)
    # else:
    #     index_ = 1
    #     print("FAIL")
    if len(argv) > 1 + int(pk.is_exec()):
        """
        for i in range(len(argv)):
            if pk.isdir(argv[i]):
                index_ = i
                break
        else:
            index_ = -1
        """
        index_ = 1
    else:
        index_ = -1
    if len(argv) > 1 and (
            build or (pk.isdir(argv[index_]) or askokcancel(str(argv[index_]), "指定的文件夹不存在\n是否创建"))):
        # print(argv[index_])
        profile = (True, argv[index_])
    else:
        profile = global_settings()
    if not profile[0]:
        pk.sys_exit(0)

    start_time = [pk.time(), ]
    if not no_gui:
        g2c2 = ShadowCraft(profile[1])
        g2c2.setup()
        g2c2.shut()
        g2c2.refresh()

    else:
        g2c2 = pk.Peeker(profile[1])
        g2c2.setup()
        g2c2.shut()
    start_time.append(pk.time())

    g2c2.__class__.debug = debug

    if debug:
        # g2c2.record_fx(f"警告：你正在使用 sxj 提供的测试版本, {pk.__version__=}")
        g2c2.record_fx(f"警告：你正在使用测试版本, {pk.__version__=}")
        showinfo("", f"警告：你正在使用测试版本, {pk.__version__=}")
    if "/forever" in argv:
        if not no_gui:
            g2c2.warn_nowindow(True, False)
        else:
            g2c2.run_until(delay=1.0, save=True)
            g2c2.shut()
            # g2c2.record_fx("")
            g2c2.save()
    elif "/run_f" in argv:
        g2c2.gui_destroy(True)
        prei = argv.index("/run_f")
        g2c2.run_until(figures=int(argv[prei + 1]), factor2="and")
    elif "/run_t" in argv:
        g2c2.gui_destroy(True)
        prei = argv.index("/run_t")
        g2c2.run_until(end_time=int(argv[prei + 1]), factor2="and")
    else:
        g2c2.gui_main()
        start_time.append(pk.time())
        g2c2.record_fx(f"%s 外部时间计算：第一阶段用时 %.2fs" % (TITLE, start_time[1] - start_time[0]))
        g2c2.record_fx(f"%s 外部时间计算：第二阶段用时 %.2fs" % (TITLE, start_time[2] - start_time[1]))
        g2c2.mainloop()
        g2c2.record_fx("正在退出. . . . . . ")
        g2c2.save()
