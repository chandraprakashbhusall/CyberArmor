import psutil
import shutil
from collections import deque

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ================= GRAPH CANVAS =================

class LiveGraphCanvas(FigureCanvas):

    def __init__(self, parent=None):

        self.fig = Figure(facecolor="#0f172a")
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)

        self.setParent(parent)

        self.ax.set_facecolor("#0f172a")
        self.ax.tick_params(colors="white")

        for spine in self.ax.spines.values():
            spine.set_color("white")


# ================= STAT CARD =================

class StatCard(QFrame):

    def __init__(self, title):

        super().__init__()

        self.setStyleSheet("""
        QFrame{
            background:#111827;
            border-radius:12px;
            padding:15px;
        }
        """)

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setStyleSheet("font-size:14px;color:#94a3b8")

        self.value = QLabel("0")
        self.value.setFont(QFont("Segoe UI",20,QFont.Bold))

        layout.addWidget(self.title)
        layout.addWidget(self.value)



# ================= HOME =================

class HomeWidget(QWidget):

    def __init__(self,parent=None):

        super().__init__(parent)

        self.setStyleSheet("""
        QWidget{
            background:#0f172a;
            color:white;
            font-family:Segoe UI;
        }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(30,30,30,30)
        main.setSpacing(20)


        # ================= TITLE =================

        title = QLabel("🛡 CyberArmor Dashboard")
        title.setFont(QFont("Segoe UI",26,QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        main.addWidget(title)



        # ================= STAT CARDS =================

        cards = QHBoxLayout()

        self.cpu_card = StatCard("CPU Usage")
        self.ram_card = StatCard("RAM Usage")
        self.disk_card = StatCard("Disk Usage")
        self.net_card = StatCard("Network KB/s")

        cards.addWidget(self.cpu_card)
        cards.addWidget(self.ram_card)
        cards.addWidget(self.disk_card)
        cards.addWidget(self.net_card)

        main.addLayout(cards)



        # ================= GRAPH =================

        self.canvas = LiveGraphCanvas(self)

        main.addWidget(self.canvas)



        # ================= DATA =================

        self.max_points = 40

        self.cpu_data = deque([0]*self.max_points,maxlen=self.max_points)
        self.ram_data = deque([0]*self.max_points,maxlen=self.max_points)
        self.disk_data = deque([0]*self.max_points,maxlen=self.max_points)
        self.net_data = deque([0]*self.max_points,maxlen=self.max_points)

        self.last_net = psutil.net_io_counters()



        # ================= TIMER =================

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)



    # ================= UPDATE GRAPH =================

    def update_graph(self):

        try:

            cpu = psutil.cpu_percent()

            ram = psutil.virtual_memory().percent

            disk = shutil.disk_usage('/')
            disk_percent = (disk.used/disk.total)*100


            net = psutil.net_io_counters()

            speed = (
                net.bytes_sent-self.last_net.bytes_sent +
                net.bytes_recv-self.last_net.bytes_recv
            )/1024

            self.last_net = net



            # Store data

            self.cpu_data.append(cpu)
            self.ram_data.append(ram)
            self.disk_data.append(disk_percent)
            self.net_data.append(speed)



            # Update cards

            self.cpu_card.value.setText(f"{cpu}%")

            self.ram_card.value.setText(f"{ram}%")

            self.disk_card.value.setText(f"{round(disk_percent,1)}%")

            self.net_card.value.setText(f"{round(speed,1)}")



            # Draw graph

            ax=self.canvas.ax

            ax.clear()

            ax.plot(self.cpu_data,label="CPU %",linewidth=2)

            ax.plot(self.ram_data,label="RAM %",linewidth=2)

            ax.plot(self.disk_data,label="Disk %",linewidth=2)

            ax.plot(self.net_data,label="Network",linewidth=2)



            ax.set_ylim(0,100)

            ax.legend()

            ax.grid(alpha=0.3)

            ax.set_title("Real-Time System Monitor",color="white")

            self.canvas.draw_idle()


        except Exception as e:
            print("Graph Error:",e)



    # ================= CLOSE =================

    def closeEvent(self,event):

        try:
            self.timer.stop()
        except:
            pass

        event.accept()