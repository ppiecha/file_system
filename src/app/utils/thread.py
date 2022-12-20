import logging
from threading import Thread
from typing import Callable, Sequence, List, NamedTuple

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

from src.app.utils.logger import get_console_logger, get_file_handler

logger = get_console_logger(name=__name__, log_level=logging.ERROR)
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
            # QMessageBox.critical(self.parent, APP_NAME, "\n".join(["Exception in background thread", str(e)]))
            logger.error(str(e))


class ShellWorker(QObject):
    exception = Signal(str)
    finished = Signal()

    def __init__(self, parent, target: Callable, args: Sequence):
        super().__init__()
        self.parent = parent
        self.target = target
        self.args = args

    def run(self):
        try:
            logger.debug(f"Executing {self.target} with args {self.args}")
            self.target(*self.args)
        except Exception as e:
            logger.error(str(e))
            self.exception.emit(str(e))
        finally:
            self.finished.emit()


class ThreadWithWorker(NamedTuple):
    thread: QThread
    worker: ShellWorker


def run_in_thread(parent, target: Callable, args: Sequence, threads: List[ThreadWithWorker]) -> None:
    def on_finish(tww: ThreadWithWorker):
        def finalize():
            logger.debug(f"count {len(threads)}")
            logger.debug(f"finishing {id(tww)}")
            parent.remove_thread(thread_with_worker=tww)
            tww.thread.deleteLater()
            logger.debug("cleanup done")

        return finalize

    logger.debug(f"run_in_thread {type(parent)}")
    thread = QThread()
    worker = ShellWorker(parent=parent, target=target, args=args)
    thread_with_worker = ThreadWithWorker(thread=thread, worker=worker)
    threads.append(thread_with_worker)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(on_finish(tww=thread_with_worker))
    worker.exception.connect(lambda exc: QMessageBox.critical(parent, "Exception in background thread", exc))
    # Start the thread
    logger.debug(f"Starting thread {thread} with worker {worker}")
    thread.start()
