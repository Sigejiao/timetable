from PyQt5.QtWidgets import QApplication
from clock_widget import ClockWindow
import sys

if __name__ == "__main__":  # 程序入口点，确保代码只在直接运行时执行
    app = QApplication(sys.argv)  # 创建PyQt5应用程序实例，传入命令行参数
    window = ClockWindow()  # 创建时钟窗口实例
    window.show()  # 显示时钟窗口
    sys.exit(app.exec_())  # 启动应用程序事件循环，并在退出时返回状态码