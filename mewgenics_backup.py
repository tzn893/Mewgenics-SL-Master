import os
import shutil
import glob
import subprocess
import json
import datetime
try:
    import psutil
except ImportError:
    psutil = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QMessageBox, QFrame,
    QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

class SaveManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mewgenics SL Master")
        self.setMinimumSize(QSize(500, 350))
        
        # Paths configuration
        self.roaming_path = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics')
        self.save_slots = [
            "steamcampaign01.sav",
            "steamcampaign02.sav",
            "steamcampaign03.sav"
        ]
        self.game_exe_path = ""
        self.always_on_top = False
        self.log_entries = []
        
        # Ensure saved directory exists
        self.config_dir = "saved"
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.log_file_path = os.path.join(self.config_dir, "MewgenicsSL.log")
        
        self.init_ui()
        self.detect_save_path()
        self.load_config()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header and Top-most toggle
        top_bar_layout = QHBoxLayout()
        header = QLabel("Mewgenics SL Master")
        header.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PyQt6.QtWidgets import QCheckBox
        self.top_most_checkbox = QCheckBox("窗口置顶")
        self.top_most_checkbox.setStyleSheet("font-size: 11px; color: #34495e;")
        self.top_most_checkbox.stateChanged.connect(self.toggle_top_most)
        
        top_bar_layout.addWidget(header, 1)
        top_bar_layout.addWidget(self.top_most_checkbox)
        layout.addLayout(top_bar_layout)

        # Path Status
        self.path_label = QLabel("路径: 正在搜索...")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.path_label)

        # Game EXE Configuration
        exe_layout = QVBoxLayout()
        
        exe_header_layout = QHBoxLayout()
        exe_header_layout.addWidget(QLabel("Mewgenics.exe 路径:"))
        
        self.auto_detect_btn = QPushButton("自动检测")
        self.auto_detect_btn.setFixedWidth(120)
        self.auto_detect_btn.clicked.connect(self.detect_exe_by_process)
        self.auto_detect_btn.setStyleSheet("font-size: 11px; padding: 2px; background-color: #34495e; color: white;")
        exe_header_layout.addWidget(self.auto_detect_btn)
        
        exe_layout.addLayout(exe_header_layout)
        
        exe_input_layout = QHBoxLayout()
        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText("请选择 Mewgenics.exe 的位置...")
        self.exe_input.textChanged.connect(self.save_config)
        self.exe_browse_btn = QPushButton("浏览")
        self.exe_browse_btn.setFixedWidth(80)
        self.exe_browse_btn.clicked.connect(self.browse_exe)
        exe_input_layout.addWidget(self.exe_input, 1)
        exe_input_layout.addWidget(self.exe_browse_btn)
        exe_layout.addLayout(exe_input_layout)
        layout.addLayout(exe_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Slot Selection
        slot_layout = QHBoxLayout()
        slot_layout.addWidget(QLabel("选择存档槽位:"))
        self.slot_combo = QComboBox()
        self.slot_combo.addItems(self.save_slots)
        self.slot_combo.currentIndexChanged.connect(self.save_config)
        slot_layout.addWidget(self.slot_combo)
        layout.addLayout(slot_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.backup_btn = QPushButton("备份")
        self.backup_btn.setFixedHeight(40)
        self.backup_btn.clicked.connect(self.perform_backup)
        self.backup_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        self.restore_btn = QPushButton("读档")
        self.restore_btn.setFixedHeight(40)
        self.restore_btn.clicked.connect(self.perform_restore)
        self.restore_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        
        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        # Quick Restart Button
        self.restart_btn = QPushButton("⚡ 快速SL (备份 + 结束进程 + 重新启动 + 读档)")
        self.restart_btn.setFixedHeight(50)
        self.restart_btn.clicked.connect(self.perform_quick_restart)
        self.restart_btn.setStyleSheet("""
            background-color: #e67e22; 
            color: white; 
            font-weight: bold; 
            border: 2px solid #d35400;
            border-radius: 5px;
        """)
        layout.addWidget(self.restart_btn)

        # Direct Restart Button (New)
        self.direct_restart_btn = QPushButton("🔄 直接重启 (结束进程 + 读档 + 重新启动)")
        self.direct_restart_btn.setFixedHeight(50)
        self.direct_restart_btn.clicked.connect(self.perform_direct_restart)
        self.direct_restart_btn.setStyleSheet("""
            background-color: #c0392b; 
            color: white; 
            font-weight: bold; 
            border: 2px solid #962d22;
            border-radius: 5px;
        """)
        layout.addWidget(self.direct_restart_btn)

        layout.addStretch()
        self.log("工具就绪。")

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.log_entries.append(entry)
        print(entry)

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    exe_path = config.get("exe_path", "")
                    selected_slot = config.get("selected_slot", "")
                    always_on_top = config.get("always_on_top", False)
                    
                    if exe_path:
                        self.exe_input.setText(exe_path)
                        self.game_exe_path = exe_path
                    
                    if selected_slot in self.save_slots:
                        index = self.save_slots.index(selected_slot)
                        self.slot_combo.setCurrentIndex(index)
                    
                    self.top_most_checkbox.setChecked(always_on_top)
                    self.toggle_top_most(always_on_top)
                self.log("已从 config.json 读取配置。")
            except Exception as e:
                self.log(f"读取配置失败: {str(e)}")

    def save_config(self):
        config = {
            "exe_path": self.exe_input.text().strip(),
            "selected_slot": self.slot_combo.currentText(),
            "always_on_top": self.top_most_checkbox.isChecked()
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")

    def toggle_top_most(self, state):
        should_be_on_top = bool(state)
        # Using WindowStaysOnTopHint for always on top
        if should_be_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        
        # In Qt, changing flags hides the window, so we must show it again
        self.show()
        self.save_config()

    def closeEvent(self, event):
        try:
            if self.log_entries:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write("\n" + "="*50 + "\n")
                    f.write(f"Session end at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("\n".join(self.log_entries))
                    f.write("\n" + "="*50 + "\n")
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
        event.accept()

    def detect_exe_by_process(self):
        if psutil is None:
            self.log("错误: 未找到 'psutil' 库。请通过 'pip install psutil' 安装。")
            QMessageBox.warning(self, "依赖缺失", "自动检测功能需要 'psutil' 库。\n\n请在终端运行 'pip install psutil'。")
            return

        self.log("正在搜索运行中的 Mewgenics 进程...")
        found_path = None
        
        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    # 严格匹配进程名 Mewgenics.exe
                    if proc.info['name'] and proc.info['name'].lower() == 'mewgenics.exe':
                        if proc.info['exe']:
                            found_path = proc.info['exe']
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if found_path:
                self.exe_input.setText(found_path)
                self.game_exe_path = found_path
                self.log(f"已自动检测到运行中的游戏路径: {found_path}")
                QMessageBox.information(self, "检测成功", f"找到运行中的游戏：\n{found_path}")
                self.save_config()
            else:
                self.log("自动检测失败: 未找到运行中的 Mewgenics 进程。")
                QMessageBox.warning(self, "检测失败", "未能找到运行中的 Mewgenics 进程。\n\n请先启动游戏，然后再点击自动检测。")
        except Exception as e:
            self.log(f"检测出错: {str(e)}")

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Mewgenics.exe", "", "可执行文件 (*.exe)")
        if file_path:
            self.exe_input.setText(file_path)
            self.game_exe_path = file_path
            self.save_config()

    def detect_save_path(self):
        if not os.path.exists(self.roaming_path):
            self.log(f"错误: 未找到路径: {self.roaming_path}")
            self.path_label.setText("错误: 未找到游戏数据文件夹。")
            self.disable_controls()
            return

        search_pattern = os.path.join(self.roaming_path, "*", "saves")
        save_dirs = glob.glob(search_pattern)

        if not save_dirs:
            self.log("错误: 未能找到 'saves' 存档目录。")
            self.path_label.setText("错误: 未找到 'saves' 文件夹。")
            self.disable_controls()
            return

        self.base_save_path = save_dirs[0]
        self.backup_path = os.path.join(self.base_save_path, "my_backup")
        
        self.path_label.setText(f"当前存档目录: {self.base_save_path}")
        self.log(f"检测到存档目录: {self.base_save_path}")
        
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            self.log("已创建 'my_backup' 备份子目录。")

    def disable_controls(self):
        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.direct_restart_btn.setEnabled(False)
        self.slot_combo.setEnabled(False)

    def perform_backup(self, silent=False):
        filename = self.slot_combo.currentText()
        src = os.path.join(self.base_save_path, filename)
        dst = os.path.join(self.backup_path, filename)

        if not os.path.exists(src):
            self.log(f"错误: 原始存档文件 {filename} 不存在。")
            return False

        try:
            shutil.copy2(src, dst)
            self.log(f"成功: 已将 {filename} 备份至 my_backup 文件夹。")
            if not silent:
                QMessageBox.information(self, "成功", f"存档 {filename} 备份完成")
            return True
        except Exception as e:
            self.log(f"备份出错: {str(e)}")
            return False

    def perform_restore(self, silent=False):
        filename = self.slot_combo.currentText()
        src = os.path.join(self.backup_path, filename)
        dst = os.path.join(self.base_save_path, filename)

        if not os.path.exists(src):
            self.log(f"错误: 未在 my_backup 中找到备份文件 {filename}。")
            return False

        if not silent:
            reply = QMessageBox.question(self, '确认读档', 
                                       f"确定要从备份恢复 {filename} 存档吗？",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return False

        try:
            shutil.copy2(src, dst)
            self.log(f"成功: 已从 my_backup 读档恢复 {filename}。")
            if not silent:
                QMessageBox.information(self, "成功", f"存档 {filename} 读档完成")
            return True
        except Exception as e:
            self.log(f"读档出错: {str(e)}")
            return False

    def perform_quick_restart(self):
        exe_path = self.exe_input.text().strip()
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(self, "路径错误", "请先提供有效的 Mewgenics.exe 路径。")
            return

        # 1. Backup
        self.log("阶段 1: 正在备份选中的存档...")
        if not self.perform_backup(silent=True):
            self.log("由于备份失败，快速SL已中止。")
            return

        # 2. Kill process
        self.log("阶段 2: 正在结束 mewgenics.exe 进程...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "mewgenics.exe", "/T"], 
                          capture_output=True, text=True)
            self.log("结束进程指令已发送。")
        except Exception as e:
            self.log(f"结束进程出错: {str(e)}")

        # 3. Launch
        self.log(f"阶段 3: 正在重新启动游戏并读档...")
        try:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            self.log("游戏已成功启动。")
            QMessageBox.information(self, "快速SL", "快速SL序列执行完成！")
        except Exception as e:
            self.log(f"启动出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法启动游戏: {str(e)}")

    def perform_direct_restart(self):
        exe_path = self.exe_input.text().strip()
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(self, "路径错误", "请先提供有效的 Mewgenics.exe 路径。")
            return

        # 1. Kill process
        self.log("开始直接重启流程...")
        self.log("阶段 1: 正在结束 mewgenics.exe 进程...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "mewgenics.exe", "/T"], 
                          capture_output=True, text=True)
        except Exception as e:
            self.log(f"结束进程出错: {str(e)}")

        # 2. Restore (Load)
        self.log("阶段 2: 正在从备份读档...")
        if not self.perform_restore(silent=True):
            self.log("读档失败，中止启动。")
            return

        # 3. Launch
        self.log(f"阶段 3: 正在重新启动游戏...")
        try:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            self.log("游戏已重新启动。")
            QMessageBox.information(self, "直接重启", "直接重启流程已完成！")
        except Exception as e:
            self.log(f"启动出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法启动游戏: {str(e)}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SaveManager()
    window.show()
    sys.exit(app.exec())
    
