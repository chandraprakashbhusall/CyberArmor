import psutil
import shutil
import db
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QScrollArea, QPushButton, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPen
import pyqtgraph as pg
import random

class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color:#0a0a0a; color:white;")
        self.max_points = 50

        # ---------------- Data ----------------
        self.cpu_data = [0]*self.max_points
        self.ram_data = [0]*self.max_points
        self.net_data = [0]*self.max_points
        self.last_net = psutil.net_io_counters()

        # ---------------- Scroll Area ----------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(20,20,20,20)
        self.main_layout.setSpacing(25)

        # ---------------- Title ----------------
        title = QLabel("🛡️ CyberArmor Dashboard")
        title.setFont(QFont("Arial", 30, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title)

        # ---------------- Tool Cards ----------------
        self.add_tool_cards()

        # ---------------- System Health & Threat ----------------
        self.add_health_threat_row()

        # ---------------- System Graphs ----------------
        self.add_system_graphs()

        # ---------------- Live Network Traffic ----------------
        self.add_live_network_monitor()

        # ---------------- Recent Activity ----------------
        self.add_recent_activity_table()

        # ---------------- Timer ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_stats)
        self.timer.start(1000)

        # ---------------- Set Main Layout ----------------
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    # ---------------- Safe DB Count ----------------
    def safe_count(self, func):
        try:
            return func() or 0
        except:
            return 0

    # ---------------- Tool Cards ----------------
    def add_tool_cards(self):
        tools = [
            ("🏠 Home","home"),
            ("🛠 Port Scanner","port"),
            ("📶 WiFi Analyzer","wifi"),
            ("🔗 Link Inspector","link"),
            ("🤖 AI Chat","ai"),
            ("🗂 File Scanner","file"),
            ("💻 System Scan","system")
        ]
        row = QHBoxLayout()
        row.setSpacing(15)
        for name, key in tools:
            btn = self.create_tool_card(name)
            row.addWidget(btn)
        self.main_layout.addLayout(row)

    def create_tool_card(self, name):
        card = QPushButton(name)
        card.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #222, stop:1 #111);
                color: white;
                font-size:16px;
                border-radius:12px;
                padding:25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #444, stop:1 #222);
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.clicked.connect(lambda: print(f"{name} clicked!"))  # placeholder
        return card

    # ---------------- Health + Threat ----------------
    def add_health_threat_row(self):
        row = QHBoxLayout()
        row.setSpacing(20)
        row.addWidget(self.create_health_card())
        row.addWidget(self.create_threat_card())
        self.main_layout.addLayout(row)

    def create_health_card(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#1f1f1f; border-radius:12px; border:1px solid #333; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(10)
        lbl = QLabel("💡 System Health")
        lbl.setFont(QFont("Arial",18,QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        # CPU
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.cpu_bar.setStyleSheet(self.progress_style())
        layout.addWidget(self.cpu_bar)

        # RAM
        self.ram_bar = QProgressBar()
        self.ram_bar.setFormat("RAM: %p%")
        self.ram_bar.setStyleSheet(self.progress_style())
        layout.addWidget(self.ram_bar)

        # Disk
        self.disk_bar = QProgressBar()
        self.disk_bar.setFormat("Disk: %p%")
        self.disk_bar.setStyleSheet(self.progress_style())
        layout.addWidget(self.disk_bar)

        return frame

    def progress_style(self):
        return """
            QProgressBar {
                border: 1px solid #333;
                border-radius: 10px;
                text-align: center;
                color: white;
                background: #111;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00ff99, stop:1 #00cc66);
                border-radius: 10px;
            }
        """

    def create_threat_card(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#1f1f1f; border-radius:12px; border:1px solid #550000; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(10)

        lbl = QLabel("⚠️ Threat Level")
        lbl.setFont(QFont("Arial",18,QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        self.threat_scene = QGraphicsScene()
        self.threat_view = QGraphicsView(self.threat_scene)
        self.threat_view.setFixedSize(180,180)
        self.threat_view.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.threat_view)

        self.update_threat_graph()
        return frame

    def update_threat_graph(self):
        self.threat_scene.clear()
        level = random.randint(0,100)  # replace with real threat calculation
        # outer circle
        circle = QGraphicsEllipseItem(10,10,160,160)
        circle.setPen(QPen(QColor("#555555"),12))
        self.threat_scene.addItem(circle)
        # arc
        arc = QGraphicsEllipseItem(10,10,160,160)
        pen = QPen(QColor(self.threat_color(level)),12)
        pen.setCapStyle(Qt.RoundCap)
        arc.setStartAngle(90*16)
        arc.setSpanAngle(-int(level*360/100*16))
        arc.setPen(pen)
        self.threat_scene.addItem(arc)
        # text
        text = QLabel(f"{level}%")
        text.setStyleSheet("color:white; font-size:20px;")
        proxy = self.threat_scene.addWidget(text)
        proxy.setPos(65,70)

    def threat_color(self, val):
        if val<30: return "green"
        elif val<60: return "yellow"
        elif val<85: return "orange"
        else: return "red"

    # ---------------- System Graphs ----------------
    def add_system_graphs(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#1f1f1f; border-radius:12px; border:1px solid #333; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(10)

        lbl = QLabel("📊 Real-Time System Monitor")
        lbl.setFont(QFont("Arial",18,QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        pg.setConfigOption('background', '#1f1f1f')
        pg.setConfigOption('foreground', 'w')

        # CPU
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_plot.setYRange(0,100)
        self.cpu_curve = self.cpu_plot.plot(self.cpu_data, pen=pg.mkPen('r', width=2))
        layout.addWidget(self.cpu_plot)

        # RAM
        self.ram_plot = pg.PlotWidget(title="RAM Usage (%)")
        self.ram_plot.setYRange(0,100)
        self.ram_curve = self.ram_plot.plot(self.ram_data, pen=pg.mkPen('g', width=2))
        layout.addWidget(self.ram_plot)

        # Network
        self.net_plot = pg.PlotWidget(title="Network KB/s")
        self.net_plot.setYRange(0, max(1,max(self.net_data)+100))
        self.net_curve = self.net_plot.plot(self.net_data, pen=pg.mkPen('c', width=2))
        layout.addWidget(self.net_plot)

        self.main_layout.addWidget(frame)

    # ---------------- Live Network Monitor ----------------
    def add_live_network_monitor(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#1f1f1f; border-radius:12px; border:1px solid #333; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15,15,15,15)
        layout.setSpacing(10)

        lbl = QLabel("🌐 Live Network Traffic")
        lbl.setFont(QFont("Arial",18,QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        self.net_bar = QProgressBar()
        self.net_bar.setFormat("Traffic: %p KB/s")
        self.net_bar.setStyleSheet(self.progress_style())
        layout.addWidget(self.net_bar)

        self.main_layout.addWidget(frame)

    # ---------------- Recent Activity ----------------
    def add_recent_activity_table(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background:#1f1f1f; border-radius:12px; border:1px solid #333; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15,15,15,15)

        lbl = QLabel("📝 Recent Activity")
        lbl.setFont(QFont("Arial",18,QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Type","Details","Time"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("QTableWidget { background:#111; color:white; gridline-color:#333; }")
        rows = db.get_recent_activity() or []
        table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for c,col in enumerate(row):
                table.setItem(r,c,QTableWidgetItem(str(col)))
        layout.addWidget(table)
        self.main_layout.addWidget(frame)

    # ---------------- Update Stats ----------------
    def update_system_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.cpu_data = self.cpu_data[1:] + [cpu]
        self.ram_data = self.ram_data[1:] + [ram]
        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)
        self.cpu_bar.setValue(int(cpu))
        self.ram_bar.setValue(int(ram))

        disk = shutil.disk_usage('/')
        self.disk_bar.setValue(int((disk.used/disk.total)*100))

        net = psutil.net_io_counters()
        sent = net.bytes_sent - self.last_net.bytes_sent
        recv = net.bytes_recv - self.last_net.bytes_recv
        total_speed = (sent+recv)//1024
        self.last_net = net
        self.net_data = self.net_data[1:] + [total_speed]
        self.net_curve.setData(self.net_data)
        self.net_plot.setYRange(0,max(100,max(self.net_data)+50))
        self.net_bar.setValue(int(total_speed))

        self.update_threat_graph()
