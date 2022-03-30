from PySide2 import QtGui
from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import QToolButton, QApplication, QLineEdit, QStyle


class ButtonLineEdit(QLineEdit):
    # buttonClicked = QtCore.pyqtSignal(bool)

    def __init__(self, icon_file, parent=None, on_click_func=None):
        super(ButtonLineEdit, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setIcon(QIcon(icon_file))
        self.button.setStyleSheet('border: 0px; padding: 0px;')
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(on_click_func)

        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        buttonSize = self.button.sizeHint()

        self.setStyleSheet('QLineEdit {padding-right: %dpx; }' % (buttonSize.width() + frameWidth + 1))
        self.setMinimumSize(max(self.minimumSizeHint().width(), buttonSize.width() + frameWidth*2 + 2),
                            max(self.minimumSizeHint().height(), buttonSize.height() + frameWidth*2 + 2))

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - buttonSize.width(),
                         (self.rect().bottom() - buttonSize.height() + 1)/2)
        super(ButtonLineEdit, self).resizeEvent(event)


import sys

def buttonClicked():
    print('You clicked the button!')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = ButtonLineEdit(icon_file=r'C:\Users\piotr\_piotr_\__GIT__\Python\file_system\src\app\file_system.ico'
                          , on_click_func=buttonClicked)
    # main.buttonClicked.connect(buttonClicked)
    main.show()

    sys.exit(app.exec_())