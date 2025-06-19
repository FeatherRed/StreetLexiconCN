import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QFrame, QStackedWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QPalette
from qfluentwidgets import ComboBox, PrimaryPushButton, IndeterminateProgressBar, InfoBar, InfoBarPosition
from pyqt5_concurrent.TaskExecutor import TaskExecutor
import time
class CreatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("create")  # 设置 objectName 以便 Pivot 能识别
        # self._bg_color = QColor("#ffffff")  # 背景色

        with open("china_admin_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.provinces_data = data["name"]
        self.city_id = data["id"]

        self.init_ui()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(40, 10, 40, 10)

        # --- 省份选择 ---
        province_layout = QHBoxLayout()
        province_label = QLabel("选择省份:")
        province_label.setStyleSheet("font:12pt;")
        self.province_combo = ComboBox()
        self.province_combo.setStyleSheet("font:12pt;")
        self.province_combo.addItems(list(self.provinces_data.keys()))
        self.province_combo.currentTextChanged.connect(self.update_cities)
        province_layout.addWidget(province_label)
        province_layout.addWidget(self.province_combo)
        self.layout.addLayout(province_layout)

        # --- 城市选择 ---
        city_layout = QHBoxLayout()
        city_label = QLabel("选择城市:")
        city_label.setStyleSheet("font:12pt;")
        self.city_combo = ComboBox()
        self.city_combo.setStyleSheet("font:12pt;")
        city_layout.addWidget(city_label)
        city_layout.addWidget(self.city_combo)
        self.layout.addLayout(city_layout)

        # --- 生成按钮 ---
        self.generate_btn = PrimaryPushButton("生成地址路名数据库")
        # self.generate_btn.setStyleSheet("""
        #     font:12pt;
        #     background:#1890ff;
        #     color:white;
        #     border-radius:5px;
        #     height:36px;
        # """)
        self.generate_btn.clicked.connect(self.generate_database)
        self.layout.addWidget(self.generate_btn)

        # --- 状态显示 ---
        self.layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 初始化城市
        self.update_cities(self.province_combo.currentText())
        self.province_combo.setMaxVisibleItems(8)
        self.city_combo.setMaxVisibleItems(8)

        # 设置进度条
        self.inProgress = IndeterminateProgressBar(self, start=False)
        self.layout.addWidget(self.inProgress)

        with open(f'resource/light/demo.qss', encoding = 'utf-8') as f:
            self.setStyleSheet(f.read())

    def update_cities(self, province):
        self.city_combo.clear()
        if province in self.provinces_data:
            self.city_combo.addItems(self.provinces_data[province])

    def generate_database(self):

        # 显示进度条
        self.inProgress.start()
        
        province = self.province_combo.currentText()
        city = self.city_combo.currentText()

        # 模拟生成过程
        future = TaskExecutor.run(self.fors)  # 使用 TaskExecutor 来运行耗时任务
        future.finished.connect(lambda e: self.createInfoBar(city, str(e)))
        # future.failed.connect(lambda e: self.createErrorInfoBar(city, str(e)))


    def fors(self,):
        time.sleep(2)
        # 模拟一个异常
        import numpy as np
        a = np.random.rand()
        if a < 0.5:
            return "正常"
        else:
            return "失败"
        

    def createInfoBar(self, city, error = None):
        def successbar(city):
            InfoBar.success(
                title = '生成完成',
                content = f"🎉 {city} 的路名数据已成功建立！",
                orient = Qt.Horizontal,
                isClosable = True,
                position = InfoBarPosition.BOTTOM,
                duration = 3000,
                parent = self,
            )
        def errorbar(city):
            InfoBar.error(
                title = '生成失败',
                content = f"生成 {city} 的路名数据时网络出现问题！",
                orient = Qt.Horizontal,
                isClosable = True,
                position = InfoBarPosition.BOTTOM,
                duration = 3000,  # won't disappear automatically
                parent = self
            )
        if error == "Future(正常)":
            successbar(city)
        elif error == "Future(失败)":
            errorbar(city)
        self.inProgress.stop()