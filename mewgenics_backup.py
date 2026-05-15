import os
import shutil
import glob
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QTextEdit, QMessageBox, QFrame,
    QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

class SaveManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mewgenics Save Manager")
        self.setMinimumSize(QSize(500, 500))
        
        # Paths configuration
        self.roaming_path = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics')
        self.save_slots = [
            "steamcampaign01.sav",
            "steamcampaign02.sav",
            "steamcampaign03.sav"
        ]
        self.game_exe_path = ""
        
        self.init_ui()
        self.detect_save_path()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Mewgenics Save Backup Utility")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Path Status
        self.path_label = QLabel("Path: Searching...")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.path_label)

        # Game EXE Configuration
        exe_layout = QVBoxLayout()
        exe_layout.addWidget(QLabel("Mewgenics.exe Path:"))
        exe_input_layout = QHBoxLayout()
        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText("Select Mewgenics.exe location...")
        self.exe_browse_btn = QPushButton("Browse")
        self.exe_browse_btn.clicked.connect(self.browse_exe)
        exe_input_layout.addWidget(self.exe_input)
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
        slot_layout.addWidget(QLabel("Select Save Slot:"))
        self.slot_combo = QComboBox()
        self.slot_combo.addItems(self.save_slots)
        slot_layout.addWidget(self.slot_combo)
        layout.addLayout(slot_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.backup_btn = QPushButton("Backup to Local")
        self.backup_btn.setFixedHeight(40)
        self.backup_btn.clicked.connect(self.perform_backup)
        self.backup_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        self.restore_btn = QPushButton("Restore from Local")
        self.restore_btn.setFixedHeight(40)
        self.restore_btn.clicked.connect(self.perform_restore)
        self.restore_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        
        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        # Quick Restart Button
        self.restart_btn = QPushButton("⚡ QUICK RESTART (Backup + Kill + Launch)")
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

        # Log Area
        layout.addWidget(QLabel("Activity Log:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        self.log_area.setStyleSheet("background-color: #1a1a1a; color: #00ff00;")
        layout.addWidget(self.log_area)

        self.log("Ready.")

    def log(self, message):
        self.log_area.append(f"> {message}")

    def browse_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Mewgenics.exe", "", "Executable Files (*.exe)")
        if file_path:
            self.exe_input.setText(file_path)
            self.game_exe_path = file_path

    def detect_save_path(self):
        if not os.path.exists(self.roaming_path):
            self.log(f"Error: Path not found: {self.roaming_path}")
            self.path_label.setText("Error: Game data folder not found.")
            self.disable_controls()
            return

        search_pattern = os.path.join(self.roaming_path, "*", "saves")
        save_dirs = glob.glob(search_pattern)

        if not save_dirs:
            self.log("Error: Could not find any 'saves' directory.")
            self.path_label.setText("Error: 'saves' folder not found.")
            self.disable_controls()
            return

        self.base_save_path = save_dirs[0]
        self.backup_path = os.path.join(self.base_save_path, "my_backup")
        
        self.path_label.setText(f"Active Dir: {self.base_save_path}")
        self.log(f"Detected save directory: {self.base_save_path}")
        
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            self.log("Created 'my_backup' subdirectory.")

    def disable_controls(self):
        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.slot_combo.setEnabled(False)

    def perform_backup(self, silent=False):
        filename = self.slot_combo.currentText()
        src = os.path.join(self.base_save_path, filename)
        dst = os.path.join(self.backup_path, filename)

        if not os.path.exists(src):
            self.log(f"Error: Original file {filename} does not exist.")
            return False

        try:
            shutil.copy2(src, dst)
            self.log(f"SUCCESS: Backed up {filename} to my_backup.")
            if not silent:
                QMessageBox.information(self, "Success", f"Backup complete for {filename}")
            return True
        except Exception as e:
            self.log(f"Backup Error: {str(e)}")
            return False

    def perform_restore(self):
        filename = self.slot_combo.currentText()
        src = os.path.join(self.backup_path, filename)
        dst = os.path.join(self.base_save_path, filename)

        if not os.path.exists(src):
            self.log(f"Error: Backup file {filename} not found.")
            return

        reply = QMessageBox.question(self, 'Confirm Restore', 
                                   f"Overwrite current save with the backup of {filename}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.copy2(src, dst)
                self.log(f"SUCCESS: Restored {filename} from my_backup.")
                QMessageBox.information(self, "Success", f"Restoration complete for {filename}")
            except Exception as e:
                self.log(f"Restore Error: {str(e)}")

    def perform_quick_restart(self):
        exe_path = self.exe_input.text().strip()
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(self, "Path Error", "Please provide a valid path to Mewgenics.exe first.")
            return

        # 1. Backup
        self.log("Phase 1: Backing up selected save...")
        if not self.perform_backup(silent=True):
            self.log("Quick Restart aborted due to backup failure.")
            return

        # 2. Kill process
        self.log("Phase 2: Terminating mewgenics.exe process...")
        try:
            # Using taskkill on Windows to ensure termination
            subprocess.run(["taskkill", "/F", "/IM", "mewgenics.exe", "/T"], 
                          capture_output=True, text=True)
            self.log("Process termination command sent.")
        except Exception as e:
            self.log(f"Process termination error: {str(e)}")

        # 3. Launch
        self.log(f"Phase 3: Launching {exe_path}...")
        try:
            # Use Popen to launch without blocking our GUI
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            self.log("Game launched successfully.")
            QMessageBox.information(self, "Quick Restart", "Quick Restart Sequence Complete!")
        except Exception as e:
            self.log(f"Launch error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to launch game: {str(e)}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SaveManager()
    window.show()
    sys.exit(app.exec())
