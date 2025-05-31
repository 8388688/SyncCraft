import simple_tools as st
import os, ctypes, sys, time, win32file, win32api, shutil, pywintypes, traceback
import sclog
from typing import Callable

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
    return hasattr(sys, "_MEIPASS")


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


def record_exc_info(verbose=False):
    exc_type, exc_value, exc_obj = get_exception_info()
    sclog.error("exception_type: \t%s" % exc_type)
    sclog.error("exception_value: \t%s" % exc_value)
    sclog.error("exception_object: \t%s" % exc_obj)
    if verbose:
        sclog.error("======== FULL EXCEPTION ========")
        for i in traceback.format_exception(exc_type, exc_value, exc_obj):
            sclog.error(i.rstrip())
        # sclog.error("".join(traceback_format_tb(exc_[2])))


record_exc_info2 = sclog.exception


def get_volume_label(drive) -> str | None:
    try:
        return win32api.GetVolumeInformation(drive)[0]
    except pywintypes.error as e:
        sclog.error(f"sc1.10+检查卷标时出现错误")
        sclog.error(f"Error Code {e.winerror}: {e.strerror}")
        # sclog.exception("sc1.10+检查卷标时出现错误\n")
        record_exc_info(True)
        return None


def set_volume_label(drive, label):
    try:
        return win32file.SetVolumeLabel(drive, label)
    except pywintypes.error as e:
        sclog.error(f"sc1.10+设置卷标时出现错误")
        sclog.error(f"Error Code {e.winerror}: {e.strerror}")
        record_exc_info(True)
    finally:
        return label


def label2mountId(drive):
    for i in os.listvolumes():
        # os.path.samefile(path1, path2)
        try:
            i_mount = os.listmounts(i)
        except FileNotFoundError:
            sclog.error(f"文件系统错误 - {i} 无法映射到对应的挂载点")
            record_exc_info(True)
            return False
        else:
            if os.path.realpath(drive) in map(lambda x: os.path.realpath(x, strict=False), i_mount):
                return i
    else:
        # raise FileNotFoundError("指定的驱动器不存在")
        return drive


def get_freespace_shutil(folder):
    _, _, free = shutil.disk_usage(folder)
    return free


def join_cmdline(*args: Callable):
    def join_cmd():
        for fx in args:
            if callable(fx):
                fx()
            else:
                sclog.warning(str(fx), "不可调用。")
                # raise ValueError(f"{str(fx)}不可调用。")

    return join_cmd


def sc_notate_auto(number):
    return st.scientific_notate(number, rate=1024, custom_seq=rate_list)
