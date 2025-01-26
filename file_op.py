import win32file
from shutil import disk_usage

__all__ = [
    "set_volume_label",
    "get_freespace_shutil",
]


def set_volume_label(drive, label):
    win32file.SetVolumeLabel(drive, label)
    return label


def get_freespace_shutil(folder):
    _, _, free = disk_usage(folder)
    return free
