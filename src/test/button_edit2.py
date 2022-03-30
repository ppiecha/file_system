import sys

from PySide2.QtWidgets import QLineEdit, QStyle, QApplication


class LineEditFileDialogWidget(QLineEdit):
    def __init__(self, parent=None):
        super(LineEditFileDialogWidget, self).__init__(parent)
        # self.setReadOnly(True)

        icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        self.action = self.addAction(icon, QLineEdit.TrailingPosition)
        self.action.triggered.connect(self.log)

    def log(self):
        print("hello")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = LineEditFileDialogWidget()
    main.show()
    sys.exit(app.exec_())