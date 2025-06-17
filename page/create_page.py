import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QFrame, QStackedWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QTimer
from PyQt5.QtGui import QColor, QPalette
from qfluentwidgets import ComboBox, PrimaryPushButton

class CreatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("create")  # 设置 objectName 以便 Pivot 能识别
        self._bg_color = QColor("#ffffff")  # 背景色

        with open("china_admin_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.provinces_data = data["name"]
        self.city_id = data["id"]

        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 10, 40, 10)

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
        layout.addLayout(province_layout)

        # --- 城市选择 ---
        city_layout = QHBoxLayout()
        city_label = QLabel("选择城市:")
        city_label.setStyleSheet("font:12pt;")
        self.city_combo = ComboBox()
        self.city_combo.setStyleSheet("font:12pt;")
        city_layout.addWidget(city_label)
        city_layout.addWidget(self.city_combo)
        layout.addLayout(city_layout)

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
        layout.addWidget(self.generate_btn)

        # --- 状态显示 ---
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font:10pt; color:#888;")
        layout.addWidget(self.status_label)

        # 初始化城市
        self.update_cities(self.province_combo.currentText())
        self.province_combo.setMaxVisibleItems(8)
        self.city_combo.setMaxVisibleItems(8)

    def update_cities(self, province):
        self.city_combo.clear()
        if province in self.provinces_data:
            self.city_combo.addItems(self.provinces_data[province])

    def generate_database(self):
        province = self.province_combo.currentText()
        city = self.city_combo.currentText()

        if not province or not city:
            self.status_label.setText("请选择省份和城市。")
            return

        # 简化生成逻辑，真实项目可替换为生成数据到文件
        self.status_label.setText(f"成功生成：{province} - {city} 的地址路名库。")

        # 过几秒清空
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

