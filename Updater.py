import os
import sys
import shutil
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QVBoxLayout, QSizePolicy, QWidget, QMessageBox, QPushButton, QProgressBar, QLabel

from QEasyWidgets.Utils import CheckUpdate, DownloadFile, NormPath, SetRichText, RunBat, BootWithBat, GetFileInfo, GetBaseDir, ManageConfig
from EVT_GUI.Functions import Function_AnimateProgressBar, Function_SetText, Function_ShowMessageBox

##############################################################################################################################

_, IsFileCompiled = GetFileInfo()


TargetDir = GetBaseDir(__file__ if IsFileCompiled == False else sys.executable)
#os.chdir(TargetDir)

ResourceDir = TargetDir if GetBaseDir(SearchMEIPASS = True) is None else GetBaseDir(SearchMEIPASS = True)


ConfigPath = NormPath(Path(TargetDir).joinpath('Config', 'Config.ini'))
Config = ManageConfig(ConfigPath)


CurrentVersion = str(Config.GetValue('Info', 'CurrentVersion'))
ExecuterName = str(Config.GetValue('Info', 'ExecuterName'))
DownloadDir = TargetDir
ExtractDir = NormPath(Path(TargetDir).joinpath('Temp'))
ExecuterPath = NormPath(Path(TargetDir).joinpath(ExecuterName))


FoldersToKeep = [NormPath(Path(TargetDir).joinpath('Config'))]
if Path(TargetDir).joinpath('FFmpeg').exists():
    FoldersToKeep.append(NormPath(Path(TargetDir).joinpath('FFmpeg')))
if Path(TargetDir).joinpath('Python').exists():
    FoldersToKeep.append(NormPath(Path(TargetDir).joinpath('Python')))
if Path(TargetDir).joinpath('Download').exists():
    FoldersToKeep.append(NormPath(Path(TargetDir).joinpath('Download')))

##############################################################################################################################

# Where to store custom signals
class CustomSignals_Updater(QObject):
    '''
    Set up signals for updater
    '''
    Signal_ExecuteTask = Signal(tuple)

    Signal_Message = Signal(str)

    Signal_IsUpdateSucceeded = Signal(bool, str)

    Signal_ReadyToUpdate = Signal(str)


UpdaterSignals = CustomSignals_Updater()


def RebootIfFailed():
    BootWithBat(
        ProgramPath = ExecuterPath,
        DelayTime = 0,
        BatFilePath = Path(NormPath(TargetDir)).joinpath('Booter.bat')
    )


def RebootIfSucceeded():
    RunBat(
        CommandList = [
            '@echo off',
            'echo Ready to move files and reboot',
            #f'taskkill /pid {os.getpid()} /f /t',
            'timeout /t 2 /nobreak',
            'echo Moving files...',
            f'robocopy "{ExtractDir}" "{TargetDir}" /E /MOVE /R:3 /W:1 /NP',
            f'start "Programm Running" "{ExecuterPath}"',
            'del "%~f0"'
        ],
        BatFilePath = NormPath(Path(TargetDir).joinpath('Updater.bat'))
    )


def UpdateChecker(
    CurrentVersion: str = ...,
):
    '''
    '''
    try:
        UpdaterSignals.Signal_Message.emit("正在检查更新，请稍等...\nChecking for updates, please wait...")
        IsUpdateNeeded, DownloadURL = CheckUpdate(
            RepoOwner = 'Spr-Aachen',
            RepoName = 'Easy-Voice-Toolkit',
            FileName = 'EVT',
            FileFormat = 'zip',
            Version_Current = CurrentVersion
        )

    except:
        #UpdaterSignals.Signal_Message.emit("更新检查失败！\nFailed to check for updates!")
        UpdaterSignals.Signal_IsUpdateSucceeded.emit(False, "更新检查失败！\nFailed to check for updates!")

    else:
        if IsUpdateNeeded:
            UpdaterSignals.Signal_ReadyToUpdate.emit(DownloadURL)
        else:
            UpdaterSignals.Signal_Message.emit("已是最新版本！\nAlready up to date!")
            UpdaterSignals.Signal_IsUpdateSucceeded.emit(False, "")


def UpdateDownloader(
    DownloadURL: str = ...,
    DownloadDir: str = ...,
    Name: str = ...,
    ExtractDir: str = ...,
    TargetDir: str = ...,
    #ExecuterPath: str = ...
):
    try:
        # Download
        UpdaterSignals.Signal_Message.emit("正在下载文件...\nDownloading files...")
        FileInfo = DownloadFile(
            DownloadURL = DownloadURL,
            DownloadDir = DownloadDir,
            FileName = Name,
            FileFormat = 'zip',
            SHA_Expected = None
        )
    except Exception as e:
        #UpdaterSignals.Signal_Message.emit("文件下载失败！\nFailed to download files!")
        UpdaterSignals.Signal_IsUpdateSucceeded.emit(False, "文件下载失败！\nFailed to download files!")
    else:
        # Unpack
        UpdaterSignals.Signal_Message.emit("正在解压文件...\nUnpacking files...")
        ExtractDir = NormPath(Path(TargetDir).joinpath('Temp')) if ExtractDir == TargetDir else ExtractDir
        shutil.unpack_archive(
            filename = FileInfo[1],
            extract_dir = ExtractDir
        )
        os.remove(FileInfo[1])
        # Cover old files (About to finish)
        UpdaterSignals.Signal_Message.emit("即将重启客户端...\nRebooting client...")
        '''
        CleanDirectory(
            Directory = TargetDir,
            WhiteList = [os.path.basename(ExtractDir), '__pycache__', '.git'].extend(FoldersToKeep)
        )
        shutil.copytree(ExtractDir, TargetDir, dirs_exist_ok = True)
        shutil.rmtree(ExtractDir)
        '''
        UpdaterSignals.Signal_IsUpdateSucceeded.emit(True, "")


class Execute_Update_Checking(QObject):
    '''
    '''
    finished = Signal()

    def __init__(self):
        super().__init__()

    def Execute(self):
        UpdateChecker(
            CurrentVersion = CurrentVersion
        )

        self.finished.emit()


class Execute_Update_Downloading(QObject):
    '''
    '''
    finished = Signal()

    def __init__(self):
        super().__init__()

    def Execute(self, DownloadURL):
        UpdateDownloader(
            DownloadURL = DownloadURL,
            DownloadDir = DownloadDir,
            Name = "EVT Update",
            ExtractDir = ExtractDir,
            TargetDir = TargetDir
        )

        self.finished.emit()


# Show GUI
class Widget_Updater(QWidget):
    '''
    '''
    def __init__(self):
        super().__init__(
            parent = None,
            f = Qt.Widget #| Qt.FramelessWindowHint
        )

        self.setMaximumSize(246, 123)
        self.setGeometry(
            QApplication.primaryScreen().size().width() // 2 - self.width() // 2,
            QApplication.primaryScreen().size().height() // 2 - self.height() // 2,
            self.width(),
            self.height()
        )

        self.setWindowIcon(QIcon(NormPath(Path(ResourceDir).joinpath('Icon.ico'))))

        self.Label = QLabel()
        self.Label.setVisible(True)
        self.Label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        #self.Label.setStyleSheet("text-align: center; font-size: 11.1px;")
        self.Label.clear()

        self.ProgressBar = QProgressBar()
        self.ProgressBar.setVisible(True)
        self.ProgressBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        #self.ProgressBar.setStyleSheet("text-align: center;")

        self.SkipButton = QPushButton()
        self.SkipButton.setVisible(True)
        self.SkipButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.SkipButton.setStyleSheet("text-align: center;")

        self.Layout = QVBoxLayout(self)
        self.Layout.setAlignment(Qt.AlignCenter)
        self.Layout.setContentsMargins(21, 12, 21, 12)
        self.Layout.setSpacing(12)
        self.Layout.addWidget(self.Label)
        self.Layout.addWidget(self.ProgressBar)
        self.Layout.addWidget(self.SkipButton)

    def Function_ExecuteMethod(self,
        ProgressBar: Optional[QProgressBar] = None,
        Method: object = ...,
        Params: Optional[tuple] = ()
    ):
        ClassName =  str(Method.__qualname__).split('.')[0]
        MethodName = str(Method.__qualname__).split('.')[1]

        ClassInstance = globals()[ClassName]()

        WorkerThread = QThread()
        ClassInstance.moveToThread(WorkerThread)
        ClassInstance.finished.connect(WorkerThread.quit)

        def ExecuteMethod():
            Args = Params

            QFunctionsSignals = CustomSignals_Updater()
            QFunctionsSignals.Signal_ExecuteTask.connect(getattr(ClassInstance, MethodName))

            WorkerThread.started.connect(lambda: Function_AnimateProgressBar(ProgressBar, IsTaskAlive = True)) if ProgressBar else None
            WorkerThread.finished.connect(lambda: Function_AnimateProgressBar(ProgressBar, IsTaskAlive = False)) if ProgressBar else None

            QFunctionsSignals.Signal_ExecuteTask.emit(Args)
            WorkerThread.start()

        TempButton = QPushButton(self)
        TempButton.hide()
        TempButton.clicked.connect(ExecuteMethod)
        TempButton.click()

    def Main(self):
        self.DownloadURL = str()
        def UpdateDownloadURL(DownloadURL):
            self.DownloadURL = DownloadURL

        UpdaterSignals.Signal_Message.connect(
            lambda Message: Function_SetText(
                self.Label,
                SetRichText(Message, 'center', 9, 420, 0.3, 12)
            )
        )
        UpdaterSignals.Signal_ReadyToUpdate.connect(
            lambda DownloadURL: (
                UpdateDownloadURL(DownloadURL),
                Function_ShowMessageBox(
                    MessageType = QMessageBox.Question,
                    WindowTitle = 'Ask',
                    Text = '检测到可用的新版本，是否更新？\nNew version available, wanna update?',
                    Buttons = QMessageBox.Yes|QMessageBox.No,
                    ButtonEvents = {
                        QMessageBox.Yes: lambda: self.Function_ExecuteMethod(
                            ProgressBar = self.ProgressBar,
                            Method = Execute_Update_Downloading.Execute,
                            Params = (self.DownloadURL)
                        ),
                        QMessageBox.No: lambda: UpdaterSignals.Signal_IsUpdateSucceeded.emit(False, "已取消下载更新！\nDownload canceled!")
                    }
                )
            )
        )
        UpdaterSignals.Signal_IsUpdateSucceeded.connect(
            lambda Succeeded, Info: (
                Config.EditConfig('Updater', 'Status', 'Executed'),
                Function_ShowMessageBox(
                    MessageType = QMessageBox.Warning,
                    WindowTitle = 'Warning',
                    Text = Info
                ) if not Succeeded and len(Info) > 0 else None,
                RebootIfSucceeded() if Succeeded else RebootIfFailed(),
                QApplication.exit(),
                os._exit(0)
            )
        )

        self.Function_ExecuteMethod(
            ProgressBar = self.ProgressBar,
            Method = Execute_Update_Checking.Execute,
            Params = ()
        )

        self.SkipButton.setText("跳过")
        self.SkipButton.clicked.connect(
            lambda: UpdaterSignals.Signal_IsUpdateSucceeded.emit(False, "")
        )

        self.show()

##############################################################################################################################

if __name__ == "__main__":
    App = QApplication(sys.argv) #App = QApplication([])

    UpdaterWidget = Widget_Updater()
    UpdaterWidget.Main() #UpdaterWidget.show()

    sys.exit(App.exec()) #App.exec()

##############################################################################################################################