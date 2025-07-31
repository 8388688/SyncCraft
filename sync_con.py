# 此文件中涵盖了 SyncCraft 的一些高层逻辑的函数，通常调用自 sync_api.py
# 这些函数可以记录日志
import os
import ntsecuritycon
import pywintypes
import win32api
import win32security
import win32file
from typing import Callable
import traceback

import sclog
from sync_api import *
from constants import *


def init(log_root: sclog.BaseLogging | None = None):
    global _root
    if isinstance(log_root, sclog.BaseLogging):
        _root = log_root
        return log_root
    else:
        raise TypeError("sync_con 日志模块没有初始化")
        # return sclog.BaseLogging("__Rernertikgnteihgbnet__")


def attr_config(self, fname, hidden: bool | None = None):
    self.record_fx(
        f"调用 {self.attr_config.__name__}({fname}) 函数，保护方向：{hidden}")
    if hidden is None:
        _root.info(f"{fname} 不隐藏")
        return
    elif hidden:
        ace = ATTR_READ_ONLY + ATTR_HIDDEN + ATTR_SYSTEM + ATTR_ARCHIVE
    else:
        ace = ATTR_NORMAL
    _root.info(f"Set Attribute: {ace}")
    win32file.SetFileAttributes(fname, ace)


def ACL_config(fname, preserve: bool | None = None, force: bool = False):
    system_user, domain, type_ = win32security.LookupAccountName(
        "", "SYSTEM")
    everyone, domain, type_ = win32security.LookupAccountName(
        "", "Everyone")
    admins, domain, type_ = win32security.LookupAccountName(
        "", "Administrators")
    user, domain, type_ = win32security.LookupAccountName(
        "", win32api.GetUserName())
    all_security_info = (
        win32security.OWNER_SECURITY_INFORMATION
        | win32security.GROUP_SECURITY_INFORMATION
        | win32security.DACL_SECURITY_INFORMATION
        | win32security.SACL_SECURITY_INFORMATION
    )
    _root.info(
        f"调用 {ACL_config.__name__}({fname}) 函数，保护方向：{preserve}，强制模式：{force}")

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
        _root.error(f"{fname} 所在驱动器似乎不支持 NTFS 安全权限")
        return 2

    if force and preserve:
        # new_sd.SetAccessRuleProtection(True, False)
        _root.info(f"设置文件所有者 - 管理员组")
        new_sd.SetSecurityDescriptorOwner(system_user, 0)
        new_sd.SetSecurityDescriptorOwner(admins, 0)
    if force:
        flag = ntsecuritycon.CONTAINER_INHERIT_ACE | ntsecuritycon.OBJECT_INHERIT_ACE  # 此文件夹、子文件夹和文件
        # flag = ntsecuritycon.CONTAINER_INHERIT_ACE | ntsecuritycon.OBJECT_INHERIT_ACE | win32security.INHERIT_ONLY_ACE | win32security.INHERITED_ACE # 同上：此文件夹、子文件夹和文件的一个变种
    else:
        flag = ntsecuritycon.NO_PROPAGATE_INHERIT_ACE  # 只有此文件夹
    permission = ntsecuritycon.FILE_ALL_ACCESS  # 不给任何权限
    # permission = ntsecuritycon.FILE_GENERIC_READ | ntsecuritycon.FILE_GENERIC_EXECUTE | ntsecuritycon.FILE_LIST_DIRECTORY | ntsecuritycon.FILE_DELETE_CHILD  # 拒绝读取和执行
    if preserve is None:
        _root.info(f"{fname} 不保护")
        return
    elif preserve:
        if force:
            # new_sd.SetSecurityDescriptorOwner(admins, False)
            dacl.AddAccessDeniedAceEx(
                win32security.ACL_REVISION, flag, permission, everyone)
        else:
            dacl.AddAccessDeniedAce(
                win32security.ACL_REVISION, permission, everyone)
    else:
        if force:
            dacl.AddAccessAllowedAceEx(
                win32security.ACL_REVISION, flag, permission, everyone)
        else:
            #################################
            # deleteAce() 确实可以删除继承的权限
            # 但是似乎每次对 ace 执行操作后，系统会自动检测一遍『已继承的权限』的完整性，如不完整则补齐。
            deleted = []
            for ace_index in range(dacl.GetAceCount()):
                (ace_type, ace_flags), access_mask, sid = dacl.GetAce(ace_index)
                name, domain, account_type = win32security.LookupAccountSid(
                    None, sid)
                # _root.info(f"{domain}\\{name}: {hex(ace_flags)}")
                deleted.append(ace_index)
            for item in deleted:
                dacl.DeleteAce(0)
            #################################
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION, permission, everyone)
    new_sd.SetSecurityDescriptorDacl(1, dacl, 0)
    if force and not preserve:
        _root.info(f"设置文件所有者 - {win32api.GetUserName()}")
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
            win32security.SetFileSecurity(
                fname, win32security.DACL_SECURITY_INFORMATION, new_sd)
            # ↑ 用显示权限替换所有权限，不管是显式的还是已继承的
            win32security.SetFileSecurity(
                fname, win32security.OWNER_SECURITY_INFORMATION, new_sd)
        else:
            # 保留已继承的权限
            win32security.SetNamedSecurityInfo(
                fname, win32security.SE_FILE_OBJECT,
                win32security.DACL_SECURITY_INFORMATION, None, None, dacl, None)


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
