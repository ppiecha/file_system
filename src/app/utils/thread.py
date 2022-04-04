from threading import Thread
from typing import Callable, Sequence, List

from PySide2.QtWidgets import QMessageBox

from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger, get_file_handler

logger = get_console_logger(name=__name__)
logger.addHandler(get_file_handler())


class ShellThread(Thread):
    """ShellThread should always e used in preference to threading.Thread.
    The interface provided by ShellThread is identical to that of threading.Thread,
    however, if an exception occurs in the thread the error will be logged
    to the user rather than printed to stderr.
    """

    def __init__(self, parent, target: Callable, args: Sequence):
        super().__init__(target=target, args=args)
        self.parent = parent
        self._real_run = self.run
        self.run = self._wrap_run

    def _wrap_run(self):
        try:
            self._real_run()
        except Exception as e:
            QMessageBox.critical(self.parent, APP_NAME, "\n".join(["Exception in background thread", str(e)]))
            logger.error(str(e))


def run_in_thread(parent, target: Callable, args: Sequence, lst: List[ShellThread] = None) -> None:
    th = ShellThread(parent=parent, target=target, args=args)
    th.start()
    lst = lst or []
    lst.append(th)
