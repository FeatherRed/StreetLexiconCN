import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QFrame, QStackedWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QPalette
from qfluentwidgets import ComboBox, PrimaryPushButton, IndeterminateProgressBar, InfoBar, InfoBarPosition, TextBrowser
from pyqt5_concurrent.TaskExecutor import TaskExecutor
import time

from page.create import create_database  # 假设 create.py 在同一目录下

import platform

class CreatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("create")  # 设置 objectName 以便 Pivot 能识别
        # self._bg_color = QColor("#ffffff")  # 背景色

        with open("china_admin_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.provinces_data = data["name"]
        self.city_id = data["id"]
        self.is_amd = "AMD" in platform.processor()  # 检测是否为 AMD 处理器
        self.init_ui()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(20, 10, 20, 10)

        # --- 省份选择 ---
        province_layout = QHBoxLayout()
        province_label = QLabel("选择省份|直辖市:")
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
        self.city_combo.currentIndexChanged.connect(self.update_button)
        city_layout.addWidget(city_label)
        city_layout.addWidget(self.city_combo)
        self.layout.addLayout(city_layout)

        # --- 生成按钮 ---
        self.generate_btn = PrimaryPushButton("生成 北京市 地址路名数据")
        self.generate_btn.clicked.connect(self.generate_database)
        self.layout.addWidget(self.generate_btn)


        # 初始化城市
        self.update_cities(self.province_combo.currentText())
        self.province_combo.setMaxVisibleItems(8)
        self.city_combo.setMaxVisibleItems(8)

        self.layout.addSpacerItem(QSpacerItem(5, 5, 5, 5))

        # 生成数据导播
        self.textBrowser = TextBrowser(self)
        # self.textBrowser.setMarkdown("## 正在处理北京市 \n")
        # print(self.textBrowser.toMarkdown())
        self.emitter = GuiSignalEmitter() # 专门用来线程通信的
        self.emitter.log.connect(self.updateTextBrowser)

        self.save_emitter = savejsonEmitter() if self.is_amd else None  # 用于保存数据的信号发射器
        if self.save_emitter:
            self.save_emitter.log.connect(self.save_json)

        self.layout.addWidget(self.textBrowser)

        # --- 状态显示 ---
        self.layout.addSpacerItem(QSpacerItem(5, 5, 5, 5))

        # 设置进度条
        self.inProgress = IndeterminateProgressBar(self, start=False)
        self.layout.addWidget(self.inProgress)

        with open(f'resource/light/demo.qss', encoding = 'utf-8') as f:
            self.setStyleSheet(f.read())

    def update_cities(self, province):
        self.city_combo.clear()
        if province in self.provinces_data:
            self.city_combo.addItems(self.provinces_data[province])

    def update_button(self, city_id):
        # 得到城市
        city = self.city_combo.currentText()
        self.generate_btn.setText(f"生成 {city} 地址路名数据")    

    def generate_database(self):
        # 清除 广播
        self.textBrowser.clear()


        # 显示进度条
        self.inProgress.start()
        province = self.province_combo.currentText()
        city = self.city_combo.currentText()
        id = self.city_id[province][city]  # 获取城市的 ID

        # # 广播头
        self.textBrowser.setMarkdown(f"## 正在生成 {city} 地址路名数据\n")

        # 模拟生成过程
        future = TaskExecutor.run(lambda : self.fors(id, city, province,self.emitter, self.save_emitter))
        if not self.is_amd:
            # CPU
            future.finished.connect(lambda: self.save_json(future.getExtra('result'), province, city))
        # future.finished.connect(lambda e: self.createInfoBar(city, str(e)))
        # future.failed.connect(lambda e: self.createErrorInfoBar(city, str(e)))


    def fors(self, id, city, province, emitter, save_emitter = None):
        result = create_database(id, city, province, emitter)

        if save_emitter is not None:
            save_emitter.log.emit(result, province, city)  # 发送保存数据的信号

        return result

    def save_json(self, result, province, city):
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
        if result == 0 or result is None:
            errorbar(city)
            self.inProgress.stop()
            return
        successbar(city)
        if not os.path.exists("output"):
            os.makedirs("output")

        # 保存
        if os.path.exists(f"output/{province}.json"):
            with open(f"output/{province}.json", 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            if city not in existing_data:
                existing_data[city] = {}
        else:
            existing_data = {}
            existing_data[city] = {}
        # 合并数据
        existing_data[city].update(result)
        with open(f"output/{province}.json", 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        self.inProgress.stop()

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
    def updateTextBrowser(self, msg):
        # 得到原有的文本
        text = self.textBrowser.toMarkdown()
        self.textBrowser.setMarkdown(text + f" ✅ {msg}\n")
        # 让 TextBrowser 滚动到最新内容
        self.textBrowser.verticalScrollBar().setValue(self.textBrowser.verticalScrollBar().maximum())

class GuiSignalEmitter(QObject):
    log = pyqtSignal(str)

class savejsonEmitter(QObject):
    log = pyqtSignal(object, str, str)