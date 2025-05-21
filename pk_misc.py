import sys, hashlib
from ctypes import windll
from os import getenv
from os.path import abspath, join, dirname
from time import time, localtime, strftime

import simple_tools as st

__version__ = "1.9.5"
build_time = 1747756800
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


def resource_path(relative):
    return join(dirname(__file__), relative)
    # return join(environ.get("_MEIPASS2", abspath("")), relative)


def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except Exception as e:
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


def get_hms(timestamp: float | int):
    tmp = timestamp // 3600
    hh = "" if tmp <= 0 else f"{tmp:} 时"
    tmp = timestamp % 3600 // 60
    mm = "" if tmp <= 0 else f"{tmp} 分"
    tmp = timestamp % 60
    ss = "" if tmp <= 0 else f"{tmp:.1f} 秒"
    return f"{hh}{mm}{ss}"


def get_exception_info():
    return sys.exc_info()


def md5sum_2(fpath: str, algorithm: str, buffering: int = 8096) -> str:
    with open(fpath, "rb") as f:
        result = hashlib.new(algorithm)
        for chunk in iter(lambda: f.read(buffering), b""):
            result.update(chunk)
        return result.hexdigest()


def sc_notate_auto(number):
    return st.scientific_notate(number, rate=1024, custom_seq=rate_list)


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
reserved_size: 硬盘的保留空间，
有时候，同步的数据会占用过多硬盘空间。这个设置在每次同步时会检查一下硬盘的剩余空间（默认为 0 字节，也就是不留空间）。
当硬盘空间小于设定的数值时，停止同步。
busy_loop 时间等待：在程序内部使用更为精确的 CPU 滴答时钟计算等待时间，对时间控制更为精准，但同时也会带来更高的 CPU 负担。
如果同步过程中同步进程难以精准控制时间，或是等待时间差过大，可以开启此选项。
""")
}
