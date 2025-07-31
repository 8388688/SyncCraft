import os
from abc import ABC, abstractmethod
from typing import Literal, AnyStr, MutableSequence
import simple_tools as st
import shutil
import time

import sync_api
import sync_con
import sclog

__version__ = "2.0.0-Alpha1"
build_time = 1744214400
TITLE = "SyncCraft"
K_PORTABLE = True
"""
rate_list = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB")
global_settings_dirp = os.path.join(os.getenv("APPDATA"), TITLE)
os.makedirs(global_settings_dirp, exist_ok=True)
global_settings_fp = os.path.join(
    global_settings_dirp, "globalsettings.sc_json")
"""

# class Archiver:
#     """存档管理"""
#     pass


class BaseSynchronization_old():
    # 将被弃用

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

        self.label_blacklist: MutableSequence = []
        self.label_whitelist: MutableSequence = []
        self.volId_blacklist: MutableSequence = []
        self.volId_whitelist: MutableSequence = []
        self.file_blacklist: MutableSequence = []
        self.file_whitelist: MutableSequence = []
        self.reserved_size: int = 0

        self.archives: MutableSequence = []

        self.lastrun_volId = ""

    def run(self):
        # raise NotImplementedError("子类必须实现 run 方法")
        tmp = self.get_factor(self.src)
        if tmp:
            for j in st.fp_gen(
                    self.src, abspath=3, files=True, folders=True, precedence_dir=True,
                    include=self.file_blacklist, exclude=self.file_whitelist):
                if not self.sync_flag:
                    sclog.info("用户终止了同步")
                    break
                if get_freespace_shutil(self.dst) <= self.reserved_size:
                    sclog.warn(f"硬盘空间不足，停止 {self.src} 的同步")
                    break
                else:
                    pass
                sname = os.path.join(self.src, j)
                fname = os.path.join(self.dst, j)
                # ↓在此版本中暂不考虑硬链接等其他文件类型
                if os.path.isfile(sname):
                    if not os.path.exists(fname):
                        self.record_fx(f"创建文件: {sname} --> {fname}")
                        try:
                            shutil.copy2(sname, fname)
                        except UnicodeError:
                            self.record_fx("文件编码错误", tag=self.LOG_ERROR)
                            self.record_exc_info(False)
                        except OSError as e:
                            self.record_fx("系统错误：", tag=self.LOG_ERROR)
                            self.record_fx(
                                f"Cannot process file {sname} --> {fname}"
                                f" \"{e.filename if e.filename is not None else ''}\","
                                f" \"{e.filename2 if e.filename2 is not None else ''}\""
                                f" Error Code {e.winerror}: {e.strerror}"
                                f" ( = {e.errno})",
                                tag=self.LOG_ERROR)
                            self.record_exc_info(True)
                        except Exception as e:
                            sclog.error("其他错误")
                            self.record_exc_info(True)
                        finally:
                            yield sname, fname
                    else:
                        # self.__record_fx(f"跳过文件: {fname}")
                        if os.path.isfile(fname):
                            pass
                        else:
                            sclog.warning(f"创建失败 - {fname} 相对文件已存在、但类型不一致")
                elif os.path.isdir(sname):
                    # ~~此处偷懒没有加目录存在性判定，因为 safe_md() 函数已经帮我们做好了判定~~
                    # ↑ 已修复
                    if not os.path.isdir(fname):
                        self.record_fx(f"创建目录: {fname}")
                        st.safe_md(fname, quiet=True)
                        shutil.copystat(sname, fname)
                    else:
                        pass
                elif not os.path.exists(sname):  # file or dir?
                    sclog.error(f"错误：{sname} 文件或目录名称不存在")
        else:  # 此 else 对应 if
            sclog.info("before_sync 条件不足，停止同步")

    def get(self, attribute: AnyStr, default=None):
        if hasattr(self, attribute):
            return getattr(self, attribute)
        else:
            return default

    def get_new_name(self, old_name: AnyStr):
        return old_name + get_time

    def archive(self, __fp=None):
        if __fp is None:
            __fp = self.dst
        new_name = __fp + get_time("%Y%m%d%H%M%S")
        os.rename(__fp, new_name)

    def get_factor(self, file_path=None, return_type: Literal["code", "int"] = "code") -> dict | int:
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
        if file_path is None:
            file_path = self.src

        if os.path.exists(file_path):
            cur_exists_ch += 1 * 2 ** 0  # m * n ** p format: 以 n 进制表示的数字串，第 p 位数字为 m
            cur_exists_list.update({"exists": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"exists": False})

        tmp = label2mountId(file_path)
        sclog.info(f"{file_path} 对应的卷 ID: {tmp}")
        if tmp and tmp != file_path:
            cur_exists_ch += 1 * 2 ** 1
            cur_exists_list.update({"ismount": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"ismount": False})

        if tmp and (not self.volId_blacklist or tmp in self.volId_blacklist):
            cur_exists_ch += 1 * 2 ** 4
            cur_exists_list.update({"volumeId_in_blacklist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"volumeId_in_blacklist": False})
        if tmp and tmp in self.volumeId_whitelist:
            cur_exists_ch += 1 * 2 ** 5
            cur_exists_list.update({"volumeId_in_whitelist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"volumeId_in_whitelist": False})

        """
        if self.lastrun != tmp:
            cur_exists_ch += 0
            cur_exists_list.update({"samemount": False})
            sclog.info(f"检测到不同的卷序列号 - {self.cursors[file_path]['lastrun']} ≠ {tmp}")
            self.__rename_and_register(self.cursors[file_path]["dst"], file_path)
        else:
            cur_exists_ch += 1 * 2 ** 3
            cur_exists_list.update({"samemount": True})
            sclog.info(f"相同的挂载点 - {tmp}")
        self.cursors[file_path].update({"lastrun": tmp})
        # sclog.info(f"{cur_exists_list}")
        """
        if cur_exists_list.get("exists", False):
            tmp2 = get_volume_label(file_path)
            sclog.info(f"[{file_path}] 的卷标是 [{tmp2}]")
        else:
            sclog.error(f"检查卷标时出现错误 - {file_path} 文件不存在")
            tmp2 = False
        if not self.label_blacklist or tmp2 in self.label_blacklist:
            cur_exists_ch += 1 * 2 ** 6
            cur_exists_list.update({"label_in_blacklist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"label_in_blacklist": False})
        if tmp2 in self.label_whitelist:
            cur_exists_ch += 1 * 2 ** 7
            cur_exists_list.update({"label_in_whitelist": True})
        else:
            cur_exists_ch += 0
            cur_exists_list.update({"label_in_whitelist": False})

        sclog.info(
            f"{file_path} 编码的数字串 - {"%.16d" % int(st.dec_to_r_convert(cur_exists_ch, 2, ))}")
        sclog.info(f"{file_path} 字典 - {cur_exists_list}")
        if return_type == "code":
            return cur_exists_ch
        else:
            return cur_exists_list


class BaseSynchronization:
    """“同步”的抽象基类

    对于任意一个 Sync
    子类至少要实现的方法和声明的属性如下
    Attributes:
        logger: 日志记录的实例，所有的记录日志的行为都通过本属性
        src: 同步的源文件夹
        dst: 同步的目标文件夹
    """
    sync_type = "BaseSynchronization"  # 子类必须重写 sync_type 类变量，并且此方法对于实例来说为只读

    def __init__(self, log_root: sclog.BaseLogging, src, dst):
        self.logger = log_root
        self.src = src
        self.dst = dst
        self.logger.notice(f"type: {self.__class__.sync_type}")

    def is_synchronizable(self) -> bool:
        # 当前是否具备了开始同步的条件。
        return os.path.exists(self.src)

    def list_src(self, __fp):
        """

        以【相对路径】的方式，
        【按同步的顺序】逐个地输出 src 中【应该被同步的】文件 \\
        （意即在某些情况下不必输出 src 下的全部文件）。
        """
        for i in os.listdir(__fp):
            fullpath = os.path.join(__fp, i)

            if os.path.isdir(fullpath):
                yield i  # 也输出文件夹
                for j in self.list_src(fullpath):
                    yield os.path.join(i, j)
            else:
                yield i

    def run(self) -> None:
        # 执行同步，本函数没有返回值。
        if self.is_synchronizable():
            for i in self.list_src(self.src):
                src_fullpath = os.path.join(self.src, i)
                dst_fullpath = os.path.join(self.dst, i)
                if not os.path.exists(dst_fullpath):
                    if os.path.isfile(src_fullpath):
                        shutil.copy2(src_fullpath, dst_fullpath)
                        self.logger.notice(
                            f"copying file: {src_fullpath} --> {dst_fullpath}")
                    else:
                        os.mkdir(dst_fullpath)
                        self.logger.notice(
                            f"copying dir:{src_fullpath} --> {dst_fullpath}")
                else:
                    self.logger.notice(
                        f"skipping: {src_fullpath} --> {dst_fullpath}")
        else:
            self.logger.notice(f"{self.src}: is_synchronizable 不允许同步")


class SolidSync(BaseSynchronization):
    sync_type = "solid"

    def __init__(self, log_root, src, dst):
        super().__init__(log_root, src, dst)

    def run(self):
        # run_beginning
        sync_con.ACL_config(self.dst, False)
        super().run()
        # run_completion
        sync_con.ACL_config(self.dst, True)


class CursorSync(BaseSynchronization):
    sync_type = "cursor"

    def __init__(self, log_root, src, dst):
        super().__init__(log_root, src, dst)

    @staticmethod
    def get_new_fname(fp):
        return os.path.normpath(fp) + time.strftime("%Y%m%d%H%M%S")

    def run(self):
        if not os.path.exists(self.dst):
            os.mkdir(self.dst)
        super().run()
        os.rename(self.dst, self.get_new_fname(self.dst))


class ReplacementSync(BaseSynchronization):
    """Trojan: 同步四大基类中唯一一个能够操作 src 中文件的类"""
    sync_type = "replacement"

    def __init__(self, log_root, src, dst):
        super().__init__(log_root, src, dst)
        self.touch_files = []
        self.move_files = []
        self.delete_files = []

    def touch(self, fp):
        """创建文件"""
        pass

    def move(self, fp):
        """移动 & 重命名文件"""
        pass

    def delete(self, fp):
        pass

    def run(self):
        # 完全重写 BaseSynchronziation 的父类
        if self.is_synchronizable():
            for i in self.list_src(self.src):
                src_fullpath = os.path.join(self.src, i)
                dst_fullpath = os.path.join(self.dst, i)
                if not os.path.exists(dst_fullpath):
                    if os.path.isfile(src_fullpath):
                        shutil.copy2(src_fullpath, dst_fullpath)
                        self.logger.notice(
                            f"copying file: {src_fullpath} --> {dst_fullpath}")
                    else:
                        os.mkdir(dst_fullpath)
                        self.logger.notice(
                            f"copying dir:{src_fullpath} --> {dst_fullpath}")
                else:
                    self.logger.notice(
                        f"skipping: {src_fullpath} --> {dst_fullpath}")


class DeviceSync(BaseSynchronization):
    sync_type = "device"


if __name__ == "__main__":
    bs = sclog.BaseLogging("KMKMKMK", "G:\\Temp\\l.txt", "G:\\Temp\\g.txt")
    sync_con.init(bs)
    test = CursorSync(
        bs, "D:\\foo", "D:\\bar")
    test.run()
