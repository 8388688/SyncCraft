import sys
from ctypes import windll

import pythoncom
import win32con
import win32gui
from win32com import client

__version__ = "v1.7.3"
TITLE = "SyncCraft"

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
    "settings": """
    reserved_size：硬盘的保留空间，
    有时候，同步的数据会占用过多硬盘空间。这个设置在每次同步时会检查一下硬盘的剩余空间（默认为 0 字节，也就是不留空间）。
    当硬盘空间小于设定的数值时，停止同步。
    busy_loop 时间等待：在程序内部使用更为精确的 CPU 滴答时钟计算等待时间，对时间控制更为精准，但同时也会带来更高的 CPU 负担。
    如果同步过程中同步进程难以精准控制时间，或是等待时间差过大，可以开启此选项。
    """
}
