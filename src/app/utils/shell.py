# pylint: skip-file
import ctypes.wintypes
import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

from win32com.shell import shell, shellcon
import win32file
import win32api
import win32con
import pythoncom
import winshell
import win32gui
import threading
import fnmatch

from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


def fail(text: str):
    logger.critical(text)
    raise RuntimeError(text)


_SEE_MASK_NOCLOSEPROCESS = 0x00000040
_SEE_MASK_INVOKEIDLIST = 0x0000000C


class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = (
        ("cbSize", ctypes.wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", ctypes.wintypes.HANDLE),
        ("lpVerb", ctypes.c_wchar_p),
        ("lpFile", ctypes.c_wchar_p),
        ("lpParameters", ctypes.c_char_p),
        ("lpDirectory", ctypes.c_char_p),
        ("nShow", ctypes.c_int),
        ("hInstApp", ctypes.wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", ctypes.c_char_p),
        ("hKeyClass", ctypes.wintypes.HKEY),
        ("dwHotKey", ctypes.wintypes.DWORD),
        ("hIconOrMonitor", ctypes.wintypes.HANDLE),
        ("hProcess", ctypes.wintypes.HANDLE),
    )


ShellExecuteEx = ctypes.windll.shell32.ShellExecuteExW
ShellExecuteEx.restype = ctypes.wintypes.BOOL


def copy(src, dst: str, auto_rename: bool) -> bool:
    """
    Copy files and directories using Windows shell.

    :param src: Path or a list of paths to copy. Filename portion of a path
                (but not directory portion) can contain wildcards ``*`` and
                ``?``.
    :param dst: destination directory.
    :param auto_rename: if ''False'' then overwrite else auto rename
    :returns: ``True`` if the operation completed successfully,
              ``False`` if it was aborted by user (completed partially).
    :raises: ``WindowsError`` if anything went wrong. Typically, when source
             file was not found.

    .. seealso:
        `SHFileperation on MSDN <http://msdn.microsoft.com/en-us/library/windows/desktop/bb762164(v=vs.85).aspx>`
    """
    if isinstance(src, str):  # in Py3 replace basestring with str
        src = os.path.abspath(src)
    else:  # iterable
        src = "\0".join(os.path.abspath(path) for path in src)

    flags = shellcon.FOF_NOCONFIRMMKDIR
    if auto_rename:
        flags = flags | shellcon.FOF_RENAMEONCOLLISION

    result, aborted = shell.SHFileOperation((0, shellcon.FO_COPY, src, os.path.abspath(dst), flags, None, None))

    if not aborted and result != 0:
        # Note: raising a WindowsError with correct error code is quite
        # difficult due to SHFileOperation historical idiosyncrasies.
        # Therefore we simply pass a message.
        raise Exception("Cannot copy. Windows error - SHFileOperation failed: 0x%08x" % result)

    return not aborted


def move(src, dst: str, auto_rename: bool = False) -> bool:
    """
    Move files and directories using Windows shell.

    :param src: Path or a list of paths to copy. Filename portion of a path
                (but not directory portion) can contain wildcards ``*`` and
                ``?``.
    :param dst: destination directory.
    :param auto_rename: if ''False'' then overwrite else auto rename
    :returns: ``True`` if the operation completed successfully,
              ``False`` if it was aborted by user (completed partially).
    :raises: ``WindowsError`` if anything went wrong. Typically, when source
             file was not found.

    .. seealso:
        `SHFileperation on MSDN <http://msdn.microsoft.com/en-us/library/windows/desktop/bb762164(v=vs.85).aspx>`
    """
    if isinstance(src, str):  # in Py3 replace basestring with str
        src = os.path.abspath(src)
    else:  # iterable
        src = "\0".join(os.path.abspath(path) for path in src)

    flags = shellcon.FOF_NOCONFIRMMKDIR
    if auto_rename:
        flags = flags | shellcon.FOF_RENAMEONCOLLISION

    result, aborted = shell.SHFileOperation((0, shellcon.FO_MOVE, src, os.path.abspath(dst), flags, None, None))

    if not aborted and result != 0:
        # Note: raising a WindowsError with correct error code is quite
        # difficult due to SHFileOperation historical idiosyncrasies.
        # Therefore we simply pass a message.
        raise Exception("Cannot copy. Windows error - SHFileOperation failed: 0x%08x" % result)

    return not aborted


def rename(src, dst: str, auto_rename: bool = False) -> bool:
    """
    Rename files and directories using Windows shell.

    :param src: Path or a list of paths to copy. Filename portion of a path
                (but not directory portion) can contain wildcards ``*`` and
                ``?``.
    :param dst: destination directory.
    :param auto_rename: if ''False'' then overwrite else auto rename
    :returns: ``True`` if the operation completed successfully,
              ``False`` if it was aborted by user (completed partially).
    :raises: ``WindowsError`` if anything went wrong. Typically, when source
             file was not found.

    .. seealso:
        `SHFileperation on MSDN <http://msdn.microsoft.com/en-us/library/windows/desktop/bb762164(v=vs.85).aspx>`
    """
    if isinstance(src, str):  # in Py3 replace basestring with str
        src = os.path.abspath(src)
    else:  # iterable
        src = "\0".join(os.path.abspath(path) for path in src)

    flags = shellcon.FOF_NOCONFIRMMKDIR | shellcon.FOF_SILENT
    if auto_rename:
        flags = flags | shellcon.FOF_RENAMEONCOLLISION

    result, aborted = shell.SHFileOperation((0, shellcon.FO_RENAME, src, os.path.abspath(dst), flags, None, None))

    if not aborted and result != 0:
        # Note: raising a WindowsError with correct error code is quite
        # difficult due to SHFileOperation historical idiosyncrasies.
        # Therefore we simply pass a message.
        raise Exception("Cannot rename. Windows error - SHFileOperation failed: 0x%08x" % result)

    return not aborted


def delete(src, hard_delete: bool) -> bool:
    """
    Move files and directories using Windows shell.

    :param src: Path or a list of paths to copy. Filename portion of a path
                (but not directory portion) can contain wildcards ``*`` and
                ``?``.
    :param hard_delete: if true then it bypasses recycle bin
    :returns: ``True`` if the operation completed successfully,
              ``False`` if it was aborted by user (completed partially).
    :raises: ``WindowsError`` if anything went wrong. Typically, when source
             file was not found.

    .. seealso:
        `SHFileperation on MSDN <http://msdn.microsoft.com/en-us/library/windows/desktop/bb762164(v=vs.85).aspx>`
    """
    if isinstance(src, str):  # in Py3 replace basestring with str
        src = os.path.abspath(src)
    else:  # iterable
        src = "\0".join(os.path.abspath(path) for path in src)

    flags = 0  # shellcon.FOF_SILENT

    logger.debug(f"deleting {src} {hard_delete}")

    if not hard_delete:
        flags |= shellcon.FOF_ALLOWUNDO

    result, aborted = shell.SHFileOperation((0, shellcon.FO_DELETE, src, None, flags, None, None))  # Flags

    if not aborted and result != 0:
        # Note: raising a WindowsError with correct error code is quite
        # difficult due to SHFileOperation historical idiosyncrasies.
        # Therefore we simply pass a message.
        raise Exception("Cannot delete. Windows error - SHFileOperation failed: 0x%08x" % result)
        # raise WindowsError('SHFileOperation failed: 0x%08x' % result)

    return not aborted


def new_file(file_name: str) -> Optional[str]:
    try:
        handle = win32file.CreateFile(
            file_name,
            win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
            None,
            win32con.CREATE_NEW,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        handle.Close()
        return None
    except Exception as e:
        return str(e)


def get_new_name(full_name: str) -> str:

    path = Path(full_name)
    if not path.exists():
        return full_name
    else:
        if fnmatch.fnmatch(path.stem, "*(*)"):
            start = path.stem.rfind("(")
            stop = path.stem.rfind(")")
            # print(path.stem[start:stop+1])
            try:
                num = int(path.stem[start + 1 : stop])
            except:
                return str(path.parent.joinpath(path.stem)) + "(1)" + path.suffix
            else:
                return str(path.parent.joinpath(path.stem[:start])) + str(num + 1) + ")" + path.suffix
        else:
            _name = str(path.parent.joinpath(path.stem)) + "(1)" + path.suffix
            if Path(_name).exists():
                get_new_name(_name)
            else:
                return str(path.parent.joinpath(path.stem)) + "(1)" + path.suffix


def copy_file(src: str, tgt: str, auto_rename) -> bool:
    if auto_rename:
        tgt = get_new_name(tgt)
    try:
        win32file.CopyFile(src, tgt, 0)
        return True
    except Exception as e:
        raise e


def move_file(src: str, tgt: str, _rename: bool) -> None:
    flags = win32file.MOVEFILE_COPY_ALLOWED
    if _rename:
        tgt = get_new_name(tgt)
    else:
        flags = flags | win32file.MOVEFILE_REPLACE_EXISTING
    try:
        win32file.MoveFileEx(src, tgt, flags)
    except Exception as e:
        raise e


class Command(Enum):
    CUT = "cut"
    COPY = "copy"
    PASTE = "paste"
    DELETE = "delete"
    PROPS = "properties"


def shell_command(path, command: Command):
    desktop_folder = shell.SHGetDesktopFolder()
    hwnd = win32gui.GetForegroundWindow()
    item = Path(path)
    path = item.parent
    parent_pidl = shell.SHILCreateFromPath(str(path), 0)[0]
    parent_folder = desktop_folder.BindToObject(parent_pidl, None, shell.IID_IShellFolder)
    pidl = parent_folder.ParseDisplayName(hwnd, None, item.name)[1]
    context_menu = parent_folder.GetUIObjectOf(hwnd, [pidl], shell.IID_IContextMenu, 0)[1]
    menu = win32gui.CreatePopupMenu()
    context_menu.QueryContextMenu(
        menu, 0, 1, 0x7FFF, shellcon.CMF_EXPLORE | shellcon.CMF_ITEMMENU | shellcon.CMF_EXTENDEDVERBS
    )
    ci = (
        0,  # Mask
        hwnd,  # hwnd
        command.value,  # Verb
        "",  # Parameters
        "",  # Directory
        win32con.SW_SHOWNORMAL,  # Show
        0,  # HotKey
        None,  # Icon
    )
    context_menu.InvokeCommand(ci)


def shell_execute(path, command: Command):
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = _SEE_MASK_NOCLOSEPROCESS | _SEE_MASK_INVOKEIDLIST
    sei.lpVerb = command.value  # "properties"
    item = path if path.endswith(os.sep) else "".join([path, os.sep])
    logger.debug(f"item cut to clipboard {item}")
    sei.lpFile = item
    sei.nShow = 1
    ShellExecuteEx(ctypes.byref(sei))


def paste(path: str):
    shell_execute(path=path, command=Command.PASTE)


def cut(path: str):
    shell_execute(path=path, command=Command.CUT)


# def delete(path: str):
#     shell_execute(path=path, command=Command.DELETE)


def properties(path: str):
    shell_execute(path=path, command=Command.PROPS)


def delete_file(path):
    shell_command(path=path, command=Command.DELETE)


def start_file(file_name: str):
    shell.ShellExecuteEx(
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, nShow=win32con.SW_NORMAL, lpVerb="Open", lpFile=file_name
    )


def open_folder(dir_name: str):
    shell.ShellExecuteEx(
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS, nShow=win32con.SW_NORMAL, lpVerb="Open", lpFile=dir_name
    )


def new_folder(folder_name):
    try:
        win32file.CreateDirectory(folder_name, None)
    except Exception as e:
        raise e


def get_file_name(path: str) -> str:
    dir, name = os.path.split(path)
    if not name:
        raise ValueError("Invalid file name")
    else:
        return name


class Shortcut:
    def __init__(self):
        self._base = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
        )

    def load(self, filename):
        self._base.QueryInterface(pythoncom.IID_IPersistFile).Load(filename)
        return self._base.GetPath(shell.SLGP_RAWPATH)[0]

    def save(self, filename):
        self._base.QueryInterface(pythoncom.IID_IPersistFile).Save(filename, 0)

    def __getattr__(self, name):
        if name != "_base":
            return getattr(self._base, name)

    @staticmethod
    def new_shortcut(path, lnk_name, target, args=None, desc=None, start_in=None):
        winshell.CreateShortcut(
            Path=str(os.path.join(path, lnk_name) if lnk_name else path),
            Target=str(target),
            Arguments=str(args),
            Description="Shortcut to " + str(target),
            StartIn=str(start_in),
        )


def get_drives():

    drive_types = {
        0: "Unknown",
        1: "No Root Directory",
        2: "Removable Disk",
        3: "Local Disk",
        4: "Network Drive",
        5: "Compact Disc",
        6: "RAM Disk",
    }

    drives = (drive for drive in win32api.GetLogicalDriveStrings().split("\000") if drive)
    drive_dict = {}
    for drive in drives:
        try:
            info = win32api.GetVolumeInformation(drive)
        except:
            info = [""]
        # print(drive, "=>", drive_types[win32file.GetDriveType(drive)])
        drive_dict[drive] = [drive, info[0], drive_types[win32file.GetDriveType(drive)], drive]
    desk_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
    home_path = Path.home()
    drive_dict[desk_path] = ["Desktop", "", desk_path, desk_path]
    drive_dict[home_path] = ["Home", "", home_path, home_path]
    return drive_dict


def get_context_menu(path, file_names):
    desktop_folder = shell.SHGetDesktopFolder()
    hwnd = win32gui.GetForegroundWindow()
    parent_pidl = shell.SHILCreateFromPath(path, 0)[0]
    parent_folder = desktop_folder.BindToObject(parent_pidl, None, shell.IID_IShellFolder)
    if file_names:
        pidls = []
        for item in file_names:
            pidl = parent_folder.ParseDisplayName(hwnd, None, item)[1]
            pidls.append(pidl)
        context_menu = parent_folder.GetUIObjectOf(hwnd, pidls, shell.IID_IContextMenu, 0)[1]
        # print(parent_folder.GetDisplayNameOf(pidls[0], shellcon.SHGDN_FORPARSING | shellcon.SHGDN_FORADDRESSBAR))
    else:
        item = Path(path)
        path = item.parent
        parent_pidl = shell.SHILCreateFromPath(str(path), 0)[0]
        parent_folder = desktop_folder.BindToObject(parent_pidl, None, shell.IID_IShellFolder)
        pidl = parent_folder.ParseDisplayName(hwnd, None, item.name)[1]
        context_menu = parent_folder.GetUIObjectOf(hwnd, [pidl], shell.IID_IContextMenu, 0)[1]
        # context_menu = parent_folder.CreateViewObject(hwnd, shell.IID_IContextMenu)
    cm_plus = None
    if context_menu:
        try:
            cm_plus = context_menu.QueryInterface(shell.IID_IContextMenu3, None)
        except Exception as e:
            pass
            try:
                cm_plus = context_menu.QueryInterface(shell.IID_IContextMenu2, None)
            except Exception as e:
                pass
    else:
        raise Exception("Unable to get context menu interface")
    if cm_plus:
        context_menu.Release()
        context_menu = cm_plus
    menu = win32gui.CreatePopupMenu()
    context_menu.QueryContextMenu(
        menu, 0, 1, 0x7FFF, shellcon.CMF_EXPLORE | shellcon.CMF_ITEMMENU | shellcon.CMF_EXTENDEDVERBS
    )
    x, y = win32gui.GetCursorPos()
    flags = win32gui.TPM_LEFTALIGN | win32gui.TPM_RETURNCMD
    cmd = win32gui.TrackPopupMenu(menu, flags, x, y, 0, hwnd, None)
    if cmd:
        ci = (
            0,  # Mask
            hwnd,  # hwnd
            cmd - 1,  # Verb
            "",  # Parameters
            "",  # Directory
            win32con.SW_SHOWNORMAL,  # Show
            0,  # HotKey
            None,  # Icon
        )
        context_menu.InvokeCommand(ci)


class ShellThread(threading.Thread):
    """ShellThread should always e used in preference to threading.Thread.
    The interface provided by ShellThread is identical to that of threading.Thread,
    however, if an exception occurs in the thread the error will be logged
    to the user rather than printed to stderr.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run

    def _wrap_run(self):
        try:
            self._real_run()
        except Exception as e:
            logger.error(str(e))


def join(items: List[str]) -> str:
    return "/".join(items)


def get_app_data_path() -> str:
    return os.getenv("APPDATA")
