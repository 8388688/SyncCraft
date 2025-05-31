import simple_tools as st
import os, ctypes, sys, time, win32file, win32api, shutil

rate_list = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB")


def resource_path(relative):
    return os.path.join(os.path.dirname(__file__), relative)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        return False


def is_exec():
    # 是在程序中运行吗（是在程序中运行，还是在源代码中运行）？
    return hasattr(sys, '_MEIPASS')


def get_exec():
    # 获取脚本运行的真实路径
    if is_exec():
        return sys.executable
    else:
        return os.path.abspath(__file__)


def get_time(format_="%Y-%m-%dT%H.%M.%SZ"):
    # 1.9 及以前的 SyncCraft 记录日志需要调用这个函数
    import warnings
    warnings.warn("1.10+ 及以后的版本不再需要该函数来格式化日志", PendingDeprecationWarning, stacklevel=4)
    return time.strftime(format_, time.localtime(time()))


def get_exception_info():
    return sys.exc_info()


def set_volume_label(drive, label):
    win32file.SetVolumeLabel(drive, label)
    return label


def get_freespace_shutil(folder):
    _, _, free = shutil.disk_usage(folder)
    return free


def sc_notate_auto(number):
    return st.scientific_notate(number, rate=1024, custom_seq=rate_list)
