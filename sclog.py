import logging
import colorlog


class BaseLogging(logging.Logger):
    """SyncCraft 基本日志"""
    L_INFO = logging.INFO
    L_FATAL = L_CRITICAL = logging.CRITICAL
    L_ERROR = logging.ERROR
    L_WARN = L_WARNING = logging.WARNING
    L_DEBUG = logging.DEBUG
    L_NOTSET = logging.NOTSET
    # 自定义日志等级
    L_NOTICE = logging.INFO + 1

    ASC_TIME_FORMAT = "%Y-%m-%dT%H.%M.%SZ"

    def __init__(self, name: str, local_log_fp, global_log_fp):
        super().__init__(name)
        logging.addLevelName(self.L_NOTICE, "NOTICE")  # 设置自定义日志级别的名称
        self.setLevel(logging.DEBUG)

        self.console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s.%(msecs)03d] %(filename)s -> %(name)s %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s",
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
            "[%(asctime)s.%(msecs)03d] %(filename)s -> %(name)s%(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s",
            datefmt=self.ASC_TIME_FORMAT,
        )

        self.local_log = logging.FileHandler(local_log_fp, encoding="utf-8")
        # self.local_log.setLevel(logging.DEBUG)
        self.local_log.setFormatter(self.file_formatter)
        self.global_log = logging.FileHandler(global_log_fp, encoding="utf-8")
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
    
    def terminate(self):
        self.local_log.close()
        self.global_log.close()


_root = BaseLogging("Temporary", "D:\\MeadEyetoe_FileTemp\\taskmgr_agent\\l.log", "D:\\MeadEyetoe_FileTemp\\taskmgr_agent\\g.g.g.llog")
debug = _root.debug
info = _root.info
warn = warning = _root.warning
error = _root.error
fatal = critical = _root.critical
notice = _root.notice
exception = _root.exception


if __name__ == "__main__":
    pass
