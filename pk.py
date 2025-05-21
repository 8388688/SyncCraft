"""pk.py 中并未实现 "destroyWhenExit": self.destroyWhenExit 的『退出时自动清理数据』功能

真正实现此功能的，在 pk_gui.py 的 gui_destroy 中。

"""
from __future__ import print_function

import stat
from builtins import open as fopen
from json import loads, dumps
from os import (chdir, rename, remove, rmdir, getenv, listdir, listmounts,
                listvolumes, getcwd, stat as os_stat, chmod, unlink)
from os.path import exists, join, isfile, isdir, realpath, dirname
# from psutil import disk_partitions
from shutil import copy2, copystat, disk_usage
from subprocess import run as command
from sys import exit as sys_exit, executable as sys_executable
from time import time
from traceback import format_exception
from typing import Literal, Callable, Mapping

import colorama
import ntsecuritycon
import pywintypes
import threading
import win32api
import win32file
import win32security

from pk_misc import (is_admin, __version__, windll, is_exec, TITLE, get_time,
                     get_exec, get_exception_info)
from simple_tools import safe_md, timestamp, wait, fp_gen, get_md5, dec_to_r_convert


def set_volume_label(drive, label):
    win32file.SetVolumeLabel(drive, label)
    return label


def get_freespace_shutil(folder):
    _, _, free = disk_usage(folder)
    return free


def safe_open(fp, fx: Callable = loads, invalidDefaultValue="{}", **kwargs) -> dict:
    if exists(fp):
        with fopen(fp, "r", **kwargs) as f:
            return fx(f.read())
    else:
        print(f"{fp} 文件不存在！")
        with fopen(fp, "w", **kwargs) as f:
            f.write(invalidDefaultValue)
        return {}


def val2key(seq: Mapping, val, default=None):
    for item in seq.keys():
        if seq[item] == val:
            return item
    else:
        return default


class Peeker:  # TODO: 参考“点名器.py”
    AND = "and"
    OR = "or"
    EQU = "=="
    NEQ = "!="
    LSS = "<"
    LEQ = "<="
    GTR = ">"
    GEQ = ">="
    INF = "Infinity"

    SOL = "solid"
    CUR = "cursor"
    REP = "replacement"
    DEVICE = "device"

    LOG_INFO = "info"
    LOG_WARNING = "warning"
    LOG_ERROR = "error"
    LOG_DEBUG = "debug"

    LOG_COLOR = {
        LOG_INFO: colorama.Fore.RESET,
        LOG_WARNING: colorama.Fore.YELLOW,
        LOG_ERROR: colorama.Fore.RED,
        LOG_DEBUG: colorama.Fore.GREEN,
    }

    ATTR_READ_ONLY = 1
    ATTR_HIDDEN = 2
    ATTR_SYSTEM = 4
    ATTR_DIR = 16
    ATTR_ARCHIVE = 32
    ATTR_NORMAL = 128

    USER_SECURITY_INFO = (
            win32security.OWNER_SECURITY_INFORMATION
            | win32security.GROUP_SECURITY_INFORMATION
            | win32security.DACL_SECURITY_INFORMATION
    )

    DEFAULT_CONFIG_FNAME = "Sync.sc_conf"

    CURRENT_WORK_DIR_STR = "当前文件夹"
    CURRENT_PROGRAM_DIR_STR = "当前程序所在文件夹"
    SYS_TEMP_DIR_STR = "系统临时目录"
    SYNC_ROOT_DIR_STR = "同步根目录"
    ISOLATED_TEMP_DIR_STR = "临时目录（隔离）"
    CUSTOM_DIR_STR = "自定义目录"

    WORK_DIR_TABLET = {
        CURRENT_WORK_DIR_STR: getcwd(),
        CURRENT_PROGRAM_DIR_STR: dirname(get_exec()),
        SYS_TEMP_DIR_STR: getenv("Temp"),
        SYNC_ROOT_DIR_STR: None,
        ISOLATED_TEMP_DIR_STR: dirname(__file__),
        CUSTOM_DIR_STR: None,
    }

    GLOBAL_ROOT_FP = join(getenv("AppData"), TITLE)
    GLOBAL_LOG_DIRP = join(GLOBAL_ROOT_FP, "__Logs__")

    def __init__(self, syncRoot_fp, setup: bool = False):  # TODO: 添加更多参数
        """

        @param syncRoot_fp: 同步根目录
        @param setup: 是否自动执行 setup() 函数
        """
        super().__init__()
        colorama.init(autoreset=True)

        self.record_fx = self.record_ln
        self.wait_fx = lambda x, busy=None: wait(x, busy_loop=busy)
        self.begin_time = time()
        self.sync_flag = True  # 为 False 时强行停止循环
        self.SYNC_ROOT_FP = syncRoot_fp  # 唯一，作为识别 ID
        self.conf_fp = join(self.SYNC_ROOT_FP, self.DEFAULT_CONFIG_FNAME)
        self.gs_log_fp = join(self.GLOBAL_LOG_DIRP, f"pk_api_{time() // 86400}.log")  # 86400: 一天一份日志
        self.log_dirp = join(self.SYNC_ROOT_FP, "__Logs__")
        self.log_fp = join(self.log_dirp, f"pk_api_{time() // 86400}.log")  # 86400: 一天一份日志
        self.log_fiet_live = True
        self.gs_log_fiet_live = True
        safe_md(self.GLOBAL_LOG_DIRP, quiet=True)
        safe_md(self.SYNC_ROOT_FP, quiet=True)
        safe_md(self.log_dirp, quiet=True)

        self.protection = True
        self.hidden = True
        self.execute_fp = get_exec()

        self.__cursors_src = []  # 存储格式为绝对路径
        self.__cursors_dst = []  # 存储格式也是绝对路径

        # 下面这几行，只是对类变量起到一个定义的作用，后面的赋值并不重要，可以任意修改
        self.log_fiet = None
        self.gs_log_fiet = None
        self.conf_fiet = None
        self.conf_config: dict | None = None

        self.cursors = {}
        self.solids = []
        self.userdata = {}
        self.run_times = 0
        self.last_run_times = 0
        self.run_beginning = ""
        self.run_completion = ""
        self.synced_archives = []
        self.exclude_in_del = []
        self.reserved_size = 0
        self.wait_busy_loop = None
        self.profileSettings = {}
        self.work_dir = ""
        self.useCustomDir: bool = False
        self.destroyWhenExit: bool = False
        self.force_unlock: bool = False
        # 下面这一行才是真正的赋值
        # self.extract_config() <-- 已移入 setup() 函数中

        if setup:
            self.setup()

    """已弃用
    
    def __del__(self):
        self.save(ren=True)
        exit_exc = format_exc()
        if exit_exc is not None:
            self.record_fx("报错：")
            self.record_fx(exit_exc)
        self.record_fx(f"删除实例 {self.SYNC_ROOT_FP}. . .")
        self.log_fiet.close()
        self.gs_log_fiet.close()
    """

    def upgrade_config(self):
        """将实例属性保存到 config 文件中

        @return: None
        """
        self.conf_config.update({
            "syncRoot_fp": self.SYNC_ROOT_FP, "cursors": self.cursors,
            "run_beginning": self.run_beginning, "run_completion": self.run_completion,
            "synced_archives": self.synced_archives, "reserved_size": self.reserved_size,
            "wait_busy_loop": self.wait_busy_loop,
            "work_dir": val2key(self.WORK_DIR_TABLET, self.work_dir) if not self.useCustomDir else self.work_dir,
            "useCustomDir": self.useCustomDir, "destroyWhenExit": self.destroyWhenExit,

            "__version__": __version__, "__RunningMode__": self.__class__.__name__
        })
        self.userdata.update({
            "run_times": self.run_times,
            "last_run_times": self.last_run_times,
            "force_unlock": self.force_unlock,
        })
        self.conf_config.update({"userdata": self.userdata})
        self.profileSettings.update({
            "volumeId_whitelist": self.profileSettings.get("volumeId_whitelist", []),
            "volumeId_blacklist": self.profileSettings.get("volumeId_blacklist", []),
            "label_blacklist": self.profileSettings.get("label_blacklist", []),
            "label_whitelist": self.profileSettings.get("label_whitelist", []),
            "file_blacklist": self.profileSettings.get("file_blacklist", []),
            "file_whitelist": self.profileSettings.get("file_whitelist", [])
        })
        self.conf_config.update({"profileSettings": self.profileSettings})
        self.record_fx("Upgrade Config 已更新")

    def extract_config(self):
        """将 config 文件中记录的实例变量【数值】更新到实例变量中

        @return: None
        """
        # __version__ 和 __RunningMode__ 属于只读变量，故未在此处更新。
        self.cursors = self.conf_config.get("cursors", {})
        # 格式：
        # {
        #     src1: {
        #         dst1:
        #         type\: [SOL | CUR | REP | DEVICE(针对驱动器同步的增强)]
        #         similarity: （仅针对驱动器的增强同步）[0.0 ~ 1.0],
        #         这个参数决定当两个 源驱动器 相同的存档，相似度达到百分之多少时合并，0 表示始终合并，1 表示永不合并
        #         lastrun: SerialNumber 硬盘序列号，当两次 run_once 检查硬盘序列号不一致时，强制 renameall_cur()
        #         注：当 type 的值【不是】 DEVICE 时，lastrun 的值与 src 保持一致
        #
        #         ...
        #     },
        #     src2: {
        #         dst2:
        #         type:
        #         ...
        #     }
        # }
        # src 必须是绝对路径
        # dst 必须是相对 self.SYNC_ROOT_FP 根的路径
        self.userdata = self.conf_config.get("userdata", {})
        self.run_times = self.userdata.get("run_times", 0)
        self.last_run_times = self.userdata.get("last_run_times", 0)
        self.force_unlock = self.userdata.get("force_unlock", False)
        self.run_beginning = self.conf_config.get("run_beginning", "")
        self.run_completion = self.conf_config.get("run_completion", "")
        self.synced_archives = self.conf_config.get("synced_archives", [])
        self.reserved_size = self.conf_config.get("reserved_size", 0)
        self.wait_busy_loop = self.conf_config.get("wait_busy_loop", None)
        self.profileSettings = self.conf_config.get("profileSettings", {
            "volumeId_whitelist": [],
            "volumeId_blacklist": [],
            "label_blacklist": [],
            "label_whitelist": [],
            "file_blacklist": [],
            "file_whitelist": [],
        })
        self.useCustomDir = self.conf_config.get("useCustomDir", False)
        self.destroyWhenExit = self.conf_config.get("destroyWhenExit", False)
        if self.useCustomDir:
            self.work_dir = self.conf_config["work_dir"]
        else:
            self.work_dir = self.WORK_DIR_TABLET.get(self.conf_config.get("work_dir", getcwd()), getcwd())
        self.record_fx("Extract Config 已更新")

    def save(self, ren: bool = True):
        self.record_fx(f"保存 {self.SYNC_ROOT_FP} {ren=} 同步目录的配置信息. . . ")
        if self.log_fiet_live:
            self.log_fiet.flush()
        if self.gs_log_fiet_live:
            self.gs_log_fiet.flush()
        self.upgrade_config()
        try:
            self.conf_fiet = fopen(self.conf_fp, "w", encoding="utf-8")
        except PermissionError:
            self.record_fx(f"无法保存 - 权限不足", tag=self.LOG_ERROR)
            self.record_exc_info(True)
        except OSError:
            self.record_fx(f"无法保存 - 原因如下", tag=self.LOG_ERROR)
            self.record_exc_info(True)
        else:
            self.conf_fiet.write(dumps(self.conf_config))
            self.conf_fiet.close()

        if ren:
            self.renameall_cur(save=True)
        self.record_fx("save 保存配置信息 - 完成！")

    def __get_id(self):
        return get_md5(self.SYNC_ROOT_FP)

    def join_cmdline(self, *args: Callable):
        def join_cmd():
            for fx in args:
                if callable(fx):
                    fx()
                else:
                    self.record_fx(str(fx), "不可调用。", tag=self.LOG_WARNING)
                    # raise ValueError(f"{str(fx)}不可调用。")

        return join_cmd

    def get_fromkey(self, keyword, src=None):
        if src is None:
            tmp = self.profileSettings.get(keyword, None)
        else:
            tmp = self.cursors.get(src, {}).get(keyword, self.profileSettings.get(keyword, None))
        return tmp

    def __label2mountId(self, drive):
        for i in listvolumes():
            # os.path.samefile(path1, path2)
            try:
                i_mount = listmounts(i)
            except FileNotFoundError:
                self.record_fx(f"文件系统错误 - {i} 无法映射到对应的挂载点", tag=self.LOG_ERROR)
                self.record_exc_info(True)
                return False
            else:
                if realpath(drive) in map(lambda x: realpath(x, strict=False), i_mount):
                    return i
        else:
            # raise FileNotFoundError("指定的驱动器不存在")
            return drive

    def __get_volume_label(self, drive) -> str | None:
        try:
            return win32api.GetVolumeInformation(drive)[0]
        except pywintypes.error:
            self.record_exc_info(True)
            return None

    def __set_volume_label(self, drive, label=""):
        try:
            return win32file.SetVolumeLabel(drive, label)
        except pywintypes.error:
            self.record_exc_info(True)

    get_volume_label = __get_volume_label
    set_volume_label = __set_volume_label

    def upgrade_exclude_dir(self):
        self.exclude_in_del = (self.log_dirp, self.conf_fp) + tuple(self.synced_archives)
        self.record_fx(f"更新排除文件列表 {self.exclude_in_del}")

    def record_ln(self, *__text, sep=" ", end="\n", local_log=None, global_log=None, tag=LOG_INFO):
        tmp = sep.join(map(str, __text)) + end
        now_time = get_time()
        if (local_log is None and self.log_fiet_live) or local_log:
            self.log_fiet.write(f"[{now_time}]{tag}: " + tmp)
        # self.log_fiet.flush()
        if (global_log is None and self.gs_log_fiet_live) or global_log:
            self.gs_log_fiet.write(f"[{now_time} | {self.SYNC_ROOT_FP}]{tag}: " + tmp)
        print(self.LOG_COLOR[tag] + f"[{now_time}]{tag}: " + tmp, sep="", end="")

    def setup(self):
        self.gs_log_fiet = open(self.gs_log_fp, "a", encoding="utf-8")
        self.log_fiet = open(self.log_fp, "a", encoding="utf-8")
        self.conf_config = safe_open(self.conf_fp, loads)

        self.WORK_DIR_TABLET[self.SYNC_ROOT_DIR_STR] = self.SYNC_ROOT_FP
        self.extract_config()
        tmp_ver = self.conf_config.get("__version__", "[Unknown]")
        if __version__ == tmp_ver:
            pass
        else:
            self.record_fx(f"运行版本不一致 {__version__} ≠ {tmp_ver}", tag=self.LOG_WARNING)

        chdir(self.work_dir)
        self.get_admin()

        # 优先级： 根目录操作 > replace > 固定分配 > 游标同步
        # 为提高程序效率，这里并没有使用 dimensional_list() 函数将列表“一维化”
        # 虽然使用了一个二重循环，但运行效率比加入 dimensional_list() 好得多
        for i in ([self.SYNC_ROOT_FP, ], [join(self.SYNC_ROOT_FP, i) for i in self.__cursors_dst]):
            for j in i:
                safe_md(j, quiet=True)
                self.record_fx(f"create dir: {j}")
                # TODO: attrib %j +s +h

        self.preserve(self.SYNC_ROOT_FP, True, None)
        self.update_cursor()
        self.renameall_cur(save=True)
        self.upgrade_exclude_dir()

        self.record_fx(f"当前工作目录: {self.work_dir}")
        self.record_fx(f"setup 函数已执行，version: {__version__}, Time used: %.3fs" % (time() - self.begin_time))

    def get_admin(self, take=False, quiet=False):
        if is_admin():
            if not quiet:
                self.record_fx(f"正在使用管理员权限运行 - 非常棒！")
            return True
        else:
            if not quiet:
                self.record_fx(f"尝试使用管理员权限运行 :(", tag=self.LOG_WARNING)
            if take:
                suffix = self.execute_fp.replace("/", "\\").split("\\")[-1].split(".")[-1]
                self.record_fx(f"准备以管理员身份重启. . . . . . {sys_executable=}, {self.execute_fp=}, {suffix=}")
                self.save(ren=True)
                chdir(getenv("Temp"))
                if is_exec():
                    windll.shell32.ShellExecuteW(None, "runas", self.execute_fp, self.SYNC_ROOT_FP, None, 1)
                else:
                    windll.shell32.ShellExecuteW(
                        None, "runas", sys_executable, " ".join((self.execute_fp, self.SYNC_ROOT_FP)), None, 1)
                sys_exit(0)
            else:
                return False

    def record_exc_info(self, verbose=True):
        exc_type, exc_value, exc_obj = get_exception_info()
        self.record_fx("exception_type: \t%s" % exc_type, tag=self.LOG_ERROR)
        self.record_fx("exception_value: \t%s" % exc_value, tag=self.LOG_ERROR)
        self.record_fx("exception_object: \t%s" % exc_obj, tag=self.LOG_ERROR)
        if verbose:
            self.record_fx("======= FULL EXCEPTION =======", tag=self.LOG_ERROR)
            for i in format_exception(exc_type, exc_value, exc_obj):
                self.record_fx(i.rstrip(), tag=self.LOG_ERROR)
            # self.record_fx("".join(traceback_format_tb(exc_[2])), tag=self.LOG_ERROR)

    def update_cursor(self):
        self.__cursors_src = list(self.cursors.keys())
        self.record_fx(f"Upgrade: {self.__cursors_src=}")
        self.__cursors_dst = [i["dst"] for i in self.cursors.values()]
        self.record_fx(f"Upgrade: {self.__cursors_dst=}")

    def __rename_and_register(self, __dir, __from_src=None):
        if exists(__dir):
            new_fn = __dir + timestamp(presets=3, no_beauty=True)
            self.record_fx(f"rename {__dir} -> {new_fn}")
            if __from_src is None:
                self.synced_archives.append(new_fn)
            else:
                self.cursors[__from_src]["archives"].append(new_fn)
            rename(__dir, new_fn)
            self.preserve(new_fn, self.hidden, self.protection, self.force_unlock)
        else:
            self.record_fx(f"Folder \'{__dir}\' does not exist!")

    def renameall_cur(self, save=False):
        self.record_fx(f"重命名: {self.__cursors_dst}")
        # for i in self.__cursors_dst:
        #     self.__rename_and_register(i)
        for i in self.cursors.keys():
            self.__rename_and_register(self.cursors[i]["dst"], i)
        self.upgrade_config()
        if save:
            self.save(ren=False)

    def delete(self, item, excludes=()):
        def deletefile_api(x, mode: Literal[1, 2] = 1, retry=4):  # mode: 1 = file, 2 = folder
            try:
                if mode == 1:
                    unlink(x)
                elif mode == 2:
                    rmdir(x)
                else:
                    raise ValueError(f"mode 参数只能是 1 or 2, 不能是 {mode}")
            except ValueError:
                self.record_exc_info(False)
                return 1
            except Exception as e:
                self.record_exc_info(False)
                self.record_fx(f"retry: {retry}")
                self.preserve(x, False, False, self.force_unlock)
                if retry > 0:
                    deletefile_api(x, mode, retry - 1)
                else:
                    self.record_fx(f"Discard. ({x})")

        for i in fp_gen(item, abspath=1, files=True, folders=True, exclude=excludes,
                        do_file=lambda x: deletefile_api(x, 1),
                        do_dir=lambda x: deletefile_api(x, 2),
                        topdown=False):
            if isfile(i):
                self.record_fx(f"delete file: {i}")
            elif isdir(i):
                self.record_fx(f"delete dir: {i}")
            else:
                self.record_fx(f"delete unknown: {i}")
        else:
            self.preserve(item, False, False, self.force_unlock)
            if not listdir(item):
                rmdir(item)
                self.record_fx(f"remove archive & rmdir: {item}")
            else:
                self.record_fx(f"remove archive: {item}")

    def unlock_arc(self, unlock=(), unlock_pre=True, delete=False, untie=True) -> int:
        # 返回值为一个整数，表示【成功】解锁了多少个存档
        # 注意当 untie 被设为 False 时，returns 总是与 param: unlock 的长度相等
        #
        # 实例：unlock_pre=False, delete=False, untie=True - 浏览存档
        # untie = False 时，即使解锁失败，也将存档从列表中删除。
        # TODO: 虽然还有诸多 bug，但我不打算修改了
        removed = []
        for i in unlock:
            if exists(i):
                self.record_fx(f"unlock: {i} - {unlock_pre=}, {delete=}, {untie=}")
                if unlock_pre:
                    self.preserve(i, False, False, self.force_unlock)
                    removed.append(i)
            else:
                self.record_fx(f"Unlock Failed - Folder {i} does not exist!", tag=self.LOG_ERROR)
                if not untie:
                    removed.append(i)
        for item in removed:
            if delete:
                self.delete(item=item)
            flag = True
            for i in self.cursors.values():
                i_arc: list = i.get("archives", [])
                for j in i_arc:
                    if j in removed:
                        i_arc.remove(j)
                        flag = False
                        break
                i["archives"] = i_arc
                if not flag:
                    break
            else:
                self.synced_archives.remove(item)
        length = len(removed)
        removed.clear()
        return length

    def unlockall_cur(self, unlock_pre=True, delete=False, untie=True):
        self.record_fx(f"{"解锁" if untie else "解除关联（解绑）"}存档" + (
            "并删除" if delete else ""))
        tmp = []
        length = 0
        for i in self.cursors:
            tmp += self.cursors[i].get("archives", [])
        length += self.unlock_arc(tmp, unlock_pre=unlock_pre, delete=delete, untie=untie)
        length += self.unlock_arc(self.synced_archives, unlock_pre=unlock_pre, delete=delete, untie=untie)
        self.record_fx(f"{self.unlockall_cur.__name__} 共计处理成功 {length} 个存档")

    def attr_config(self, fname, hidden: bool | None = None):
        self.record_fx(f"调用 {self.attr_config.__name__}({fname}) 函数，保护方向：{hidden}")
        if hidden is None:
            self.record_fx(f"{fname} 不隐藏")
            return
        elif hidden:
            ace = Peeker.ATTR_READ_ONLY + Peeker.ATTR_HIDDEN + Peeker.ATTR_SYSTEM + Peeker.ATTR_ARCHIVE
        else:
            ace = Peeker.ATTR_NORMAL
        self.record_fx(f"Set Attribute: {ace}")
        win32file.SetFileAttributes(fname, ace)

    def ACL_config(self, fname, preserve: bool | None = None, force: bool = False):
        system_user, domain, type_ = win32security.LookupAccountName("", "SYSTEM")
        everyone, domain, type_ = win32security.LookupAccountName("", "Everyone")
        admins, domain, type_ = win32security.LookupAccountName("", "Administrators")
        user, domain, type_ = win32security.LookupAccountName("", win32api.GetUserName())
        all_security_info = (
                win32security.OWNER_SECURITY_INFORMATION
                | win32security.GROUP_SECURITY_INFORMATION
                | win32security.DACL_SECURITY_INFORMATION
                | win32security.SACL_SECURITY_INFORMATION
        )
        self.record_fx(f"调用 {self.ACL_config.__name__}({fname}) 函数，保护方向：{preserve}，强制模式：{force}")

        """
        sd = win32security.GetFileSecurity(fname, all_security_info)
        old_dacl = sd.GetSecurityDescriptorDacl()
        old_sacl = sd.GetSecurityDescriptorSacl()
        old_group = sd.GetSecurityDescriptorGroup()
        """
        if force:
            new_sd = win32security.SECURITY_DESCRIPTOR()
            new_sd.Initialize()
            dacl = win32security.ACL()
            dacl.Initialize()
        else:
            new_sd = win32security.GetNamedSecurityInfo(
                fname, win32security.SE_FILE_OBJECT, win32security.DACL_SECURITY_INFORMATION)
            dacl = new_sd.GetSecurityDescriptorDacl()

        if dacl is None:
            self.record_fx(f"{fname} 所在驱动器似乎不支持 NTFS 安全权限", tag=self.LOG_ERROR)
            return 2

        if force and preserve:
            # new_sd.SetAccessRuleProtection(True, False)
            self.record_fx(f"设置文件所有者 - 管理员组")
            new_sd.SetSecurityDescriptorOwner(system_user, 0)
            new_sd.SetSecurityDescriptorOwner(admins, 0)
        if force:
            self.record_fx(f"此文件夹、子文件夹和文件", tag=self.LOG_DEBUG)
            flag = ntsecuritycon.CONTAINER_INHERIT_ACE | ntsecuritycon.OBJECT_INHERIT_ACE  # 此文件夹、子文件夹和文件
            # flag = ntsecuritycon.CONTAINER_INHERIT_ACE | ntsecuritycon.OBJECT_INHERIT_ACE | win32security.INHERIT_ONLY_ACE | win32security.INHERITED_ACE # 同上：此文件夹、子文件夹和文件的一个变种
        else:
            self.record_fx(f"只有此文件夹", tag=self.LOG_DEBUG)
            flag = ntsecuritycon.NO_PROPAGATE_INHERIT_ACE  # 只有此文件夹
        permission = ntsecuritycon.FILE_ALL_ACCESS  # 不给任何权限
        # permission = ntsecuritycon.FILE_GENERIC_READ | ntsecuritycon.FILE_GENERIC_EXECUTE | ntsecuritycon.FILE_LIST_DIRECTORY | ntsecuritycon.FILE_DELETE_CHILD  # 拒绝读取和执行
        self.record_fx(f"{preserve=}, {force=}", tag=self.LOG_DEBUG)
        if preserve is None:
            self.record_fx(f"{fname} 不保护")
            return
        elif preserve:
            if force:
                # new_sd.SetSecurityDescriptorOwner(admins, False)
                dacl.AddAccessDeniedAceEx(win32security.ACL_REVISION, flag, permission, everyone)
            else:
                dacl.AddAccessDeniedAce(win32security.ACL_REVISION, permission, everyone)
        else:
            if force:
                dacl.AddAccessAllowedAceEx(win32security.ACL_REVISION, flag, permission, everyone)
            else:
                #################################
                # deleteAce() 确实可以删除继承的权限
                # 但是似乎每次对 ace 执行操作后，系统会自动检测一遍『已继承的权限』的完整性，如不完整则补齐。
                deleted = []
                for ace_index in range(dacl.GetAceCount()):
                    (ace_type, ace_flags), access_mask, sid = dacl.GetAce(ace_index)
                    name, domain, account_type = win32security.LookupAccountSid(None, sid)
                    # self.record_fx(f"{domain}\\{name}: {hex(ace_flags)}")
                    deleted.append(ace_index)
                for item in deleted:
                    dacl.DeleteAce(0)
                #################################
                dacl.AddAccessAllowedAce(win32security.ACL_REVISION, permission, everyone)
        new_sd.SetSecurityDescriptorDacl(1, dacl, 0)
        if force and not preserve:
            self.record_fx(f"设置文件所有者 - {win32api.GetUserName()}")
            new_sd.SetSecurityDescriptorOwner(user, 0)
        if preserve:
            if force:
                win32security.SetFileSecurity(
                    fname, win32security.DACL_SECURITY_INFORMATION |
                           win32security.OWNER_SECURITY_INFORMATION, new_sd)
            else:
                win32security.SetFileSecurity(
                    fname, win32security.DACL_SECURITY_INFORMATION, new_sd)
        else:
            if force:
                win32security.SetFileSecurity(fname, win32security.DACL_SECURITY_INFORMATION, new_sd)
                # ↑ 用显示权限替换所有权限，不管是显式的还是已继承的
                win32security.SetFileSecurity(fname, win32security.OWNER_SECURITY_INFORMATION, new_sd)
            else:
                # 保留已继承的权限
                win32security.SetNamedSecurityInfo(
                    fname, win32security.SE_FILE_OBJECT,
                    win32security.DACL_SECURITY_INFORMATION, None, None, dacl, None)

    def preserve(self, fname, hidden: bool | None, preserve: bool | None, force: bool = False):
        self.record_fx(f"调用 {self.preserve.__name__} 函数, {fname=}, {hidden=}, {preserve=}, {force=}")
        if preserve is None:
            self.attr_config(fname, hidden)
            # self.ACL_config(fname, preserve)
        elif preserve:
            self.attr_config(fname, hidden)
            self.ACL_config(fname, preserve, force)
        else:
            self.ACL_config(fname, preserve, force)
            self.attr_config(fname, hidden)
        self.record_fx(f"{self.preserve.__name__} 命令成功完成")

    def pattern(self, file_path, return_type="code") -> dict | int:
        # return_type: "code" | "dict"
        #
        # 专门针对驱动器同步的增强
        # 一串 N 位二进制数字
        # 0000000000000000
        # 第 2^0 位：是否存在？
        # 第 2^1 位：是否为驱动器？
        # 第 2^2 位：src 所在驱动器的序列号是否相同？（未实现）
        # 第 2^3 位：src 所在挂载点的 GUID 是否相同？
        # 第 2^4 位：src 所在挂载点的序列号是否存在于【黑】名单
        # 第 2^5 位：src 所在挂载点的序列号是否存在于【白】名单
        # 第 2^6 位：src 所在挂载点的卷标是否存在于【黑】名单
        # 第 2^7 位：src 所在挂载点的卷标是否存在于【白】名单
        cur_exists_ch = 0
        cur_exists_list = dict()

        if exists(file_path):
            cur_exists_ch += 1 * 2 ** 0  # m * n ** p format: 以 n 进制表示的数字串，第 p 位数字为 m
            cur_exists_list.update({"exists": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"exists": False})

        tmp = self.__label2mountId(file_path)
        self.record_fx(f"{file_path} 对应的卷 ID：{tmp}")
        if tmp and tmp != file_path:
            cur_exists_ch += 1 * 2 ** 1
            cur_exists_list.update({"ismount": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"ismount": False})

        id_blk = self.cursors[file_path].get("volumeId_blacklist", self.profileSettings.get("volumeId_blacklist", []))
        if tmp and (not id_blk or tmp in id_blk):
            cur_exists_ch += 1 * 2 ** 4
            cur_exists_list.update({"volumeId_in_blacklist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"volumeId_in_blacklist": False})
        if tmp and tmp in self.cursors[file_path].get(
                "volumeId_whitelist", self.profileSettings.get("volumeId_whitelist", [])):
            cur_exists_ch += 1 * 2 ** 5
            cur_exists_list.update({"volumeId_in_whitelist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"volumeId_in_whitelist": False})

        if self.cursors[file_path]["lastrun"] != tmp:
            cur_exists_ch += 0
            cur_exists_list.update({"samemount": False})
            self.record_fx(f"检测到不同的卷序列号 - {self.cursors[file_path]['lastrun']} ≠ {tmp}")
            self.__rename_and_register(self.cursors[file_path]["dst"], file_path)
        else:
            cur_exists_ch += 1 * 2 ** 3
            cur_exists_list.update({"samemount": True})
            self.record_fx(f"相同的挂载点 - {tmp}")
        self.cursors[file_path].update({"lastrun": tmp})
        # self.record_fx(f"{cur_exists_list}")
        if cur_exists_list.get("exists", False):
            tmp2 = self.__get_volume_label(file_path)
            self.record_fx(f"[{file_path}] 的卷标是 [{tmp2}]")
        else:
            self.record_fx(f"检查卷标时出现错误 - {file_path} 文件不存在", tag=self.LOG_ERROR)
            tmp2 = False
        lab_blk = self.get_fromkey("label_blacklist", file_path)
        if not lab_blk or tmp2 in lab_blk:
            cur_exists_ch += 1 * 2 ** 6
            cur_exists_list.update({"label_in_blacklist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"label_in_blacklist": False})
        if tmp2 in self.get_fromkey("label_whitelist", file_path):
            cur_exists_ch += 1 * 2 ** 7
            cur_exists_list.update({"label_in_whitelist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"label_in_whitelist": False})

        self.record_fx(f"{file_path} 编码的数字串 - {"%.16d" % int(dec_to_r_convert(cur_exists_ch, 2, ))}")
        self.record_fx(f"{file_path} 字典 - {cur_exists_list}")
        if return_type == "code":
            return cur_exists_ch
        else:
            return cur_exists_list

    def before_sync(self, filepath):
        flag = True
        code = self.pattern(filepath, return_type="dict")
        # filepath[0] -> filepath
        # filepath[1] -> self.cursors[filepath]['dst']
        if code.get("exists"):
            safe_md(self.cursors[filepath]["dst"], quiet=True)
            self.record_fx(f"{self.cursors[filepath]["dst"]} 已创建")
        else:
            self.record_fx(f"源文件夹 {filepath} 不存在！")
            if isdir(self.cursors[filepath]["dst"]):
                rmdir(self.cursors[filepath]["dst"])
            else:
                self.record_fx(f"目标文件夹 {self.cursors[filepath]['dst']} 也不存在！")
        if code.get("volumeId_in_whitelist") or code.get("label_in_whitelist"):
            self.record_fx(f"《白名单·悟空》已阻止 {filepath} 的同步")
            flag = False
        if not code.get("volumeId_in_blacklist") or not code.get("label_in_blacklist"):
            self.record_fx(f"《黑名单·悟空》已阻止 {filepath} 的同步")
            flag = False

        return flag

    def run_once(self, delay: float = 0.0, increment_delay: float = 1.0, run_completion="", run_beginning="",
                 save=False):
        """主程序"""
        if self.can_peek(Peeker.OR):
            # old: cmd = "\"" + self.EXE_FP + "\" \"" + self.BATCH_FP + "\""
            if run_beginning:
                # 参数命令 > self 命令 > 不执行
                self.record_fx(f"{self.SYNC_ROOT_FP} 执行参数命令: {run_beginning}")
                command(run_beginning)  # system(run_beginning)
            elif self.run_beginning:
                self.record_fx(f"{self.SYNC_ROOT_FP} 执行默认命令: {self.run_beginning}")
                command(self.run_beginning)
            else:
                self.record_fx("已跳过命令执行")

            for i in self.cursors.keys():
                tmp = self.before_sync(i)

                if tmp:
                    for j in fp_gen(i, abspath=3, files=True, folders=True, precedence_dir=True,
                                    include=self.profileSettings.get("file_blacklist", []),
                                    exclude=self.profileSettings.get("file_whitelist", [])):
                        if not self.sync_flag:
                            self.record_fx("用户终止了同步")
                            break
                        if get_freespace_shutil(self.cursors[i]["dst"]) <= self.reserved_size:
                            self.record_fx(f"硬盘空间不足，停止 {i} 的同步", tag=self.LOG_WARNING)
                            break
                        else:
                            pass
                        sname = join(i, j)
                        fname = join(self.cursors[i]["dst"], j)
                        # ↓在此版本中暂不考虑硬链接等其他文件类型
                        if isfile(sname):
                            if not exists(fname):
                                self.record_fx(f"创建文件: {sname} --> {fname}")
                                try:
                                    copy2(sname, fname)
                                except PermissionError:
                                    self.record_fx("拒绝访问", tag=self.LOG_ERROR)
                                    self.record_exc_info(False)
                                except UnicodeError:
                                    self.record_fx("文件编码错误", tag=self.LOG_ERROR)
                                    self.record_exc_info(False)
                                except FileNotFoundError:
                                    self.record_fx("找不到文件", tag=self.LOG_ERROR)
                                    self.record_exc_info(False)
                                except OSError:
                                    self.record_fx("系统错误：", tag=self.LOG_ERROR)
                                    self.record_exc_info(False)
                                except Exception as e:
                                    self.record_fx("其他错误", tag=self.LOG_ERROR)
                                    self.record_exc_info(False)
                                finally:
                                    yield sname, fname
                            else:
                                # self.__record_fx(f"跳过文件: {fname}")
                                if isfile(fname):
                                    pass
                                else:
                                    self.record_fx(f"创建失败 - {fname} 相对文件已存在、但类型不一致",
                                                   tag=self.LOG_WARNING)
                        elif isdir(sname):
                            # ~~此处偷懒没有加目录存在性判定，因为 safe_md() 函数已经帮我们做好了判定~~
                            # ↑ 已修复
                            if not isdir(fname):
                                self.record_fx(f"创建目录: {fname}")
                                safe_md(fname, quiet=True)
                                copystat(sname, fname)
                            else:
                                pass
                        elif not exists(sname):  # file or dir?
                            self.record_fx(f"错误：{sname} 文件或目录名称不存在", tag=self.LOG_ERROR)
                else:  # 此 else 对应 if
                    self.record_fx("before_sync 条件不足，停止同步")
                del tmp

            if save:
                self.save(False)
            self.last_run_times += 1

            if run_completion:
                self.record_fx(f"{self.SYNC_ROOT_FP} 执行参数命令: {run_completion}")
                command(run_completion)
            elif self.run_completion:
                self.record_fx(f"{self.SYNC_ROOT_FP} 执行默认命令: {run_completion}")
                command(self.run_completion)
            else:
                self.record_fx("已跳过命令执行")
        else:
            self.record_fx(f"不可 peek - {self.last_run_times}")
            if self.last_run_times != 0:
                self.renameall_cur(save=False)
            else:
                self.record_fx("无法重命名")
            self.last_run_times = 0
        delay_var = self.last_run_times * increment_delay + delay
        self.record_fx(f"{self.run_once.__name__}: 等待 {delay_var} 秒")
        self.wait_fx(delay_var)
        self.run_times += 1

    def can_peek(self, factor: int | Literal[OR, AND] = OR, rel=EQU):
        # factor: 至少 factor 个条件满足后继续执行，当此值被设为 AND 或 OR 时，rel 的值将被忽略。
        cur_exists_ch = 0
        self.record_fx("更新的 self.__cursors_src", self.__cursors_src)
        for i in self.__cursors_src:
            if exists(i):
                cur_exists_ch += 1
            else:
                cur_exists_ch += 0

        if (cur_exists_ch == len(self.__cursors_src) and factor == Peeker.AND) or (
                cur_exists_ch != 0 and factor == Peeker.OR):
            return True
        elif (rel == Peeker.EQU and cur_exists_ch == factor) or \
                (rel == Peeker.NEQ and cur_exists_ch != factor) or \
                (rel == Peeker.GTR and cur_exists_ch > factor) or \
                (rel == Peeker.GEQ and cur_exists_ch >= factor) or \
                (rel == Peeker.LSS and cur_exists_ch < factor) or \
                (rel == Peeker.LEQ and cur_exists_ch <= factor):
            return True
        else:
            return False

    def get_cursor_list(self):
        return self.__cursors_src

    def get_solid_list(self):
        return list(map(lambda x: x[0], self.solids))

    def logout(self, arc_mode: int, del_log: bool, del_conf: bool, del_subfile: bool):
        self.record_fx(f"{self.logout.__name__} 注销此实例: {arc_mode=}, {del_log=}, {del_conf=}, {del_subfile=}")
        if arc_mode == 0:
            # 解锁
            self.unlockall_cur(unlock_pre=True, delete=False, untie=True)
        elif arc_mode == 1:
            # 解锁并删除
            self.unlockall_cur(unlock_pre=True, delete=True, untie=True)
        elif arc_mode == 2:
            # 解除逻辑关联（保留物理文件）
            self.unlockall_cur(unlock_pre=False, delete=False, untie=False)
        else:
            self.record_fx(f"参数错误 - {arc_mode}", tag=self.LOG_ERROR)
        self.log_fiet.close()
        self.record_fx = lambda *__text, **kwargs: self.record_ln(
            *__text, local_log=False, global_log=True)
        self.log_fiet_live = False
        if del_conf:
            self.conf_config.clear()
            self.extract_config()
            remove(self.conf_fp)
        if del_log:
            self.delete(self.log_dirp)
        if del_subfile:
            self.delete(self.SYNC_ROOT_FP, excludes=self.exclude_in_del)
        else:
            if not listdir(self.SYNC_ROOT_FP):
                self.delete(self.SYNC_ROOT_FP)
        sys_exit(0)

    def shut(self):
        self.run_times = 0
        self.last_run_times = 0
        self.upgrade_config()
        self.record_fx("已清除同步状态")

    def terminate_sync(self):
        self.record_fx("终止同步：等待当前操作完成")
        self.sync_flag = False

    def run_until(self, *args, **kwargs):
        import warnings
        comment: str = (f"{self.run_until.__name__} 预计在 1.9.4 版本中移除\n"
                        f"使用 self.run_until_gen 函数代替 {self.run_until.__name__}")
        warnings.warn(f"{comment}", DeprecationWarning, stacklevel=4)
        self.record_fx(comment)
        for i in self.run_until_gen(*args, **kwargs):
            pass

    def run_until_gen(
            self, figures: int = INF, end_time: float = INF, delay: float = 0.0,
            increment_delay: float = 0.0, factor2=AND, save=False):
        # 重复执行 run_once() 直到所给条件不成立
        # 当条件被设为 INF 时，意味着永远为真。
        # 没错，不带任何参数的 `run_until()` 就是一个死循环
        def __can_peek():
            b_time = True if end_time == Peeker.INF or time() < end_time else False
            b_run = True if figures == Peeker.INF or self.run_times < figures else False
            if (factor2 == Peeker.AND and (b_time and b_run)) or (factor2 == Peeker.OR and (b_time and b_run)):
                return self.sync_flag & True
            else:
                return self.sync_flag & False

        done = __can_peek()
        while done:
            for j in self.run_once(increment_delay=increment_delay, save=save):
                if self.sync_flag:
                    yield j
                else:
                    break
                    # return 0
            if self.sync_flag:
                done = __can_peek()
                self.record_fx(f"{self.run_until_gen.__name__}: 等待 {delay} 秒")
                self.wait_fx(delay)
            else:
                break

        self.sync_flag = True
        self.record_fx("run_until_gen: 同步旗标已解锁")


if __name__ == "__main__":
    pass
