import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

import emu_gui

# TODO: implement a simple gui for the emulator

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    ui = emu_gui.Ui_MainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
