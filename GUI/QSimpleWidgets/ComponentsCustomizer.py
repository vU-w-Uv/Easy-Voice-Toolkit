from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import *

from .QFunctions import *

##############################################################################################################################

class ToolButtonBase(QToolButton):
    '''
    '''
    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(parent)

        self.setStyleSheet(Function_GetStyleSheet('Button'))
        ComponentsSignals.Signal_SetTheme.connect(
            lambda Theme: self.setStyleSheet(Function_GetStyleSheet('Button', Theme))
        )

        self.setFont('Microsoft YaHei')
        self.setText(text)
    '''
        self.setIconSize(QSize(16, 16))
        self.setIcon(QIcon())

        self.isPressed = False
        self.isHover = False

    def setProperty(self, name: str, value) -> bool:
        if name != 'icon':
            return super().setProperty(name, value)

        self.setIcon(value)
        return True

    def setIcon(self, icon: Union[QIcon, str]):
        self.setProperty('hasIcon', icon is not None)
        self.setStyle(QApplication.style())
        self._icon = icon or QIcon()
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._icon is None:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.43)
        elif self.isPressed:
            painter.setOpacity(0.63)

        w, h = self.iconSize().width(), self.iconSize().height()
        y = (self.height() - h) / 2
        x = (self.width() - w) / 2
        Function_DrawIcon(self._icon, painter, QRectF(x, y, w, h))

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()
    '''

class ToolButton_UnderLined(ToolButtonBase):
    '''
    Check its stylesheet in qss file
    '''

##############################################################################################################################

class TableWidgetBase(QTableWidget):
    '''
    '''
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.setStyleSheet(Function_GetStyleSheet('Table'))
        ComponentsSignals.Signal_SetTheme.connect(
            lambda Theme: self.setStyleSheet(Function_GetStyleSheet('Table', Theme))
        )

        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.RowHeight = self.horizontalHeader().height()

        self.SetIndexHeader()
        self.IsIndexShown = False
        self.SetIndexHeaderVisible(True)

    def SetIndexHeader(self):
        self.verticalHeader().setVisible(False)
        #self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.insertColumn(0)
        self.setHorizontalHeaderItem(0, QTableWidgetItem('Index'))
        #self.setColumnWidth(0, self.RowHeight * 1.5)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) #self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        def SetIndex():
            for Index in range(self.rowCount()):
                self.setItem(Index, 0, QTableWidgetItem(f"{Index + 1}"))
        self.model().rowsInserted.connect(SetIndex)
        self.model().rowsRemoved.connect(SetIndex)

    def SetIndexHeaderVisible(self, ShowIndexHeader: bool = True):
        if ShowIndexHeader and not self.IsIndexShown:
            self.showColumn(0)
            self.IsIndexShown = True

        if not ShowIndexHeader and self.IsIndexShown:
            self.hideColumn(0)
            self.IsIndexShown = False

##############################################################################################################################