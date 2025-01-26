from os import chdir, getenv
from os.path import dirname, normpath, samefile, exists
from tkinter.filedialog import askdirectory

from pk_gui import *
from pk_misc import update_sc
import threading


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


def put_conf():
    global gs_config
    gs_fiet = open(global_settings_fp, "w", encoding="utf-8")
    gs_fiet.write(pk.dumps(gs_config))
    gs_fiet.close()


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
        put_conf()
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
        put_conf()

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


if __name__ == '__main__':
    global_settings_dirp = pk.join(getenv("APPDATA"), TITLE)
    pk.safe_md(global_settings_dirp, quiet=True)
    global_settings_fp = pk.join(global_settings_dirp, "globalsettings.sc_json")

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
