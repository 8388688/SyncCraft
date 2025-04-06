import sys
import threading
import pystray
from PIL import Image

from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QProgressBar, QMessageBox,
    QLineEdit, QStyleFactory
)


class PyQtStray:
    def __init__(self, syncRoot_fp):
        super().__init__(syncRoot_fp)
        # 添加菜单和图标
        self.create_systray_icon()
        # 绘制界面
        # self.gui_main()

    def create_systray_icon(self):
        """
        使用 Pystray 创建系统托盘图标
        """
        menu = (
            pystray.MenuItem("显示", self.show_window, default=True),
            pystray.MenuItem(self.KEY_BOARD["save_arc"][2], self.KEY_BOARD["save_arc"][3]),
            pystray.Menu.SEPARATOR,  # 在系统托盘菜单中添加分隔线
            pystray.MenuItem(self.KEY_BOARD["save_exit"][2], self.KEY_BOARD["save_exit"][3])
        )
        image = Image.open(self.ICON_FP)
        self.icon = pystray.Icon("icon", image, f"{self.TITLE} - {self.SYNC_ROOT_FP}", menu)
        # self.record_fx("icon.name=", self.icon.name)
        print("icon.name=", self.icon.name)
        threading.Thread(target=self.icon.run, daemon=True).start()

    # 关闭窗口时隐藏窗口，并将 Pystray 图标放到系统托盘中。
    def hide_window(self):
        self.withdraw()

    # 从系统托盘中恢复 Pystray 图标，并显示隐藏的窗口。
    def show_window(self):
        self.icon.visible = True
        self.deiconify()

    def quit_window(self, icon: pystray.Icon):
        """退出程序"""
        icon.stop()  # 停止 Pystray 的事件循环
        self.quit()  # 终止 Tkinter 的事件循环
        self.destroy()  # 销毁应用程序的主窗口和所有活动

    def gui_destroy(self, destroy2=None, slide=False, save=True):
        self.icon.visible = False
        self.icon.stop()
        super().gui_destroy(destroy2, slide, save)


class SyncCraftGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.resize(660, 462)
        self.setGeometry(100, 100, 660, 462)
        self.centralWidget()
        self.setFixedSize(self.width(), self.height())  # resizable = False

        # self.re

    def test(self):
        print("DF")

    def gui_main(self):
        pushbutton1 = QPushButton(self)
        pushbutton2 = QPushButton(self)
        pushbutton3 = QPushButton(self)
        pushbutton4 = QPushButton(self)
        pushbutton5 = QPushButton(self)
        pushbutton6 = QPushButton(self)
        lineedit1 = QLineEdit(self)
        lineedit2 = QLineEdit(self)

        lineedit1.move(120, 200)
        lineedit2.move(350, 200)
        lineedit1.resize(200, 30)
        lineedit2.resize(200, 30)
        pushbutton1.move(120, 250)
        pushbutton2.move(350, 250)
        pushbutton3.move(120, 300)
        pushbutton4.move(350, 300)
        pushbutton5.move(120, 350)
        pushbutton6.move(350, 350)
        pushbutton1.resize(200, 30)
        pushbutton2.resize(200, 30)
        pushbutton3.resize(200, 30)
        pushbutton4.resize(200, 30)
        pushbutton5.resize(200, 30)
        pushbutton6.resize(200, 30)

        pushbutton1.setText("运行")
        pushbutton1.clicked.connect(lambda: self.test())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print(QStyleFactory.keys())
    app.setStyle(QStyleFactory.create('Fusion'))
    w = SyncCraftGUI()
    w.gui_main()
    w.show()
    sys.exit(app.exec())
