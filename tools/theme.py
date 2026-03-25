from PyQt5.QtWidgets import QApplication

# ===============================
# GLOBAL THEME STATE
# ===============================

current_theme = "dark"

primary_color = "#00BCD4"


# ===============================
# DARK THEME
# ===============================

DARK_THEME = """
QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: Segoe UI;
}

QFrame {
    background-color: #111827;
    border-radius: 10px;
}

QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 8px 14px;
    border-radius: 8px;
}

QPushButton:hover {
    background-color: PRIMARY;
    color: black;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 6px;
    border-radius: 6px;
}

QTableWidget {
    background-color: #0f172a;
    gridline-color: #334155;
}

QHeaderView::section {
    background-color: #1e293b;
    padding: 6px;
    border: none;
}
"""


# ===============================
# LIGHT THEME
# ===============================

LIGHT_THEME = """
QWidget {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: Segoe UI;
}

QFrame {
    background-color: white;
    border-radius: 10px;
}

QPushButton {
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    padding: 8px 14px;
    border-radius: 8px;
}

QPushButton:hover {
    background-color: PRIMARY;
    color: white;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: white;
    border: 1px solid #cbd5e1;
    padding: 6px;
    border-radius: 6px;
}

QTableWidget {
    background-color: white;
    gridline-color: #cbd5e1;
}

QHeaderView::section {
    background-color: #e2e8f0;
    padding: 6px;
    border: none;
}
"""


# ===============================
# GET STYLESHEET
# ===============================

def get_stylesheet():

    if current_theme == "dark":
        style = DARK_THEME
    else:
        style = LIGHT_THEME

    return style.replace("PRIMARY", primary_color)



# ===============================
# SET THEME
# ===============================

def set_theme(mode):

    global current_theme

    current_theme = mode

    apply_theme()



# ===============================
# SET ACCENT COLOR
# ===============================

def set_primary_color(color):

    global primary_color

    primary_color = color

    apply_theme()



# ===============================
# APPLY THEME
# ===============================

def apply_theme():

    app = QApplication.instance()

    if app:
        app.setStyleSheet(get_stylesheet())