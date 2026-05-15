# Mewgenics SL Master

一个为《Mewgenics》设计的辅助工具，支持存档自动备份、读档、以及快速 SL（重启游戏并恢复存档）。

## 功能特性

- **一键备份/读档**: 轻松管理不同槽位的存档。
- **自动检测**: 通过运行中的游戏进程自动定位 `Mewgenics.exe` 路径。
- **快速 SL**: 备份当前进度 -> 结束游戏进程 -> 重新启动 -> 自动读档。
- **窗口置顶**: 方便在游戏运行期间快速操作。
- **配置持久化**: 自动保存路径、槽位选择及窗口设置到 `saved/config.json`。

## 环境要求

在直接运行 `.py` 源代码之前，请确保已安装 Python 并安装以下依赖库：

```bash
pip install PyQt6 psutil
```

## 使用方法

### 直接运行源代码
1. 确保已安装上述依赖。
2. 在终端/命令行运行：
   ```bash
   python mewgenics_backup.py
   ```
   *或者使用提供的 `run.bat` (Windows)。*

### 构建单文件 EXE
如果你想将其打包成一个独立的本地程序，可以使用 `PyInstaller`：

1. 安装 PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. 执行构建命令：
   ```bash
   pyinstaller --onefile --noconsole mewgenics_backup.py
   ```
   *注：构建完成后，可执行文件将出现在 `dist` 文件夹中。*

## 文件说明

- `mewgenics_backup.py`: 工具主代码。
- `saved/config.json`: 存储你的个性化设置（路径、槽位等）。
- `saved/MewgenicsSL.log`: 程序运行日志。
- `my_backup/`: 存档文件实际备份存储的位置。

## 注意事项

- **自动检测**: 需要游戏正在运行才能成功识别路径。若未运行，请手动点击“浏览”选择。
- **存档路径**: 工具会自动寻找 `%APPDATA%\Glaiel Games\Mewgenics` 下的存档目录。