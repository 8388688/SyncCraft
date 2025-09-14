import os
import json
import random
import shutil
import time
from abc import ABC, abstractmethod
from typing import Literal, AnyStr, MutableSequence

import simple_tools as st

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
        self.logger: sclog.BaseLogging = log_root
        self.src = src
        self.dst = dst
        self.logger.debug(f"type: {self.__class__.sync_type}")

    def is_synchronizable(self) -> bool:
        # 当前是否具备了开始同步的条件。
        return os.path.exists(self.src)

    def list_src(self, __fp, topdown=True):
        """

        以【相对路径】的方式，
        【按同步的顺序】逐个地输出 __fp 中【应该被同步的】文件 \\
        （意即在某些情况下不必输出 src 下的全部文件）。

        传入的 __fp 必须是目录
        """
        for i in os.listdir(__fp):
            fullpath = os.path.join(__fp, i)
            if os.path.isdir(fullpath):
                if topdown:
                    yield i  # 也输出文件夹
                for j in self.list_src(fullpath):
                    yield os.path.join(i, j)
                if not topdown:
                    yield i
            else:
                yield i

    def sync(self):
        # 同步的核心代码写在这里
        # 请不要在外部程序直接调用这个函数，而应该使用更加健壮性的 run() 函数
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
                    shutil.copystat(src_fullpath, dst_fullpath)
                    self.logger.notice(
                        f"copying dir: {src_fullpath} --> {dst_fullpath}")
            else:
                self.logger.notice(
                    f"skipping: {src_fullpath} --> {dst_fullpath}")

    def run(self) -> None:
        # 执行同步，本函数没有返回值。
        if self.is_synchronizable():
            if not os.path.exists(self.dst):
                self.logger.warning(f"目标根文件夹不存在 - {self.dst}")
                os.makedirs(self.dst)
            self.sync()
        else:
            self.logger.notice(f"{self.src}: is_synchronizable 不允许同步")


class SolidSync(BaseSynchronization):
    """固实同步，同步完成后会保护 dst 文件夹

    """
    sync_type = "solid"

    def __init__(self, log_root, src, dst):
        super().__init__(log_root, src, dst)

    def run(self):
        # run_beginning
        if os.path.exists(self.dst):
            sync_con.ACL_config(self.dst, False)
        else:
            self.logger.info(f"{self.dst} 不存在")
        super().run()
        # run_completion
        if os.path.exists(self.src):
            # 这里进行存在性检查是为了向后兼容做考虑
            sync_con.ACL_config(self.dst, True)
        else:
            self.logger.info(f"{self.dst} 不存在")


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
    FILE_TYPE = "file"
    DIR_TYPE = "dir"

    def __init__(self, log_root, src, dst, move_files=dict(), touch_files=dict()):
        super().__init__(log_root, src, dst)
        self.move_files = move_files
        # {src1: dst1, src2: dst2, ...}
        # src 不为空而 dst 为空，表示 rm 文件
        # src, dst 都不为空表示 mv 文件
        self.pur_prior = False
        # True 为替换文件优先于同步，反之则为同步优先于替换
        self.put_in_force = False
        # 是否强制替换已存在的文件
        self.touch_files = touch_files
        # {fp1: filetype1, fp2: filetype2}

    def touch_file_api(self, fp):
        open(fp, "wb").close()

    def touch_dir_api(self, fp):
        os.makedirs(fp, exist_ok=False)

    def move_file_api(self, src, dst):
        shutil.move(self, src, dst)

    def move_dir_api(self, src, dst):
        shutil.move(self, src, dst)

    def del_file_api(self, fp):
        os.unlink(fp)

    def del_dir_api(self, fp):
        os.rmdir(fp)

    def touch(self, fp, filetype):
        """创建文件，注意 fp 【不是】相对路径（但不一定是绝对路径）"""
        self.logger.info(f"要检测的文件: {fp}")
        if not os.path.exists(fp) or self.put_in_force:
            if os.path.exists(fp):
                self.logger.notice(f"replace(强制替换): {fp}")
                self.delete(fp)
            if filetype == self.__class__.FILE_TYPE:
                self.logger.notice(f"make file: {fp}")
                self.touch_file_api(fp)
            elif filetype == self.__class__.DIR_TYPE:
                self.logger.notice(f"make dir: {fp}")
                self.touch_dir_api(fp)
            else:
                self.logger.error(f"TypeError: 错误的文件类型 - {filetype}")
        else:
            self.logger.error(f"{fp} - File already exists")

    def move(self, src, dst):
        """移动 & 重命名文件"""
        if os.path.dirname(src) == dst:
            self.logger.warning(f"{src} 的目标文件夹和 {dst} 是同一文件夹")
            return
        if os.path.isfile(dst):
            self.logger.error(
                f"Cannot move {src} to {dst} - File already exists.")
        else:
            self.logger.notice(f"move: {src} --> {dst}")
            self.move_file_api(src, dst)

    def delete_single(self, fp_or_dirp):
        # fp_or_dirp 是【绝对路径】
        if os.path.exists(fp_or_dirp):
            if os.path.isfile(fp_or_dirp):
                self.logger.notice(f"delete file: {fp_or_dirp}")
                self.del_file_api(fp_or_dirp)
            elif os.path.isdir(fp_or_dirp):
                self.logger.notice(f"delete dir: {fp_or_dirp}")
                self.del_dir_api(fp_or_dirp)
            else:
                self.logger.warning(f"{fp_or_dirp} - unknown file type.")
                self.del_file_api(fp_or_dirp)
        else:
            self.logger.error(f"delete failed - {fp_or_dirp} not found.")

    def delete(self, fp):
        # 同上，绝对路径
        for i in self.list_src(fp, topdown=False):
            i_fullpath = os.path.join(fp, i)
            self.delete_single(i_fullpath)
        else:
            self.del_dir_api(fp)

    def touch_pr(self, dst: dict, root_fp):
        # dst 中的格式均为【相对路径】，这与 delete、touch 和 move 都不一样
        for k, v in dst.items():
            self.touch(os.path.join(root_fp, k), v)

    def sync(self):
        temp_remove: list = []  # 记录格式：【相对】路径
        for k, v in self.move_files.items():
            if k and not v:
                temp_remove.append(k)
        self.logger.debug(f"{self.move_files=}, {temp_remove=}")
        ################
        # 这一框代码会在后面有重复
        if self.pur_prior:
            self.touch_pr(self.touch_files, self.src)
            for k in temp_remove:
                # TODO: 是用 delete 还是用 delete_single 函数？
                self.delete(os.path.join(self.src, k))
        ################
        for i in self.list_src(self.src):
            # i: 相对路径
            self.logger.debug(f"{i=}")
            src_fullpath = os.path.join(self.src, i)
            dst_fullpath = os.path.join(self.dst, i)
            if os.path.isfile(src_fullpath):
                if not os.path.exists(dst_fullpath):
                    # dst 对应路径不存在文件，执行同步
                    shutil.copy2(src_fullpath, dst_fullpath)
                    self.logger.notice(
                        f"copying file: {src_fullpath} --> {dst_fullpath}")
                else:
                    self.logger.notice(
                        f"skipping file: {src_fullpath} --> {dst_fullpath}")
                if not self.pur_prior and (os.path.dirname(i) in temp_remove or i in temp_remove):
                    self.delete_single(src_fullpath)
            else:
                if not os.path.exists(dst_fullpath):
                    os.mkdir(dst_fullpath)
                    shutil.copystat(src_fullpath, dst_fullpath)
                    self.logger.notice(
                        f"copying dir: {src_fullpath} --> {dst_fullpath}")
                else:
                    self.logger.notice(
                        f"skipping dir: {src_fullpath} --> {dst_fullpath}")

                if os.path.dirname(i) in temp_remove:
                    temp_remove.append(i)
            #############
            if i in self.move_files.keys():
                if self.move_files[i]:
                    # move 函数中本身已经记录了日志，这里就无需二遍记录了
                    if os.path.isabs(self.move_files[i]):
                        self.logger.info(f"绝对路径：修正后为 {self.move_files[i]}")
                        self.move(src_fullpath, self.move_files[i])
                    else:
                        self.logger.info(f"相对路径：修正后为 {os.path.join(
                            self.src, self.move_files[i])}")
                        self.move(src_fullpath, os.path.join(
                            self.src, self.move_files[i]))
                else:
                    # delete 同上
                    self.logger.info(
                        f"不要重复删除：{src_fullpath}")
            #############
        if not self.pur_prior:
            self.touch_pr(self.touch_files, self.src)
            self.logger.debug(f"{temp_remove=}")
            for k in reversed(temp_remove):
                # TODO: 是用 delete 还是用 delete_single 函数？
                self.delete_single(os.path.join(self.src, k))

    def run(self):
        return super().run()


class RepSpp(ReplacementSync):
    """替换文件增强版

    这个类对删除文件的方法进行了增强，并添加了白名单机制
    """
    sync_type = "replacement++"

    def __init__(self, log_root, src, dst, move_files=dict(), touch_files=dict(), del_type=0, after_delete=True):
        super().__init__(log_root, src, dst, move_files, touch_files)
        self.del_type = del_type
        self.after_delete = after_delete
        # 0 = 继承父类的删除动作
        # 1 = 清空文件内容
        # 2 = 随机数据填充
        # 3 = 零字节填充
        self.whitelist = []  # TODO: NotImplemented: 实际上尚未使用
        self.BUFFER = 131072  # 缓冲区大小

    def appendtowhitelist(self, fp):
        self.whitelist.append(fp)

    def delete_single(self, fp):
        # fp 是【绝对路径】
        if os.path.exists(fp):
            if os.path.isfile(fp):
                self.logger.notice(f"delete file: {fp}")

                self.logger.notice(f"删除 {fp} - {self.del_type=}")
                if self.del_type == 0:
                    return super().__del_file_api(fp)
                if self.del_type == 1:
                    open(fp, "wb").close()
                    self.logger.debug("清空文件内容")
                    self.appendtowhitelist(fp)
                elif self.del_type == 2:
                    size = os.path.getsize(fp)
                    cycle, remain = divmod(size, self.BUFFER)
                    with open(fp, "wb") as f:
                        for i in range(cycle):
                            buffer = bytearray()
                            self.logger.debug(f"随机数据填充 - 第 {i + 1} 轮循环")
                            for j in range(self.BUFFER):
                                buffer.append(int(random.random() * 128))
                            f.write(buffer)
                        buffer = bytearray()
                        self.logger.debug("随机数据填充 - 剩余文件碎片")
                        for j in range(remain):
                            buffer.append(int(random.random() * 128))
                        f.write(buffer)
                    del buffer
                    self.appendtowhitelist(fp)
                elif self.del_type == 3:
                    size = os.path.getsize(fp)
                    cycle, remain = divmod(size, self.BUFFER)
                    buffer = bytes(self.BUFFER)
                    with open(fp, "wb") as f:
                        for i in range(cycle):
                            self.logger.debug(f"零字节填充 - 第 {i + 1} 轮循环")
                            f.write(buffer)
                        buffer = bytes(remain)
                        self.logger.debug("零字节填充 - 剩余文件碎片")
                        f.write(buffer)
                    del buffer
                    self.appendtowhitelist(fp)

                if self.after_delete:
                    return self.del_file_api(fp)

            elif os.path.isdir(fp):
                if self.after_delete:
                    self.logger.notice(f"delete dir: {fp}")
                    self.del_dir_api(fp)
            else:
                if self.after_delete:
                    self.logger.warning(f"{fp} - unknown file type.")
                    self.del_file_api(fp)
        else:
            self.logger.error(f"delete failed - {fp} not found.")


class DeviceSync(BaseSynchronization):
    sync_type = "device"

    def __init__(self, log_root, src, dst):
        super().__init__(log_root, src, dst)

    def run(self):
        root_fp = os.path.splitdrive(self.src)[0]
        if not root_fp.endswith(os.sep):
            root_fp += os.sep
        self.logger.info(f"检查 [{root_fp}] 的卷标")
        tmp_label = sync_con.get_volume_label(root_fp)
        if tmp_label is not None:
            self.logger.notice(f"[{root_fp}] 的卷标是 [{tmp_label}]")
        else:
            self.logger.error(f"检查 [{root_fp}] 的卷标失败")
        self.logger.info(f"检查 [{root_fp}] 的卷 ID")
        tmp_label = sync_con.label2mountId(root_fp)
        if tmp_label:
            self.logger.notice(f"[{root_fp}] 的卷 ID 是 [{tmp_label}]")
        else:
            self.logger.error(f"检查 [{root_fp}] 的卷 ID 失败")
        super().run()


class LO_Sync(BaseSynchronization):
    # list only，只列取文件目录，而不进行同步
    def sync(self):
        for i in self.list_src(self.src):
            src_fullpath = os.path.join(self.src, i)
            dst_fullpath = os.path.join(self.dst, i)
            if os.path.isfile(src_fullpath):
                self.logger.notice(
                    f"listing file: {src_fullpath} --> {dst_fullpath}")
            else:
                self.logger.notice(
                    f"listing dir: {src_fullpath} --> {dst_fullpath}")


all_instance: tuple[type[BaseSynchronization]] = (
    SolidSync, CursorSync,
    ReplacementSync, DeviceSync,
    RepSpp,
)
all_showing_instance = ((i, i.sync_type) for i in all_instance)


def get_config(fp):
    with open(fp, "rb") as f:
        result = json.loads(f.read())
    return result


def put_config(fp, json0):
    with open(fp, "w", encoding="utf-8") as f:
        f.write(json.dumps(json0, ))


def read_instance(log_root: sclog.BaseLogging, cfg):
    """通常来说，读取目录应该为 instance.sc_conf"""
    for i in cfg.keys():
        for j in all_instance:
            if j.sync_type == i:
                # make instance
                for inst in cfg[i]:
                    yield j(log_root=log_root, **inst)


__all__ = [
    "all_instance", "all_showing_instance",

    "BaseSynchronization",
    "SolidSync",
    "CursorSync",
    "ReplacementSync",
    "RepSpp",
    "DeviceSync",

    "get_config", "put_config", "read_instance"
]
