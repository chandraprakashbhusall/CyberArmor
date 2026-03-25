from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import db


# ==========================
# ADMIN PANEL WIDGET
# ==========================

class AdminPanelWidget(QWidget):

    logoutSignal = pyqtSignal()

    def __init__(self):

        super().__init__()

        self.setStyleSheet(self.style())

        self.build_ui()

        self.load_dashboard()


# ==========================
# UI
# ==========================

    def build_ui(self):

        mainLayout=QHBoxLayout(self)



# SIDEBAR

        sidebar=QVBoxLayout()

        title=QLabel("ADMIN PANEL")
        title.setFont(QFont("Arial",18,QFont.Bold))

        sidebar.addWidget(title)


        self.dashboardBtn=QPushButton("Dashboard")
        self.usersBtn=QPushButton("Users")
        self.statsBtn=QPushButton("Statistics")
        self.logoutBtn=QPushButton("Logout")


        sidebar.addWidget(self.dashboardBtn)
        sidebar.addWidget(self.usersBtn)
        sidebar.addWidget(self.statsBtn)

        sidebar.addStretch()

        sidebar.addWidget(self.logoutBtn)



# STACK

        self.stack=QStackedWidget()

        self.dashboardPage=QWidget()
        self.usersPage=QWidget()
        self.statsPage=QWidget()

        self.stack.addWidget(self.dashboardPage)
        self.stack.addWidget(self.usersPage)
        self.stack.addWidget(self.statsPage)



        mainLayout.addLayout(sidebar,1)
        mainLayout.addWidget(self.stack,4)



# BUTTONS

        self.dashboardBtn.clicked.connect(
            lambda:self.stack.setCurrentWidget(self.dashboardPage))

        self.usersBtn.clicked.connect(
            lambda:self.stack.setCurrentWidget(self.usersPage))

        self.statsBtn.clicked.connect(
            lambda:self.stack.setCurrentWidget(self.statsPage))

        self.logoutBtn.clicked.connect(self.logoutSignal.emit)



# BUILD PAGES

        self.build_dashboard()

        self.build_users()

        self.build_stats()



# ==========================
# DASHBOARD
# ==========================

    def build_dashboard(self):

        layout=QVBoxLayout(self.dashboardPage)

        title=QLabel("CyberArmor Dashboard")

        title.setFont(QFont("Arial",22))

        layout.addWidget(title)



# CARDS

        cards=QHBoxLayout()

        self.usersCard=self.card("Users")
        self.toolsCard=self.card("Tools")
        self.scansCard=self.card("Scans")

        cards.addWidget(self.usersCard)
        cards.addWidget(self.toolsCard)
        cards.addWidget(self.scansCard)

        layout.addLayout(cards)



        self.dashboardText=QTextEdit()
        self.dashboardText.setReadOnly(True)

        layout.addWidget(self.dashboardText)



# ==========================
# USERS PAGE
# ==========================

    def build_users(self):

        layout=QVBoxLayout(self.usersPage)


        title=QLabel("Users")

        title.setFont(QFont("Arial",20))

        layout.addWidget(title)



# SEARCH

        self.searchBox=QLineEdit()

        self.searchBox.setPlaceholderText("Search user...")

        layout.addWidget(self.searchBox)

        self.searchBox.textChanged.connect(self.search_users)



# TABLE

        self.userTable=QTableWidget()

        self.userTable.setColumnCount(4)

        self.userTable.setHorizontalHeaderLabels(

            ["Select","Username","Email","Date"]

        )

        self.userTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.userTable.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.userTable)



# DELETE BUTTON

        deleteBtn=QPushButton("Delete Selected Users")

        deleteBtn.clicked.connect(self.delete_users)

        layout.addWidget(deleteBtn)



# ==========================
# STATISTICS PAGE
# ==========================

    def build_stats(self):

        layout=QVBoxLayout(self.statsPage)


        title=QLabel("Statistics")

        title.setFont(QFont("Arial",20))

        layout.addWidget(title)



        self.statsBox=QTextEdit()

        self.statsBox.setReadOnly(True)

        layout.addWidget(self.statsBox)



# ==========================
# CARD
# ==========================

    def card(self,title):

        box=QLabel("0")

        box.setAlignment(Qt.AlignCenter)

        box.setFont(QFont("Arial",18))

        return box



# ==========================
# LOAD DASHBOARD
# ==========================

    def load_dashboard(self):

        self.usersCard.setText(str(db.total_users()))

        self.toolsCard.setText(str(db.total_tools()))

        self.scansCard.setText(str(db.total_scans()))


        stats=db.tool_stats()

        text="Tool Usage\n\n"

        for tool,count in stats.items():

            text+=f"{tool} : {count}\n"


        self.dashboardText.setText(text)


        self.load_users()

        self.load_stats()



# ==========================
# LOAD USERS
# ==========================

    def load_users(self):

        users=db.get_all_users()

        self.userTable.setRowCount(len(users))


        for row,u in enumerate(users):

            check=QCheckBox()

            self.userTable.setCellWidget(row,0,check)

            self.userTable.setItem(row,1,QTableWidgetItem(u[0]))

            self.userTable.setItem(row,2,QTableWidgetItem(u[1]))

            self.userTable.setItem(row,3,QTableWidgetItem(u[2]))



# ==========================
# SEARCH USERS
# ==========================

    def search_users(self):

        text=self.searchBox.text()

        users=db.search_users(text)

        self.userTable.setRowCount(len(users))


        for row,u in enumerate(users):

            check=QCheckBox()

            self.userTable.setCellWidget(row,0,check)

            self.userTable.setItem(row,1,QTableWidgetItem(u[0]))

            self.userTable.setItem(row,2,QTableWidgetItem(u[1]))

            self.userTable.setItem(row,3,QTableWidgetItem(u[2]))



# ==========================
# DELETE USERS
# ==========================

    def delete_users(self):

        rows=self.userTable.rowCount()

        deleted=0

        for r in range(rows):

            check=self.userTable.cellWidget(r,0)

            if check.isChecked():

                email=self.userTable.item(r,2).text()

                db.delete_user(email)

                deleted+=1


        QMessageBox.information(self,"Done",f"{deleted} users deleted")

        self.load_dashboard()



# ==========================
# LOAD STATS
# ==========================

    def load_stats(self):

        stats=db.tool_stats()

        text="Tool Statistics\n\n"

        for tool,count in stats.items():

            text+=f"{tool} used {count} times\n"


        scans=db.scans_per_user()

        text+="\nScans Per User\n\n"

        for u,c in scans:

            text+=f"{u} : {c}\n"


        self.statsBox.setText(text)



# ==========================
# STYLE
# ==========================

    def style(self):

        return """

        QWidget{

        background:#0d1117;

        color:white;

        font-size:14px;

        }


        QPushButton{

        background:#161b22;

        padding:10px;

        border-radius:6px;

        }


        QPushButton:hover{

        background:#238636;

        }


        QLineEdit{

        padding:8px;

        border-radius:6px;

        }


        QTableWidget{

        background:#161b22;

        }


        QTextEdit{

        background:#161b22;

        }

        """