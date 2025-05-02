import colorlog, colorama
import logging
from abc import ABC, abstractmethod
from typing import AnyStr


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
        logging.addLevelName(self.L_NOTICE, "NOTICE")  # 设置自定义日志级别的名称
        self.setLevel(logging.DEBUG)
        self.general_formatter = logging.Formatter(
            "[%(asctime)s | %(name)s]%(levelname)s: %(message)s",
            datefmt=self.ASC_TIME_FORMAT,
        )
        self.color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': "red,bg_white",
        }
    )

        # 使用FileHandler输出到文件
        self.local_log = logging.FileHandler("G:\\Temp\\log.txt", encoding="utf-8")
        # local_log.setLevel(logging.DEBUG)
        self.local_log.setFormatter(self.general_formatter)
        self.global_log = logging.FileHandler("G:\\Temp\\loggg.txt", encoding="utf-8")
        self.global_log.setFormatter(self.general_formatter)

        # 使用StreamHandler输出到屏幕
        self.console = logging.StreamHandler()
        # ch.setLevel(logging.DEBUG)
        self.console.setFormatter(self.general_formatter)

        self.addHandler(self.console)
        self.addHandler(self.local_log)
        self.addHandler(self.global_log)

    # def log(self, *__text, tag, sep=" ", end="\n"):
        # msg = sep.join(str(i) for i in __text) + end
        # super().log(level=tag, msg=msg, *tuple())

    def _notice(self, msg, *args, **kwargs):
        if self.isEnabledFor(self.L_NOTICE):
            self.log(self.L_NOTICE, msg, *args, **kwargs)

    notice = _notice



class Archiver:
    """存档管理"""
    pass


class BaseSynchronization(ABC):
    @abstractmethod
    def __init__(self):
        # raise NotImplementedError("子类必须实现这个方法")
        pass


class SolidSync(BaseSynchronization):
    pass


class CursorSync(BaseSynchronization):
    pass


class ReplacementSync(BaseSynchronization):
    pass


class DeviceSync(BaseSynchronization):
    pass


if __name__ == '__main__':
    g2 = logging.getLogger("abcc")
    g2.setLevel(3)
    print(g2.getEffectiveLevel())
    g = BaseLogging("DFG")
    g.setLevel(8)
    g.debug("CNM")
    g.error("CNNH")
    g.notice("NOTICE")
