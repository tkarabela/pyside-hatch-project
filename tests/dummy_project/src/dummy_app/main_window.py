from PySide6.QtCore import QObject


class MainWindow(QObject):
    def window_title(self) -> str:
        return self.tr("Window title from Python")
