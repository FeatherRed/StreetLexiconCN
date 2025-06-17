# coding:utf-8
import sys
from PyQt5.QtCore import Qt, QEvent, QSize, QEventLoop, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStackedWidget, QHBoxLayout, QLabel, QWidget, QVBoxLayout

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
                            isDarkTheme, setTheme, Theme, setThemeColor, NavigationToolButton, NavigationPanel)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, StandardTitleBar
from qfluentwidgets import Pivot, setTheme, Theme, SplashScreen

from page import CreatePage


class Widget(QWidget):

    def __init__(self, text: str, parent = None):
        super().__init__(parent = parent)
        self.label = QLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        self.setObjectName(text.replace(' ', '-'))


class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))
        self.resize(500, 500)
        self.setWindowIcon(QIcon('resource/logo.png'))
        self.setWindowTitle('地图地址路名库生成器')

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        self.show()

        # use dark theme mode
        # setTheme(Theme.DARK)

        # change the theme color
        # setThemeColor('#0078d4')

        self.vBoxLayout = QVBoxLayout(self)
        # self.navigationInterface = NavigationBar(self)
        self.stackWidget = QStackedWidget(self)

        self.pivot = Pivot(self)

        self.CreateInterface = CreatePage()
        self.FindInterface = Widget('Find', self)

        # create sub interface
        self.addSubInterface(self.CreateInterface, 'create', '创建')
        self.addSubInterface(self.FindInterface, 'find', '查询')

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        # self.initNavigation()

        self.initWindow()
        self.splashScreen.finish()

    def initLayout(self):
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        # self.vBoxLayout.addWidget(self.navigationInterface)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackWidget)
        self.vBoxLayout.setStretchFactor(self.stackWidget, 1)

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        # widget.setAlignment(Qt.AlignCenter)
        self.stackWidget.addWidget(widget)
        self.pivot.addItem(routeKey = objectName, text = text)

    def initWindow(self):
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()
        self.pivot.setCurrentItem(self.CreateInterface.objectName())
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackWidget.setCurrentWidget(self.findChild(QWidget, k)))

        # 给启动页面时间
        loop = QEventLoop(self)
        QTimer.singleShot(3000, loop.quit)
        loop.exec()

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{color}/demo.qss', encoding = 'utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
