import colorlog, os
import logging
from abc import ABC, abstractmethod
from typing import Literal


class BaseLogging(logging.Logger):
    """SyncCraft 基本日志"""
    L_INFO = logging.INFO
    L_CRITICAL = logging.CRITICAL
    L_FATAL = L_CRITICAL
    L_ERROR = logging.ERROR
    L_WARNING = logging.WARNING
    L_WARN = L_WARNING
    L_DEBUG = logging.DEBUG
    L_NOTSET = logging.NOTSET
    # 自定义日志等级
    L_NOTICE = logging.INFO + 1

    ASC_TIME_FORMAT = "%Y-%m-%dT%H.%M.%SZ"

    def __init__(self, name: str):
        super().__init__(name)
        logging.addLevelName(self.L_NOTICE, "NOTICE")  # 设置自定义日志级别的名称
        self.setLevel(logging.DEBUG)

        self.console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s",
            datefmt=self.ASC_TIME_FORMAT,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "NOTICE": "cyan",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red,bg_white",
            }
        )
        self.file_formatter = logging.Formatter(
            "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s",
            datefmt=self.ASC_TIME_FORMAT,
        )

        self.local_log = logging.FileHandler("G:\\Temp\\log.txt", encoding="utf-8")
        # self.local_log.setLevel(logging.DEBUG)
        self.local_log.setFormatter(self.file_formatter)
        self.global_log = logging.FileHandler("G:\\Temp\\glog.txt", encoding="utf-8")
        self.global_log.setFormatter(self.file_formatter)

        # 使用StreamHandler输出到屏幕
        self.console = logging.StreamHandler()
        # self.console.setLevel(logging.DEBUG)
        self.console.setFormatter(self.console_formatter)

        if not self.handlers:
            self.addHandler(self.console)
            self.addHandler(self.local_log)
            self.addHandler(self.global_log)
        self.console.close()
        self.local_log.close()
        self.global_log.close()

    # def log(self, *__text, tag, sep=" ", end="\n"):
        # msg = sep.join(str(i) for i in __text) + end
        # super().log(level=tag, msg=msg, *tuple())

    def notice(self, msg, *args, **kwargs):
        if self.isEnabledFor(self.L_NOTICE):
            self._log(self.L_NOTICE, msg, args, **kwargs)

    def commit(self):
        self.local_log.flush()
        self.global_log.flush()


class Archiver:
    """存档管理"""
    pass


class BaseSynchronization(ABC):
    sync_type = ""  # 子类必须重写 sync_type 方法，并且此方法对于实例来说为只读
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

        self.archives = []

    @abstractmethod
    def run(self):
        raise NotImplementedError("子类必须实现 run 方法")

    def get_factor(self, file_path, return_type: Literal["code", "int"]="code") -> dict | int:
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

        if os.path.exists(file_path):
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



class SolidSync(BaseSynchronization):
    sync_type = "solid"

    def run(self):
        pass


class CursorSync(BaseSynchronization):
    sync_type = "cursor"


class ReplacementSync(BaseSynchronization):
    sync_type = "replacement"


class DeviceSync(BaseSynchronization):
    sync_type = "device"


if __name__ == "__main__":
    pass