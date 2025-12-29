"""
GUI主窗口模块
使用PyQt5创建用户界面
"""
import sys
import os
import queue
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit,
    QScrollArea, QFileDialog, QMessageBox, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QDesktopWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5.QtGui import QFont
from core import FriendChecker
from utils import FileParser
from config import DEFAULT_THREAD_COUNT, ConfigManager


class CheckWorker(QThread):
    """检查工作线程 - 使用线程池实现真正的并行执行"""
    
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list)
    result_signal = pyqtSignal(tuple)  # 实时结果信号
    
    def __init__(self, profiles: List[tuple], cookies: List[str], headless: bool = False, thread_count: int = None):
        super().__init__()
        self.profiles = profiles
        self.cookies = cookies
        self.headless = headless
        self.thread_count = thread_count  # 添加线程数参数
        self._is_running = True  # 运行标志
        self._mutex = QMutex()  # 线程安全锁
        self._results = []  # 存储结果
        self._completed_count = 0  # 已完成任务计数
        self._checkers = []  # 存储所有checker实例，用于关闭浏览器
        self._executor = None  # 线程池执行器
        self._profile_queue = queue.Queue()  # 线程安全的链接队列
    
    def stop(self):
        """停止检查"""
        with QMutexLocker(self._mutex):
            self._is_running = False
        
        # 立即关闭所有浏览器
        self._close_all_browsers()
    
    def _close_all_browsers(self):
        """关闭所有浏览器实例"""
        for checker in self._checkers:
            try:
                checker.close()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
        self._checkers.clear()
    
    def _initialize_checker(self, checker: FriendChecker, index: int) -> bool:
        """
        初始化单个checker的浏览器
        
        Args:
            checker: FriendChecker实例
            index: checker索引
            
        Returns:
            是否初始化成功
        """
        try:
            self.progress_signal.emit(f"正在初始化浏览器 {index + 1}/{len(self._checkers)}...")
            
            # 初始化浏览器并恢复Cookie
            if not checker.initialize_browser():
                self.progress_signal.emit(f"浏览器 {index + 1} 初始化失败")
                return False
            
            self.progress_signal.emit(f"✓ 浏览器 {index + 1} 初始化完成")
            return True
            
        except Exception as e:
            self.progress_signal.emit(f"浏览器 {index + 1} 初始化出错: {str(e)}")
            return False
    
    def _check_single_profile(self, checker: FriendChecker) -> tuple:
        """
        从队列中获取链接并检查（在独立线程中执行）
        
        Args:
            checker: FriendChecker实例
            
        Returns:
            检查结果元组
        """
        try:
            # 从队列中获取链接（线程安全）
            try:
                url, name = self._profile_queue.get(timeout=1)
            except queue.Empty:
                return None  # 队列为空，返回None
            
            # 检查是否被停止
            with QMutexLocker(self._mutex):
                if not self._is_running:
                    return (url, name, False, "检查已停止", False)
            
            is_visible, message, is_valid = checker.check_friend_visibility(url, name)
            result = (url, name, is_visible, message, is_valid)
            
            # 检查完成后，从文件中删除这个链接
            if hasattr(self, 'file_path') and self.file_path:
                FileParser.remove_checked_link(self.file_path, url)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            # 提供更友好的错误信息
            if "WinError 193" in error_msg or "不是有效的 Win32 应用程序" in error_msg:
                error_msg = "ChromeDriver版本不兼容，请重新安装依赖"
            return (url, name, False, f"检查失败: {error_msg}", False)
    
    def run(self):
        """执行检查任务 - 使用线程池并行执行"""
        # 为每个Cookie创建一个FriendChecker实例（每个线程独立使用）
        self._checkers = []
        # 使用设置的线程数，如果没有设置则使用Cookie数量
        total_threads = self.thread_count if self.thread_count is not None else len(self.cookies)
        # 只使用前 total_threads 个Cookie
        cookies_to_use = self.cookies[:total_threads]
        for i, cookie_string in enumerate(cookies_to_use):
            checker = FriendChecker(cookie_string, headless=self.headless, thread_index=i, total_threads=total_threads)
            self._checkers.append(checker)
        
        try:
            # 第一步：初始化所有浏览器（确保浏览器正常打开后再开始检测）
            self.progress_signal.emit("正在初始化浏览器...")
            initialized_checkers = []
            
            for i, checker in enumerate(self._checkers):
                # 检查是否被停止
                with QMutexLocker(self._mutex):
                    if not self._is_running:
                        self.progress_signal.emit("检查已停止")
                        break
                
                # 初始化浏览器
                if self._initialize_checker(checker, i):
                    initialized_checkers.append(checker)
                else:
                    self.progress_signal.emit(f"警告: 浏览器 {i + 1} 初始化失败，将跳过")
            
            # 如果没有成功初始化的浏览器，直接返回
            if not initialized_checkers:
                self.progress_signal.emit("没有可用的浏览器，检查终止")
                self.finished_signal.emit(self._results)
                return
            
            self.progress_signal.emit(f"✓ 所有浏览器初始化完成，共 {len(initialized_checkers)} 个可用")
            
            # 第二步：将所有链接放入队列（线程安全）
            for url, name in self.profiles:
                self._profile_queue.put((url, name))
            
            # 第三步：使用线程池并行执行任务
            # max_workers 设置为已初始化的 checker 数量
            self._executor = ThreadPoolExecutor(max_workers=len(initialized_checkers))
            
            # 为每个checker创建一个持续运行的任务
            future_to_checker = {}
            for checker in initialized_checkers:
                future = self._executor.submit(self._process_profiles, checker)
                future_to_checker[future] = checker
            
            # 等待所有任务完成
            for future in as_completed(future_to_checker):
                # 检查是否被停止
                with QMutexLocker(self._mutex):
                    if not self._is_running:
                        break
                
                try:
                    future.result()  # 等待任务完成
                except Exception as e:
                    print(f"处理任务时出错: {e}")
        
        except Exception as e:
            self.progress_signal.emit(f"执行过程中出错: {str(e)}")
        
        finally:
            # 关闭线程池
            if self._executor:
                self._executor.shutdown(wait=False)
            
            # 关闭所有浏览器
            self._close_all_browsers()
        
        # 发送完成信号
        self.finished_signal.emit(self._results)
    
    def _process_profiles(self, checker: FriendChecker):
        """
        持续从队列中获取链接并处理
        
        Args:
            checker: FriendChecker实例
        """
        while True:
            # 检查是否被停止
            with QMutexLocker(self._mutex):
                if not self._is_running:
                    break
            
            # 从队列中获取链接并检查
            result = self._check_single_profile(checker)
            
            # 如果返回None，说明队列为空，退出循环
            if result is None:
                break
            
            url, name = result[0], result[1]
            
            # 线程安全地添加结果
            with QMutexLocker(self._mutex):
                self._results.append(result)
                self._completed_count += 1
            
            # 实时发送结果到主线程
            self.result_signal.emit(result)
            self.progress_signal.emit(f"✓ {name} 检查完成 ({self._completed_count}/{len(self.profiles)})")


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.cookie_inputs = []
        self.cookie_rows = []  # 存储cookie行widget
        self.profiles = []
        self.check_results = []  # 存储检查结果
        self.worker = None
        self.result_row_count = 0  # 结果表格行数计数器
        self.screen = QDesktopWidget().screenGeometry()  # 获取屏幕尺寸
        self.init_ui()
        self.load_config()  # 加载保存的配置
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('Facebook好友可见性检查工具')
        self.setGeometry(100, 100, 600, 250)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel('Facebook好友可见性检查工具')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 线程设置区域
        thread_group = self.create_thread_group()
        main_layout.addWidget(thread_group)
        
        # Cookie输入区域
        cookie_group = self.create_cookie_group()
        main_layout.addWidget(cookie_group)
        
        # 文件上传区域
        file_group = self.create_file_group()
        main_layout.addWidget(file_group)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('开始检查')
        self.start_button.setFont(QFont('Arial', 12))
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_check)
        self.start_button.setEnabled(False)
        
        self.stop_button = QPushButton('停止检查')
        self.stop_button.setFont(QFont('Arial', 12))
        self.stop_button.setMinimumHeight(40)
        self.stop_button.clicked.connect(self.stop_check)
        self.stop_button.setEnabled(False)
        
        self.export_button = QPushButton('导出有效链接')
        self.export_button.setFont(QFont('Arial', 12))
        self.export_button.setMinimumHeight(40)
        self.export_button.clicked.connect(self.export_valid_links)
        self.export_button.setEnabled(False)
        
        self.clear_button = QPushButton('清空')
        self.clear_button.setFont(QFont('Arial', 12))
        self.clear_button.setMinimumHeight(40)
        self.clear_button.clicked.connect(self.clear_all)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        # 结果显示区域
        result_group = self.create_result_group()
        main_layout.addWidget(result_group)
        
        # 初始化Cookie输入框
        self.init_cookie_inputs()
    
    def create_thread_group(self) -> QGroupBox:
        """创建线程设置组"""
        group = QGroupBox('线程设置')
        layout = QHBoxLayout()
        
        thread_label = QLabel('线程数量:')
        thread_label.setFont(QFont('Arial', 10))
        
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setMinimum(1)
        self.thread_spinbox.setMaximum(20)
        self.thread_spinbox.setValue(DEFAULT_THREAD_COUNT)
        self.thread_spinbox.setFont(QFont('Arial', 10))
        self.thread_spinbox.valueChanged.connect(self.update_cookie_inputs)
        
        # 无头模式复选框
        self.headless_checkbox = QCheckBox('无头模式')
        self.headless_checkbox.setFont(QFont('Arial', 10))
        self.headless_checkbox.setToolTip('勾选后浏览器将在后台运行，不显示窗口')
        
        layout.addWidget(thread_label)
        layout.addWidget(self.thread_spinbox)
        layout.addWidget(self.headless_checkbox)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_cookie_group(self) -> QGroupBox:
        """创建Cookie输入组"""
        group = QGroupBox('Cookie设置')
        layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # 不设置固定高度，让内容自适应
        scroll.setMinimumHeight(100)
        
        # Cookie输入容器
        self.cookie_container = QWidget()
        self.cookie_layout = QVBoxLayout(self.cookie_container)
        self.cookie_layout.setSpacing(8)
        self.cookie_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(self.cookie_container)
        layout.addWidget(scroll)
        
        group.setLayout(layout)
        return group
    
    def create_file_group(self) -> QGroupBox:
        """创建文件上传组"""
        group = QGroupBox('链接文件')
        layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText('请选择包含Facebook链接的文件 (格式: 链接----名字)')
        self.file_path_edit.setReadOnly(True)
        
        self.upload_button = QPushButton('上传文件')
        self.upload_button.clicked.connect(self.upload_file)
        
        layout.addWidget(self.file_path_edit)
        layout.addWidget(self.upload_button)
        
        group.setLayout(layout)
        return group
    
    def create_result_group(self) -> QGroupBox:
        """创建结果显示组"""
        group = QGroupBox('检查结果')
        layout = QVBoxLayout()
        
        # 创建表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(['链接', '名字', '好友列表可见', '链接有效性'])
        
        # 设置表格属性
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.result_table)
        
        group.setLayout(layout)
        return group
    
    def init_cookie_inputs(self):
        """初始化Cookie输入框（预先创建20个）"""
        # 预先创建20个Cookie输入框
        for i in range(20):
            # 为每个Cookie创建一个水平布局
            cookie_row = QWidget()
            row_layout = QHBoxLayout(cookie_row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            
            # 创建标签
            label = QLabel(f'Cookie {i + 1}:')
            label.setFont(QFont('Arial', 9))
            label.setMinimumWidth(70)
            label.setMaximumWidth(70)
            
            # 创建输入框
            input_field = QLineEdit()
            input_field.setPlaceholderText('请输入Facebook Cookie字符串')
            input_field.setFont(QFont('Arial', 9))
            
            # 添加到行布局
            row_layout.addWidget(label)
            row_layout.addWidget(input_field)
            
            # 添加到主布局
            self.cookie_layout.addWidget(cookie_row)
            self.cookie_rows.append(cookie_row)
            self.cookie_inputs.append(input_field)
        
        # 添加弹性空间
        self.cookie_layout.addStretch()
        
        # 初始显示数量
        self.update_cookie_inputs()
    
    def update_cookie_inputs(self):
        """更新Cookie输入框显示数量"""
        thread_count = self.thread_spinbox.value()
        
        # 只显示/隐藏，不创建/删除
        for i in range(20):
            if i < thread_count:
                self.cookie_rows[i].show()
            else:
                self.cookie_rows[i].hide()
        
        # 动态调整窗口大小
        self.adjust_window_size(thread_count)
    
    def upload_file(self):
        """上传文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择链接文件',
            '',
            'Text Files (*.txt);;All Files (*)'
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
            # 解析文件
            self.profiles = FileParser.parse_links_file(file_path)
            
            if self.profiles:
                self.result_table.setRowCount(0)
                self.check_results.clear()
                print(f'成功加载 {len(self.profiles)} 个链接')
                self.start_button.setEnabled(True)
                self.export_button.setEnabled(False)
                
                # 保存文件路径供worker使用
                self.worker = None  # 重置worker
            else:
                QMessageBox.warning(self, '警告', '未能从文件中解析出有效的链接')
                self.start_button.setEnabled(False)
    
    def start_check(self):
        """开始检查"""
        # 获取Cookie
        cookies = []
        for input_field in self.cookie_inputs:
            cookie = input_field.text().strip()
            if cookie:
                cookies.append(cookie)
        
        if not cookies:
            QMessageBox.warning(self, '警告', '请至少输入一个Cookie')
            return
        
        if not self.profiles:
            QMessageBox.warning(self, '警告', '请先上传链接文件')
            return
        
        # 保存配置
        thread_count = self.thread_spinbox.value()
        headless = self.headless_checkbox.isChecked()
        ConfigManager.save_config(thread_count, cookies, headless)
        
        # 禁用按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.thread_spinbox.setEnabled(False)
        self.result_table.setRowCount(0)
        self.check_results.clear()
        self.result_row_count = 0  # 重置行数计数器
        
        # 创建并启动工作线程
        headless = self.headless_checkbox.isChecked()
        thread_count = self.thread_spinbox.value()  # 获取设置的线程数
        self.worker = CheckWorker(self.profiles, cookies, headless, thread_count)
        self.worker.file_path = self.file_path_edit.text()  # 传递文件路径
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.result_signal.connect(self.on_result_received)  # 连接实时结果信号
        self.worker.start()
    
    def stop_check(self):
        """停止检查"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.stop_button.setEnabled(False)
    
    def on_progress(self, message: str):
        """处理进度更新"""
        print(message)
    
    def on_result_received(self, result: tuple):
        """实时接收检查结果"""
        url, name, is_visible, message, is_valid = result
        
        # 添加到结果列表
        self.check_results.append(result)
        
        # 添加到表格
        row = self.result_row_count
        self.result_table.insertRow(row)
        
        # 链接
        self.result_table.setItem(row, 0, QTableWidgetItem(url))
        
        # 名字
        self.result_table.setItem(row, 1, QTableWidgetItem(name))
        
        # 好友列表可见
        visible_text = '是' if is_visible else '否'
        visible_item = QTableWidgetItem(visible_text)
        visible_item.setForeground(Qt.green if is_visible else Qt.red)
        self.result_table.setItem(row, 2, visible_item)
        
        # 链接有效性
        valid_text = '是' if is_valid else '否'
        valid_item = QTableWidgetItem(valid_text)
        valid_item.setForeground(Qt.green if is_valid else Qt.red)
        self.result_table.setItem(row, 3, valid_item)
        
        # 滚动到最新行
        self.result_table.scrollToBottom()
        
        # 更新行数计数器
        self.result_row_count += 1
    
    def on_finished(self, results: List[tuple]):
        """处理检查完成"""
        # 统计结果
        valid_count = sum(1 for _, _, _, _, is_valid in results if is_valid)
        visible_count = sum(1 for _, _, is_visible, _, is_valid in results if is_visible and is_valid)
        
        print(f'\n检查完成!')
        print(f'总计: {len(results)} 个用户')
        print(f'有效链接: {valid_count} 个')
        print(f'好友列表可见: {visible_count} 个')
        print(f'好友列表不可见: {valid_count - visible_count} 个')
        
        # 重新启用按钮
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(valid_count > 0)
        self.upload_button.setEnabled(True)
        self.thread_spinbox.setEnabled(True)
    
    def export_valid_links(self):
        """导出有效链接"""
        if not self.check_results:
            QMessageBox.warning(self, '警告', '没有可导出的结果')
            return
        
        # 筛选有效链接
        valid_links = [(url, name) for url, name, _, _, is_valid in self.check_results if is_valid]
        
        if not valid_links:
            QMessageBox.warning(self, '警告', '没有有效的链接可导出')
            return
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存有效链接',
            '',
            'Text Files (*.txt);;All Files (*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for url, name in valid_links:
                        f.write(f'{url}----{name}\n')
                
                QMessageBox.information(self, '成功', f'已导出 {len(valid_links)} 个有效链接')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')
    
    def clear_all(self):
        """清空所有内容"""
        self.file_path_edit.clear()
        self.result_table.setRowCount(0)
        self.check_results.clear()
        self.profiles.clear()
        
        for input_field in self.cookie_inputs:
            input_field.clear()
        
        self.start_button.setEnabled(False)
        self.export_button.setEnabled(False)
    
    def load_config(self):
        """加载保存的配置"""
        config = ConfigManager.load_config()
        
        # 设置线程数量
        thread_count = config.get('thread_count', DEFAULT_THREAD_COUNT)
        self.thread_spinbox.setValue(thread_count)
        
        # 设置无头模式
        headless = config.get('headless', False)
        self.headless_checkbox.setChecked(headless)
        
        # 设置Cookie
        cookies = config.get('cookies', [])
        for i, cookie in enumerate(cookies):
            if i < len(self.cookie_inputs):
                self.cookie_inputs[i].setText(cookie)
        
        print(f"已加载配置: 线程数={thread_count}, Cookie数={len(cookies)}, 无头模式={headless}")
    
    def adjust_window_size(self, thread_count: int):
        """根据线程数量动态调整窗口大小"""
        # 获取屏幕尺寸
        screen_width = self.screen.width()
        screen_height = self.screen.height()
        
        # 设置窗口宽度（使用屏幕宽度的 40%）
        window_width = int(screen_width * 0.4)
        # 确保窗口宽度至少 400px
        window_width = max(window_width, 400)
        
        # 计算各个组件的高度（固定值）
        # 标题高度
        title_height = 30
        # 线程设置高度
        thread_group_height = 40
        # Cookie设置高度（根据线程数量动态计算，但限制最大值）
        cookie_row_height = 25
        cookie_group_height = min(cookie_row_height * thread_count + 20, 80)
        # 文件上传高度
        file_group_height = 40
        # 按钮区域高度
        button_height = 40
        # 结果显示区域高度（固定值）
        result_group_height = 80
        
        # 计算总高度
        total_height = title_height + thread_group_height + cookie_group_height + file_group_height + button_height + result_group_height + 60
        
        # 设置窗口大小
        self.resize(window_width, total_height)
        
        # 居中显示窗口
        x = (screen_width - window_width) // 2
        y = (screen_height - total_height) // 2
        self.move(x, y)
        
        print(f"窗口大小已调整为: {window_width} x {total_height} (屏幕: {screen_width} x {screen_height})")
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.worker and self.worker.isRunning():
            # 先停止检查
            self.worker.stop()
            self.worker.wait()
            event.accept()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()