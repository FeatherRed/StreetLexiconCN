import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QButtonGroup, QFileDialog, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from qfluentwidgets import (PrimaryPushButton, InfoBar, InfoBarPosition, LineEdit, CheckBox, PushButton, ToolButton, SearchLineEdit,
                            RadioButton, InfoBarIcon, TableWidget, ToolTipPosition, ToolTipFilter, IndeterminateProgressBar, ComboBox)
from qfluentwidgets import FluentIcon as FIT
from pyqt5_concurrent.TaskExecutor import TaskExecutor
from query import query_city, query_road, query_street, query_district

import platform

import json
class SearchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("search")  # 设置 objectName 以便 Pivot 能识别

        self.json_path = ""  # 保存选择的json文件路径
        self.is_amd = "AMD" in platform.processor()  # 检测是否为 AMD 处理器
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(20, 10, 20, 10)

        # --- 查询类型选择 ---
        type_layout = QHBoxLayout()
        # type_label = QLabel("查询类型:")
        # type_label.setStyleSheet("font: 12pt 'Segoe UI', 'Microsoft YaHei';")
        # type_layout.addWidget(type_label)


        # 城市下拉框：靠左
        self.city_combo = ComboBox(self)
        self.city_combo.setPlaceholderText("选择查询城市")
        self.city_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.city_combo.setMaxVisibleItems(8)
        type_layout.addWidget(self.city_combo)

        # 中间 spacer：弹性撑开空白
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        type_layout.addItem(spacer)

        # 单选按钮组：靠右排列
        self.tableheader = ["行政", "街道", "道路"]
        self.check_boxes = []
        self.button_group = QButtonGroup(self)  # 创建按钮组以管理单选按钮
        self.button_group.setExclusive(True)  # 设置为单选模式

        for text in self.tableheader:  # 跳过“城市”
            cb = CheckBox(text, self)
            cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            type_layout.addWidget(cb)
            self.button_group.addButton(cb)  # 将复选框添加到按钮组
            self.check_boxes.append(cb)
            # cb.clicked.connect(lambda checked, b=cb: self.on_checkbox_clicked(b))  # 连接点击事件



        self.check_boxes[-1].setChecked(True)  # 默认选中

        self.layout.addLayout(type_layout)

        # --- 选择JSON文件按钮（放在查询框左边，无QLabel） ---
        self.json_path = ""
        second_layout = QHBoxLayout()
        self.file_btn = ToolButton(FIT.FOLDER, self)
        self.file_btn.setToolTip(f"当前未选择文件")
        self.file_btn.installEventFilter(ToolTipFilter(self.file_btn, 0, ToolTipPosition.RIGHT))  # 设置鼠标悬停提示
        
        self.file_btn.clicked.connect(self.select_json_file)
        second_layout.addWidget(self.file_btn)

        # --- 输入框 ---
        self.input_edit = SearchLineEdit(self)
        self.input_edit.setPlaceholderText("请输入查询内容")
        self.input_edit.setStyleSheet("font:12pt;")
        self.input_edit.searchButton.clicked.connect(self.query_action)  # 输入框回车或点击搜索按钮时触发查询
        second_layout.addWidget(self.input_edit)
        self.layout.addLayout(second_layout)

        self.emitter = SearchEmitter() if self.is_amd else None  # 用于线程通信的信号发射器
        if self.emitter:
            # 连接信号到槽函数
            self.emitter.log.connect(self.updatetable)
        # --- 查询按钮 ---
        # self.query_btn = PrimaryPushButton("查询")
        # self.query_btn.clicked.connect(self.query_action)
        # self.layout.addWidget(self.query_btn)

        # 初始化表格
        self.tableView = TableWidget(self)
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        self.tableView.setWordWrap(False)
        self.tableView.setColumnCount(3)
        self.tableView.verticalHeader().hide()
        self.tableView.setHorizontalHeaderLabels(self.tableheader)
        # 不可编辑
        self.tableView.setEditTriggers(TableWidget.NoEditTriggers)
        # self.tableView.resizeColumnsToContents()  # 根据内容调整列宽

        # self.tableView.horizontalHeader().setSectionResizeMode(0, 1)  # 设置第一列宽度自适应

        # self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.tableView)
        # 设置进度条
        self.inProgress = IndeterminateProgressBar(self, start=False)
        self.layout.addWidget(self.inProgress)

    def select_json_file(self):
        def createInfoInfoBar(file_path):
            content = "已选择文件: " + file_path if file_path else "未选择文件"
            w = InfoBar(
                icon=InfoBarIcon.INFORMATION,
                title='文件选择',
                content=content,
                orient=Qt.Vertical,    # vertical layout
                isClosable=True,
                position=InfoBarPosition.BOTTOM_LEFT,
                duration=2000,
                parent=self
            )
            w.show()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择JSON文件", "", "JSON Files (*.json)")
        if file_path:
            self.json_path = file_path

            with open(self.json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not data:    
                        raise ValueError("文件内容为空")
                    # 更新 ComboBox的选项
                    self.data = data
                    # 拿文件名字
                    self.province = self.json_path.split('/')[-1].split('.')[0]  # 获取文件名作为省份名称

                    self.city_combo.clear()
                    city_list = list(data.keys())
                    self.city_combo.addItems(city_list)
                    self.city_combo.setCurrentIndex(0)  # 默认选中第一个城市
                except ValueError as e:
                    InfoBar.error(
                        title='错误',
                        content=f'选择的文件无效: {e}',
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.BOTTOM,
                        duration=2000,
                        parent=self
                    )
                    self.json_path = ""
                    return
        self.file_btn.setToolTip(f"{self.json_path}") # 更新ToolButton的提示文本
        createInfoInfoBar(self.json_path)

    def on_checkbox_clicked(self, clicked_box):
        if clicked_box.isChecked():
            # 取消其他所有 checkbox 的选中状态
            for box in self.check_boxes:
                if box is not clicked_box:
                    box.setChecked(False)      
        else:
            # 如果点击的是自己且已选中，则取消自己，不做别的处理
            pass
    

    def query_action(self):
        # 获取选中的checkbox文本
        flag = -1
        for i, cb in enumerate(self.check_boxes):
            if cb.isChecked():
                flag = i
                break
        query_text = self.input_edit.text().strip()  # 获取输入框中的文本并去除首尾空格
        # 如果 json_info 为空，提示用户选择文件
        if not self.json_path:
            InfoBar.warning(
                title='警告',
                content='当前未选择文件，请先选择一个JSON文件！',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self
            )
            return
        # 拿combox
        city_name = self.city_combo.currentText()
        province_name = self.province  # 使用之前保存的省份名称
        # 显示进度条
        self.inProgress.start()
        future = TaskExecutor.run(self.search, flag, query_text, self.data, city_name, province_name, self.emitter)  # 使用 TaskExecutor 来运行耗时任务
        if not self.is_amd:
            # 如果是 CPU 处理器，直接获取结果
            if query_text == "":
                query_text = city_name
            future.finished.connect(lambda: self.updatetable(future.getExtra('result'), query_text))
        # 修改一下query_text   
        # future.finished.connect(lambda e: self.updatetable(e.getExtra('result'), query_text))  # 更新表格数据

    def updatetable(self, data, query_text):
        """
        更新表格数据
        :param data: 二维列表，包含要显示的数据
        """
        num = len(data)

        self.tableView.clear()
        self.tableView.setRowCount(0)

        self.createInfoBar(num, query_text)

        self.tableView.setRowCount(num)
        for i, row in enumerate(data):
            for j in range(3):
                
                table_item = QTableWidgetItem(row[j + 1] if row[j + 1] is not None else "\\")
                table_item.setTextAlignment(Qt.AlignCenter)
                self.tableView.setItem(i, j, table_item)
        self.tableView.resizeColumnsToContents()
        # self.tableView.horizontalHeader().setStretchLastSection(True)  # 最后一列拉伸填满剩余空间
        self.tableView.setHorizontalHeaderLabels(self.tableheader)

        self.inProgress.stop()

    def search(self, flag, text, data, city, province, emitter = None):
        # 模拟一个耗时任务

        if flag == -1:
            a =  query_city(city, province, data[city])
        elif flag == 0:
            a = query_district(text, city, province, data[city])
        elif flag == 1:
            a = query_street(text, city, province, data[city])
        elif flag == 2:
            a = query_road(text, city, province, data[city])
        if text == "":
            text = city
        if emitter:
            emitter.log.emit(a, text)
        return a

    def createInfoBar(self, num, query_text):
        if num > 0:
            InfoBar.success(
                title='查询完成',
                content=f"🎉 共有 {num} 条与“{query_text}”有关的道路信息！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            InfoBar.success(
                title='查询完成',
                content=f"未查到关于“{query_text}”的道路信息！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
                parent=self,
            )

class SearchEmitter(QObject):
    log = pyqtSignal(object, str)