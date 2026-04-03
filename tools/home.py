"""
CyberArmor – Home Dashboard
Real-time system monitor with live graphs.
"""

import shutil
from collections import deque

import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker


# ──────────────────────────────────────────────
# STAT CARD
# ──────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, title, icon, accent="#00BCD4"):
        super().__init__()
        self.accent = accent

        self.setFixedHeight(110)
        self.setStyleSheet(f"""
        QFrame {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #111827, stop:1 #0f172a);
            border-radius: 14px;
            border: 1px solid #1e293b;
        }}
        QFrame:hover {{ border: 1px solid {accent}; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        icon_lbl.setStyleSheet(f"""
        QLabel {{
            background: rgba({self._rgb(accent)}, 0.15);
            border-radius: 24px;
        }}
        """)
        layout.addWidget(icon_lbl)

        col = QVBoxLayout()
        col.setSpacing(2)
        self.value_lbl = QLabel("—")
        self.value_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.value_lbl.setStyleSheet(f"color: {accent}; background: transparent;")

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")

        col.addWidget(self.value_lbl)
        col.addWidget(title_lbl)
        layout.addLayout(col)
        layout.addStretch()

    def set_value(self, text):
        self.value_lbl.setText(str(text))

    def _rgb(self, hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"


# ──────────────────────────────────────────────
# LIVE GRAPH CANVAS
# ──────────────────────────────────────────────

BG = "#0a0f1e"
GRID = "#1e293b"
COLORS = {
    "CPU":  "#00BCD4",
    "RAM":  "#8b5cf6",
    "Disk": "#f59e0b",
    "Net":  "#10b981",
}


class LiveGraph(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(facecolor=BG, figsize=(10, 3.5))
        self.ax  = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self.fig.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.12)

        # Style axes
        self.ax.set_facecolor(BG)
        self.ax.tick_params(colors="#64748b", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(GRID)
        self.ax.set_ylim(0, 105)
        self.ax.set_xlim(0, 59)
        self.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d%%'))
        self.ax.grid(color=GRID, linewidth=0.5, alpha=0.6)
        self.ax.set_title("Real-Time System Monitor", color="#94a3b8",
                          fontsize=11, pad=8)

    def update_plot(self, cpu, ram, disk, net):
        self.ax.clear()
        self.ax.set_facecolor(BG)
        self.ax.set_ylim(0, 105)
        self.ax.set_xlim(0, len(cpu) - 1)
        self.ax.tick_params(colors="#64748b", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(GRID)
        self.ax.grid(color=GRID, linewidth=0.5, alpha=0.6)
        self.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d%%'))
        self.ax.set_title("Real-Time System Monitor", color="#94a3b8",
                          fontsize=11, pad=8)

        x = list(range(len(cpu)))

        self.ax.plot(x, list(cpu),  color=COLORS["CPU"],  linewidth=2,
                     label="CPU",  alpha=0.9)
        self.ax.fill_between(x, list(cpu),  alpha=0.08, color=COLORS["CPU"])

        self.ax.plot(x, list(ram),  color=COLORS["RAM"],  linewidth=2,
                     label="RAM",  alpha=0.9)
        self.ax.fill_between(x, list(ram),  alpha=0.08, color=COLORS["RAM"])

        self.ax.plot(x, list(disk), color=COLORS["Disk"], linewidth=2,
                     label="Disk", alpha=0.9)
        self.ax.fill_between(x, list(disk), alpha=0.08, color=COLORS["Disk"])

        net_scaled = [min(v, 100) for v in net]
        self.ax.plot(x, net_scaled,  color=COLORS["Net"],  linewidth=2,
                     label="Net",  alpha=0.9)
        self.ax.fill_between(x, net_scaled,  alpha=0.08, color=COLORS["Net"])

        legend = self.ax.legend(
            loc="upper right",
            facecolor="#111827",
            edgecolor=GRID,
            labelcolor="#94a3b8",
            fontsize=9,
            framealpha=0.9
        )

        self.draw_idle()


# ──────────────────────────────────────────────
# INFO BADGE
# ──────────────────────────────────────────────

class InfoBadge(QFrame):
    def __init__(self, label, value="—", accent="#00BCD4"):
        super().__init__()
        self.setStyleSheet(f"""
        QFrame {{
            background: rgba({self._rgb(accent)}, 0.08);
            border-radius: 10px;
            border: 1px solid rgba({self._rgb(accent)}, 0.2);
        }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)

        self.lbl = QLabel(f"{label}:  ")
        self.lbl.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")

        self.val = QLabel(str(value))
        self.val.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 12px; background: transparent;")

        layout.addWidget(self.lbl)
        layout.addWidget(self.val)
        layout.addStretch()

    def update(self, value):
        self.val.setText(str(value))

    def _rgb(self, h):
        h = h.lstrip("#")
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ──────────────────────────────────────────────
# HOME WIDGET
# ──────────────────────────────────────────────

class HomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QWidget { background: #0a0f1e; color: #e2e8f0; font-family: 'Segoe UI'; }")

        self.N = 60   # data points
        self.cpu_data  = deque([0.0] * self.N, maxlen=self.N)
        self.ram_data  = deque([0.0] * self.N, maxlen=self.N)
        self.disk_data = deque([0.0] * self.N, maxlen=self.N)
        self.net_data  = deque([0.0] * self.N, maxlen=self.N)
        self._last_net = psutil.net_io_counters()

        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    # ── UI ───────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🛡  System Monitor")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("background: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()

        # Live indicator
        live = QLabel("● LIVE")
        live.setStyleSheet("color: #10b981; font-size: 12px; font-weight: bold; background: transparent;")
        hdr.addWidget(live)
        root.addLayout(hdr)

        # Stat cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.cpu_card  = StatCard("CPU Usage",   "🖥",  "#00BCD4")
        self.ram_card  = StatCard("RAM Usage",   "🧠",  "#8b5cf6")
        self.disk_card = StatCard("Disk Usage",  "💾",  "#f59e0b")
        self.net_card  = StatCard("Network KB/s","📶",  "#10b981")

        for card in [self.cpu_card, self.ram_card, self.disk_card, self.net_card]:
            cards_row.addWidget(card)

        root.addLayout(cards_row)

        # Graph
        graph_frame = QFrame()
        graph_frame.setStyleSheet("""
        QFrame {
            background: #0a0f1e;
            border-radius: 14px;
            border: 1px solid #1e293b;
        }
        """)
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(8, 8, 8, 8)

        self.canvas = LiveGraph(self)
        graph_layout.addWidget(self.canvas)
        root.addWidget(graph_frame)

        # Extra info row
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        self.badge_cpu_count = InfoBadge("CPU Cores",   str(psutil.cpu_count()), "#00BCD4")
        self.badge_ram_total = InfoBadge("RAM Total",   self._fmt_bytes(psutil.virtual_memory().total), "#8b5cf6")
        self.badge_disk_free = InfoBadge("Disk Free",   "—", "#f59e0b")
        self.badge_net_sent  = InfoBadge("Net Sent",    "—", "#10b981")
        self.badge_net_recv  = InfoBadge("Net Received","—", "#10b981")

        for badge in [self.badge_cpu_count, self.badge_ram_total,
                      self.badge_disk_free, self.badge_net_sent, self.badge_net_recv]:
            info_row.addWidget(badge)

        root.addLayout(info_row)

    # ── TICK ─────────────────────────────────

    def _tick(self):
        try:
            # CPU
            cpu = psutil.cpu_percent(interval=None)

            # RAM
            ram = psutil.virtual_memory()
            ram_pct = ram.percent

            # Disk
            disk = shutil.disk_usage("/")
            disk_pct = (disk.used / disk.total) * 100

            # Network
            net = psutil.net_io_counters()
            sent_diff = net.bytes_sent - self._last_net.bytes_sent
            recv_diff = net.bytes_recv - self._last_net.bytes_recv
            total_kb  = (sent_diff + recv_diff) / 1024
            self._last_net = net

            # Append
            self.cpu_data.append(cpu)
            self.ram_data.append(ram_pct)
            self.disk_data.append(disk_pct)
            self.net_data.append(min(total_kb, 100))   # cap at 100 for graph scale

            # Update cards
            self.cpu_card.set_value(f"{cpu:.1f}%")
            self.ram_card.set_value(f"{ram_pct:.1f}%")
            self.disk_card.set_value(f"{disk_pct:.1f}%")
            self.net_card.set_value(f"{total_kb:.1f} KB/s")

            # Update badges
            self.badge_disk_free.update(self._fmt_bytes(disk.free))
            self.badge_net_sent.update(self._fmt_bytes(net.bytes_sent))
            self.badge_net_recv.update(self._fmt_bytes(net.bytes_recv))

            # Redraw graph
            self.canvas.update_plot(
                self.cpu_data,
                self.ram_data,
                self.disk_data,
                self.net_data,
            )

        except Exception as e:
            print("HomeWidget tick error:", e)

    # ── HELPERS ──────────────────────────────

    @staticmethod
    def _fmt_bytes(n):
        if n < 1024:
            return f"{n} B"
        elif n < 1024 ** 2:
            return f"{n/1024:.1f} KB"
        elif n < 1024 ** 3:
            return f"{n/1024**2:.1f} MB"
        else:
            return f"{n/1024**3:.2f} GB"

    def closeEvent(self, event):
        try:
            self.timer.stop()
        except Exception:
            pass
        event.accept()
