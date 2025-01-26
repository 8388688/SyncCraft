import sys
import tkinter as tk
from ctypes import windll
from http.client import RemoteDisconnected
from os import rename, unlink, getenv
from os.path import abspath, exists, join
from time import time, localtime, strftime, strptime, mktime
from tkinter import ttk
from tkinter.constants import *
from tkinter import messagebox as msgbox

import pythoncom
import win32con
import win32gui
import simple_tools as st
import threading
from requests import get
from requests.exceptions import ConnectTimeout
from win32com import client
from webbrowser import open as webbopen

__version__ = "1.8"
build_time = 1737648000
TITLE = "SyncCraft"
rate_list = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB")
global_settings_dirp = join(getenv("APPDATA"), TITLE)
st.safe_md(global_settings_dirp, quiet=True)
global_settings_fp = join(global_settings_dirp, "globalsettings.sc_json")

"""
def get_freespace_ctypes(folder):
    import platform
    from os import statvfs
    from ctypes import pointer, windll, c_ulonglong, c_wchar_p
    '''
    获取磁盘剩余空间
    :param folder: 磁盘路径 例如 D:\\
    :return: 剩余空间 单位 G
    '''
    if platform.system() == 'Windows':
        free_bytes = c_ulonglong(0)
        windll.kernel32.GetDiskFreeSpaceExW(c_wchar_p(folder), None, None, pointer(free_bytes))
        return free_bytes.value / 1024 / 1024 // 1024
    else:
        st = statvfs(folder)
        return st.f_bavail * st.f_frsize / 1024 // 1024
"""


def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False


def is_exec():
    return hasattr(sys, '_MEIPASS')


def get_exec():
    if is_exec():
        return sys.executable  # 获取打包后可执行文件的真实路径
    else:
        return abspath(__file__)  # 获取脚本路径


def get_time(format_="%Y-%m-%dT%H.%M.%SZ"):
    return strftime(format_, localtime(time()))


def topmost_st(name, top, focus=True):
    hwnd_title = {}

    def get_all_hwnd(hwnd_, mouse):
        if (win32gui.IsWindow(hwnd_)
                and win32gui.IsWindowEnabled(hwnd_)
                and win32gui.IsWindowVisible(hwnd_)):
            hwnd_title.update({hwnd_: win32gui.GetWindowText(hwnd_)})

    win32gui.EnumWindows(get_all_hwnd, 0)
    hwnd = win32gui.FindWindow(None, name)

    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)

        pythoncom.CoInitialize()
        shell = client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        if focus:
            win32gui.SetForegroundWindow(hwnd)
        if top is None:
            pass
        elif top:
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE | win32con.SWP_NOOWNERZORDER | win32con.SWP_SHOWWINDOW | win32con.SWP_NOSIZE)
        else:
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
    else:
        return False


def update_sc(win: tk.Tk | tk.Toplevel, record_fx=print, buildTime=build_time):
    def update_api():
        nonlocal size, chunk_size, start_t, content_size
        down_btn.config(state=DISABLED)
        dl_bar.grid(row=3, column=0, columnspan=3, padx=10, pady=5)
        dl_bar.start()
        root.update()
        try:
            url = up_content[updatable].get("url", None)
        except ConnectionRefusedError:
            record_fx("[WinError 10061] 似乎 github.com 已拒绝连接。[ConnectionRefusedError]")
        except ConnectTimeout:
            record_fx("加载缓慢。[ConnectTimeout]")
        except TimeoutError:
            record_fx('连接超时。[TimeoutError]')
        except RemoteDisconnected:
            record_fx("请求头的 User-Agent 错误。[RemoteDisconnected]")
        except ConnectionAbortedError:
            record_fx("你的主机中的软件中止了一个已建立的连接。")
        except ConnectionError:
            record_fx("ConnectionError")
        else:
            if url is None:
                webbopen("https://github.com/8388688/SyncCraft/releases")
                return -2
            elif url:
                req = get(url, stream=True)  # 这里需要对 url 更新
            else:
                req = get(f"https://github.com/8388688/SyncCraft/releases/download/{updatable}/{TITLE}.exe",
                          stream=True)
            content_size = int(req.headers.get("content-length", -1))
            if req.status_code == 200 and content_size != -1:
                dl_bar.stop()
                dl_bar.config(mode="determinate", maximum=content_size)

                with open(get_exec() + ".tmp", "wb") as package:
                    for chunk in req.iter_content(chunk_size=chunk_size):
                        package.write(chunk)
                        size += len(chunk)
                        dl_bar.config(value=size)
                        label.config(
                            text=f"已下载 {st.scientific_notate(size, custom_seq=rate_list, rate=1024)}/"
                                 f"{st.scientific_notate(content_size, custom_seq=rate_list, rate=1024)}")
                        root.update()
                        # root.update_idletasks()

                exec_bak = get_exec() + ".old"
                if exists(exec_bak):
                    unlink(exec_bak)
                rename(get_exec(), exec_bak)
                rename(get_exec() + ".tmp", get_exec())
            else:
                record_fx("下载错误！", response.status_code)
            dl_bar.forget()
            msgbox.showinfo("更新完成", "更新完成，用时%.1fs\n请重启 %s" % (time() - start_t, TITLE), parent=root)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, '
                      'like Gecko) Chrome/107.0.0.0 Safari/537.36',
        # 'Connection': 'close'  # 不使用持久连接
    }
    # response = get(url, stream=True)
    response = get(r'https://raw.githubusercontent.com/8388688/SyncCraft/main/version.json',
                   headers=headers)
    response_json = response.json()
    up_content = response_json["updates"]
    size = 0
    start_t = time()
    chunk_size = 8192  # 每次下载的数据大小
    content_size = int(response.headers.get("content-length", -1))
    updatable = __version__

    # current_date = mktime(strptime("", "%Y-%m-%d"))
    tmp = ""
    for i in up_content.keys():
        if up_content[i]["build_time"] > buildTime:
            updatable = i
            buildTime = up_content[i]["build_time"]
            # current_date = response_json[i]["date"]
            tmp = f"更新内容：\n{up_content[i]["content"]}"

    if updatable == __version__:
        record_fx("暂无更新")
        msgbox.showinfo("检查更新", "暂无更新")
    else:
        root = tk.Toplevel(win)
        up_content_text = tk.Text(root, width=60, height=18, undo=False, bd=3)
        up_content_text.grid(row=1, column=0, columnspan=3, padx=10, pady=5)
        tk.Label(root, text=f"{TITLE} 有新的更新！", bd=3, relief=GROOVE, width=60, height=1).grid(
            row=0, column=0, columnspan=3, padx=10, pady=10)
        dl_bar = ttk.Progressbar(root, length=400, cursor="spider", mode="indeterminate", maximum=content_size)
        tk.Label(root, text=f"正在将 {TITLE} 从 {__version__} 更新至 {updatable} 版本").grid(
            row=2, column=0, columnspan=2, padx=10, pady=5)
        label = tk.Label(root, text="")
        label.grid(row=2, column=2, padx=10, pady=5)
        down_btn = tk.Button(root, width=10, text="Download!", command=update_api)
        down_btn.grid(row=4, column=0, padx=10, pady=5)
        tk.Button(root, width=10, text="Cancel", command=root.destroy).grid(row=4, column=2, padx=10, pady=5)
        up_content_text.insert(END, tmp)
        up_content_text.config(state=DISABLED)
        root.update()


help_text = {
    "initial": f"""{TITLE} - 一个文件夹同步的工具\n{__version__=}""",
    "1": """支持延时同步、静默同步、多目录同步等""",

    "2": """注意事项：虽然理论上同步的 dst 目录可以为任意路径，
    但为了游标同步的统一性，推荐将所有 dst 目录统一归入 SyncRoot_fp 根目录下""",
    "choose": """第三行的“抑或是”为选填、若留空，系统会自动忽略该选项""",
    "add": """添加文件夹：如果 dst 为相对路径，
    系统会自动将其转换为相对同步根目录的路径""",
    "parameter": """参数设置：
    /forever: 
    /no_gui: 
    /build: 
    """,
    "settings": ("""
reserved_size：硬盘的保留空间，
有时候，同步的数据会占用过多硬盘空间。这个设置在每次同步时会检查一下硬盘的剩余空间（默认为 0 字节，也就是不留空间）。
当硬盘空间小于设定的数值时，停止同步。
busy_loop 时间等待：在程序内部使用更为精确的 CPU 滴答时钟计算等待时间，对时间控制更为精准，但同时也会带来更高的 CPU 负担。
如果同步过程中同步进程难以精准控制时间，或是等待时间差过大，可以开启此选项。
""")
}
