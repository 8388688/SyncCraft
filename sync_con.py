# 此文件中涵盖了 SyncCraft 的一些高层逻辑的函数，通常调用自 sync_api.py
# 这些函数可以记录日志
import os
import pywintypes
import win32api

import sclog
from sync_api import *


def init(log_root: sclog.BaseLogging | None = None):
    if isinstance(log_root, sclog.BaseLogging):
        return log_root
    else:
        raise TypeError("sync_con 日志模块没有初始化")
        # return sclog.BaseLogging("__Rernertikgnteihgbnet__")


def get_volume_label(drive) -> str | None:
    try:
        return win32api.GetVolumeInformation(drive)[0]
    except pywintypes.error as e:
        _root.error(f"sc1.10+检查卷标时出现错误")
        _root.error(f"Error Code {e.winerror}: {e.strerror}")
        # _root.exception("sc1.10+检查卷标时出现错误\n")
        record_exc_info(True)
        return None


def label2mountId(drive):
    for i in os.listvolumes():
        # os.path.samefile(path1, path2)
        try:
            i_mount = os.listmounts(i)
        except FileNotFoundError:
            _root.error(f"文件系统错误 - {i} 无法映射到对应的挂载点")
            record_exc_info(True)
            return False
        else:
            if os.path.realpath(drive) in [os.path.realpath(j, strict=False) for j in i_mount]:
                return i
    else:
        # raise FileNotFoundError("指定的驱动器不存在")
        return drive


def record_exc_info(verbose=False):
    exc_type, exc_value, exc_obj = get_exception_info()
    _root.error("exception_type: \t%s" % exc_type)
    _root.error("exception_value: \t%s" % exc_value)
    _root.error("exception_object: \t%s" % exc_obj)
    if verbose:
        _root.error("======== FULL EXCEPTION ========")
        for i in traceback.format_exception(exc_type, exc_value, exc_obj):
            _root.error(i.rstrip())
        # _root.error("".join(traceback_format_tb(exc_[2])))


# record_exc_info2 = _root.exception


def set_volume_label(drive, label):
    try:
        return win32file.SetVolumeLabel(drive, label)
    except pywintypes.error as e:
        _root.error(f"sc1.10+设置卷标时出现错误")
        _root.error(f"Error Code {e.winerror}: {e.strerror}")
        record_exc_info(True)
    finally:
        return label


def join_cmdline(*args: Callable):
    def join_cmd():
        for fx in args:
            if callable(fx):
                fx()
            else:
                _root.warning(str(fx), "不可调用。")
                # raise ValueError(f"{str(fx)}不可调用。")

    return join_cmd


_root: sclog.BaseLogging = None
