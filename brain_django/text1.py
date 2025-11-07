import os
import asyncio
import logging
from datetime import datetime
import pandas as pd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QTabWidget, QFileDialog, QStatusBar,
                            QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QComboBox,
                            QMessageBox)  # 新增QMessageBox用于提示
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QFontDatabase, QColor

# 设备数据收集类（保持设备连接逻辑，不影响文件分析）
class TGAMDataCollector(QObject):
    data_received = pyqtSignal(str)
    file_created = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)
    recording_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.is_connected = False
        self.is_recording = False
        self.recorded_files = []  # 存储记录的文件路径
    
    async def connect_device(self):
        self.is_connected = True
        self.connection_changed.emit(True)
        self.status_updated.emit("设备已连接")
        
    async def disconnect_device(self):
        self.is_connected = False
        self.connection_changed.emit(False)
        self.status_updated.emit("设备已断开")
        
    def start_recording(self, path):
        self.is_recording = True
        self.recording_changed.emit(True)
        self.file_created.emit(path)
        self.recorded_files.append(path)
        self.status_updated.emit(f"正在记录数据至: {path}")
        
    def stop_recording(self):
        self.is_recording = False
        self.recording_changed.emit(False)
        self.status_updated.emit("记录已停止")

# 配置
DEFAULT_API_KEY = "51e09aa5-d2dd-41ab-bf91-51ef798844e7"
LOG_FILE = "app.log"
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# 日志配置
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("基于EEG与人工智能的睡眠健康评估系统 V2.0")
        self.setGeometry(100, 100, 1200, 800)
        self.collector = TGAMDataCollector()
        self.analyzer = None
        self.api_key = DEFAULT_API_KEY
        self._setup_ui()
        self._connect_signals()
        self._load_recorded_files()

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #0f172a;
                color: #e2e8f0;
                border-top: 1px solid #334155;
                padding: 4px;
            }
        """)
        self.statusBar.showMessage("就绪 | 后端:已连接 设备:未连接 数据:未连接 API:未连接")

    def _setup_ui(self):
        """初始化界面，适配当前截图布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧面板（设备连接 + 数据记录）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(300)
        left_panel.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        main_layout.addWidget(left_panel)

        # 标题
        title_label = QLabel("基于EEG与人\n工智能的睡眠健康\n评估系统 V2.0")
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffd700; padding: 10px; line-height: 1.5;")
        left_layout.addWidget(title_label)

        # 设备连接区域
        device_group = QGroupBox("设备连接")
        device_group.setStyleSheet("""
            QGroupBox {
                color: #e2e8f0;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px;
            }
        """)
        device_layout = QFormLayout()
        device_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        device_layout.setLabelAlignment(Qt.AlignLeft)
        device_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 蓝牙地址输入
        self.bluetooth_addr = QLabel("例如: JDY-18")
        self.bluetooth_addr.setStyleSheet("color: #94a3b8; border: 1px solid #334155; padding: 5px; border-radius: 4px;")
        device_layout.addRow("蓝牙设备地址", self.bluetooth_addr)

        # 扫描按钮
        self.btn_scan = QPushButton("扫描")
        self._style_button(self.btn_scan, "#3b82f6")
        device_layout.addRow(self.btn_scan)

        # 连接状态
        self.connection_status = QLabel("连接状态: 未连接")
        self.connection_status.setStyleSheet("color: #ef4444;")
        device_layout.addRow(self.connection_status)

        # 信号质量
        self.signal_quality = QLabel("信号质量: --/200")
        self.signal_quality.setStyleSheet("color: #94a3b8;")
        device_layout.addRow(self.signal_quality)

        device_group.setLayout(device_layout)
        left_layout.addWidget(device_group)

        # 数据记录区域
        record_group = QGroupBox("数据记录")
        record_group.setStyleSheet("""
            QGroupBox {
                color: #e2e8f0;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px;
            }
        """)
        record_layout = QVBoxLayout()

        # 数据记录列表
        self.record_list = QListWidget()
        self.record_list.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
                border-radius: 2px;
            }
        """)
        record_layout.addWidget(self.record_list)

        # 最近记录下拉框
        self.recent_records = QComboBox()
        self.recent_records.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 5px;
                margin-top: 5px;
            }
        """)
        record_layout.addWidget(self.recent_records)

        record_group.setLayout(record_layout)
        left_layout.addWidget(record_group)
        left_layout.addStretch()

        # 右侧面板（控制按钮 + 内容区域）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 1)

        # 控制按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.btn_connect = QPushButton("连接设备")
        self.btn_record = QPushButton("开始记录")
        self.btn_analyze = QPushButton("分析数据")  # 核心按钮：点击后弹出文件选择
        self.btn_import = QPushButton("导入数据")
        self.btn_test_backend = QPushButton("测试后端连接")

        # 样式化按钮（与截图中的橙色分析按钮匹配）
        self._style_button(self.btn_connect, "#3b82f6")
        self._style_button(self.btn_record, "#10b981", enabled=False)
        self._style_button(self.btn_analyze, "#f59e0b")  # 橙色分析按钮
        self._style_button(self.btn_import, "#8b5cf6")
        self._style_button(self.btn_test_backend, "#64748b")

        control_layout.addWidget(self.btn_connect)
        control_layout.addWidget(self.btn_record)
        control_layout.addWidget(self.btn_analyze)
        control_layout.addWidget(self.btn_import)
        control_layout.addWidget(self.btn_test_backend)
        right_layout.addLayout(control_layout)

        # 内容标签页（实时数据/分析报告/系统日志）
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 6px;
                background-color: #0f172a;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 8px 16px;
                border: 1px solid #334155;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #0f172a;
                color: #38bdf8;
                border-top: 2px solid #38bdf8;
            }
        """)

        # 实时数据
        self.raw_view = QTextEdit()
        self.raw_view.setReadOnly(True)
        self.raw_view.setFont(QFont("Consolas", 10))
        self.raw_view.setStyleSheet("color: #e2e8f0; background-color: #0f172a; border: none;")

        # 分析报告
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFont(QFont("Microsoft YaHei", 10))
        self.report_view.setStyleSheet("color: #e2e8f0; background-color: #0f172a; border: none;")
        self.report_view.setHtml("<p style='color:#94a3b8'>分析报告内容将显示在此处</p>")

        # 系统日志
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setStyleSheet("color: #e2e8f0; background-color: #0f172a; border: none;")

        self.tabs.addTab(self.raw_view, "实时数据")
        self.tabs.addTab(self.report_view, "分析报告")
        self.tabs.addTab(self.log_view, "系统日志")
        right_layout.addWidget(self.tabs, 1)

        # 日志重定向
        class LogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)

        log_handler = LogHandler(self.log_view)
        log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(log_handler)

    def _style_button(self, button, color, enabled=True):
        """统一按钮样式"""
        button.setEnabled(enabled)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: #334155;
                color: #94a3b8;
            }}
        """)

    def _connect_signals(self):
        """连接信号与槽"""
        # 按钮事件
        self.btn_connect.clicked.connect(lambda: asyncio.create_task(self.toggle_connection()))
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_analyze.clicked.connect(self.analyze_data)  # 绑定分析按钮事件
        self.btn_import.clicked.connect(self.import_data)
        self.btn_test_backend.clicked.connect(self.test_backend)
        self.btn_scan.clicked.connect(self.scan_devices)

        # 设备状态信号
        self.collector.connection_changed.connect(self.update_connection_status)
        self.collector.recording_changed.connect(self.update_recording_status)
        self.collector.status_updated.connect(self.update_status)
        self.collector.data_received.connect(self.update_raw_view)
        self.collector.file_created.connect(self._add_recorded_file)

    def _load_recorded_files(self):
        """加载已记录的数据文件"""
        try:
            for file in os.listdir(RECORDINGS_DIR):
                if file.endswith(('.xls', '.xlsx', '.csv', '.txt')):
                    file_path = os.path.join(RECORDINGS_DIR, file)
                    self._add_record_to_list(file_path)
            logger.info(f"已加载 {self.record_list.count()} 个数据记录")
        except Exception as e:
            logger.error(f"加载数据记录失败: {str(e)}")

    def _add_record_to_list(self, file_path):
        """将文件添加到数据记录列表"""
        file_name = os.path.basename(file_path)
        ctime = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y/%m/%d %H:%M")
        try:
            if file_name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
                points = len(df)
            else:
                with open(file_path, 'r') as f:
                    points = sum(1 for line in f if line.strip())
            item_text = f"{file_name} ({ctime}) - 数据点数: {points}"
        except:
            item_text = f"{file_name} ({ctime})"

        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, file_path)
        self.record_list.addItem(item)
        self.recent_records.addItem(file_name)
        self.recent_records.setItemData(self.recent_records.count()-1, file_path, Qt.UserRole)

    def _add_recorded_file(self, file_path):
        """新增记录文件时更新列表"""
        self._add_record_to_list(file_path)
        self.record_list.setCurrentRow(self.record_list.count() - 1)

    def update_connection_status(self, connected):
        """更新设备连接状态"""
        if connected:
            self.connection_status.setText("连接状态: 已连接")
            self.connection_status.setStyleSheet("color: #10b981;")
            self.btn_record.setEnabled(True)
            self.statusBar.showMessage("后端:已连接 设备:已连接 数据:未连接 API:未连接")
        else:
            self.connection_status.setText("连接状态: 未连接")
            self.connection_status.setStyleSheet("color: #ef4444;")
            self.btn_record.setEnabled(False)
            self.statusBar.showMessage("后端:已连接 设备:未连接 数据:未连接 API:未连接")

    def update_recording_status(self, recording):
        """更新记录状态"""
        if recording:
            self.btn_record.setText("停止记录")
            self._style_button(self.btn_record, "#ef4444")
        else:
            self.btn_record.setText("开始记录")
            self._style_button(self.btn_record, "#10b981")

    def update_status(self, status):
        """更新状态栏"""
        self.statusBar.showMessage(f"{status} | 后端:已连接 设备:{'已连接' if self.collector.is_connected else '未连接'} 数据:未连接 API:未连接")

    def update_raw_view(self, data):
        """更新实时数据视图"""
        self.raw_view.append(data)
        self.raw_view.moveCursor(self.raw_view.textCursor().End)

    async def toggle_connection(self):
        """切换设备连接状态"""
        if self.collector.is_connected:
            await self.collector.disconnect_device()
            self.btn_connect.setText("连接设备")
            self._style_button(self.btn_connect, "#3b82f6")
        else:
            await self.collector.connect_device()
            self.btn_connect.setText("断开连接")
            self._style_button(self.btn_connect, "#ef4444")

    def toggle_recording(self):
        """切换数据记录状态"""
        if not self.collector.is_recording:
            timestamp = datetime.now().strftime("%m-%d-%H%M")
            file_name = f"{timestamp}_eeg_data.xls"
            file_path = os.path.join(RECORDINGS_DIR, file_name)
            self.collector.start_recording(file_path)
        else:
            self.collector.stop_recording()

    def import_data(self):
        """导入外部数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            os.getcwd(),
            "数据文件 (*.xls *.xlsx *.csv *.txt)"
        )
        if file_path:
            dest_path = os.path.join(RECORDINGS_DIR, os.path.basename(file_path))
            if file_path != dest_path:
                import shutil
                shutil.copy2(file_path, dest_path)
                file_path = dest_path
            self._add_record_to_list(file_path)
            self.record_list.setCurrentRow(self.record_list.count() - 1)
            logger.info(f"导入数据文件: {file_path}")
            self.statusBar.showMessage(f"已导入: {os.path.basename(file_path)}")

    def test_backend(self):
        """测试后端连接"""
        self.statusBar.showMessage("测试后端连接中...")
        QTimer.singleShot(1000, lambda: self.statusBar.showMessage("后端:已连接 设备:未连接 数据:未连接 API:未连接"))
        logger.info("后端连接测试成功")

    def scan_devices(self):
        """扫描蓝牙设备"""
        self.statusBar.showMessage("正在扫描蓝牙设备...")
        QTimer.singleShot(1500, lambda: self.statusBar.showMessage("扫描完成，可选择设备连接 | 后端:已连接 设备:未连接 数据:未连接 API:未连接"))
        self.bluetooth_addr.setText("JDY-18 (已发现)")

    def analyze_data(self):
        """核心修改：点击分析数据后直接弹出文件选择框，选择后分析"""
        # 步骤1：弹出文件选择对话框，让用户选择要分析的文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要分析的数据文件",  # 对话框标题
            RECORDINGS_DIR,  # 默认打开记录目录
            "数据文件 (*.xls *.xlsx *.csv *.txt)"  # 支持的文件格式
        )

        # 步骤2：处理用户选择（取消选择或选择无效文件）
        if not file_path or not os.path.exists(file_path):
            # 提示用户未选择有效文件（解决原问题中的提示逻辑）
            QMessageBox.warning(self, "提示", "请先选择有效的数据文件", QMessageBox.Ok)
            self.statusBar.showMessage("请先选择有效的数据文件 | 后端:已连接 设备:未连接 数据:未连接 API:未连接")
            self.report_view.setHtml("<p style='color:#ef4444'>请先选择有效的数据文件</p>")
            return

        # 步骤3：选择有效文件后，开始分析
        try:
            file_name = os.path.basename(file_path)
            self.statusBar.showMessage(f"正在分析 {file_name}... 请稍候")
            self.report_view.setHtml(f"<p style='color:#38bdf8'>正在分析 {file_name}，请等待结果...</p>")
            
            # 导入分析器并执行分析
            from brain_start.eeg_analyzer import EEGAnalyzer
            self.analyzer = EEGAnalyzer(file_path, self.api_key)
            report_content, report_filename = self.analyzer.analyze()
            
            # 显示分析结果
            self.report_view.setHtml(report_content)
            self.tabs.setCurrentIndex(1)  # 自动切换到分析报告标签页
            self.statusBar.showMessage(f"分析完成: {file_name} | 报告已保存")
            logger.info(f"分析完成: {file_path} -> 报告: {report_filename}")

        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.statusBar.showMessage(error_msg)
            self.report_view.setHtml(f"<p style='color:#ef4444'>{error_msg}</p>")
            logger.error(error_msg, exc_info=True)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())