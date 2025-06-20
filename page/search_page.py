import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QButtonGroup, QFileDialog, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from qfluentwidgets import (PrimaryPushButton, InfoBar, InfoBarPosition, LineEdit, CheckBox, PushButton, ToolButton, 
                            RadioButton, InfoBarIcon, TableWidget, ToolTipPosition, ToolTipFilter, IndeterminateProgressBar)
from qfluentwidgets import FluentIcon as FIT
from pyqt5_concurrent.TaskExecutor import TaskExecutor
class SearchPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("search")  # 设置 objectName 以便 Pivot 能识别

        self.json_path = ""  # 保存选择的json文件路径
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(20, 10, 20, 10)

        # --- 查询类型选择 ---
        type_layout = QHBoxLayout()
        type_label = QLabel("查询类型:")
        type_label.setStyleSheet("font: 12pt 'Segoe UI', 'Microsoft YaHei';")
        type_layout.addWidget(type_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.radio_buttons = []

        self.tableheader = ["城市", "行政区", "街道", "道路"]
        for text in self.tableheader:
            rb = RadioButton(text, self)
            rb.setStyleSheet("font: 12pt 'Segoe UI', 'Microsoft YaHei';")
            type_layout.addWidget(rb)
            self.button_group.addButton(rb)
            self.radio_buttons.append(rb)
        self.radio_buttons[0].setChecked(True)  # 默认选中第一个

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
        self.input_edit = LineEdit(self)
        self.input_edit.setPlaceholderText("请输入查询内容")
        self.input_edit.setStyleSheet("font:12pt;")
        second_layout.addWidget(self.input_edit)
        self.layout.addLayout(second_layout)


        # --- 查询按钮 ---
        self.query_btn = PrimaryPushButton("查询")
        self.query_btn.clicked.connect(self.query_action)
        self.layout.addWidget(self.query_btn)

        # 初始化表格
        self.tableView = TableWidget(self)
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        self.tableView.setWordWrap(False)
        self.tableView.setColumnCount(4)
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
        else:
            self.json_path = ""
        self.file_btn.setToolTip(f"{self.json_path}") # 更新ToolButton的提示文本
        createInfoInfoBar(self.json_path)

    def query_action(self):
        # 获取选中的radio按钮文本
        query_type = ""
        for rb in self.radio_buttons:
            if rb.isChecked():
                query_type = rb.text()
                break
        query_text = self.input_edit.text()

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
        
        # 显示进度条
        self.inProgress.start()
        future = TaskExecutor.run(self.fors, self.json_path, query_type, query_text)  # 使用 TaskExecutor 来运行耗时任务
        future.finished.connect(lambda e: self.updatetable(e.getExtra('result'), query_text))  # 更新表格数据

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
            for j in range(4):
                table_item = QTableWidgetItem(row[j])
                table_item.setTextAlignment(Qt.AlignCenter)
                self.tableView.setItem(i, j, table_item)
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)  # 最后一列拉伸填满剩余空间
        self.tableView.setHorizontalHeaderLabels(self.tableheader)

        self.inProgress.stop()

    def fors(self, json_path, query_type, query_text):
        # 模拟一个耗时任务
        import time
        time.sleep(2)
        # 这里可以添加实际的查询逻辑
        # 返回查询结果
        songInfos = [
        ]
        return songInfos
    
    def createInfoBar(self, num, query_text):
        if num > 0:
            InfoBar.success(
                title='查询完成',
                content=f"🎉 共有 {num} 条与“{query_text}”有关的道路信息！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=2000,
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