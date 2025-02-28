import sys
import json
import requests
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QComboBox, QTextEdit, QLineEdit
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import Qt

# GitHub Raw JSON URL
JSON_URL = "https://raw.githubusercontent.com/OWASP/wstg/master/checklists/checklist.json"

def fetch_checklist():
    response = requests.get(JSON_URL)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_reference_details(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "Failed to fetch reference."
        
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("div", id="main")
        if not main_content:
            return "Main content not found."
        
        content = ""
        capture = False
        
        for element in main_content.find_all(['h2', 'p', 'ul', 'li', 'pre', 'code', 'br']):
            if element.name == 'h2':
                if 'summary' in element.get('id', '').lower():
                    capture = True
                    content += f"\n\n📌 <b>{element.get_text(strip=True)}</b><br>\n"
                elif 'how-to' in element.get('id', '').lower():
                    content += f"\n\n<br><br>🔍 <b>{element.get_text(strip=True)}</b><br><br>\n"
                elif 'tools' in element.get('id', '').lower():
                    content += f"\n\n<br><br>🛠 <b>{element.get_text(strip=True)}</b><br>\n"
                elif 'test objectives' in element.get('id', '').lower():
                    content += f"\n\n<br><br>🎯 <b>{element.get_text(strip=True)}</b><br>\n"
                elif 'remediation' in element.get('id', '').lower():
                    content += f"\n\n<br><br>🛡️ <b>{element.get_text(strip=True)}</b><br>\n"
            elif capture:
                if element.name == 'p':
                    content += f"{element.get_text(' ', strip=True)}<br>\n\n"
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        content += f"- {li.get_text(strip=True)}<br>\n"
                    content += "\n"
                elif element.name == 'pre':
                    code_block = element.get_text(" ", strip=True)  # Use space instead of newlines for code snippets
                    content += f"<pre><code>{code_block}</code></pre>\n\n"
                elif element.name == 'br':
                    content += "\n"
                elif element.name[0] == 'h' and element.name != "h2":
                    content += f"\n\n📌 <b>{element.get_text(strip=True)}</b><br>\n"
        
        return content.strip()
    except Exception as e:
        return f"Error fetching reference: {str(e)}"

class OWASPChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 OWASP WSTG Checklist Browser by ibarkay")
        self.setGeometry(100, 100, 900, 800)
        
        self.data = fetch_checklist()
        self.categories = sorted(self.data["categories"].keys())  # Extract categories
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Search Bar
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("🔍 Search checklists...")
        self.searchBar.textChanged.connect(self.updateChecklist)
        layout.addWidget(self.searchBar)
        
        # Category Dropdown
        self.categoryDropdown = QComboBox()
        self.categoryDropdown.addItem("📂 All Categories")
        self.categoryDropdown.addItems(self.categories)
        self.categoryDropdown.currentTextChanged.connect(self.updateChecklist)
        layout.addWidget(self.categoryDropdown)
        
        # Main Layout
        mainLayout = QHBoxLayout()
        
        # Checklist Items Box
        self.checklistBox = QListWidget()
        self.checklistBox.itemClicked.connect(self.displayDetails)
        self.checklistBox.currentRowChanged.connect(self.handleArrowKeyNavigation)
        mainLayout.addWidget(self.checklistBox)
        
        # Details Box
        rightLayout = QVBoxLayout()
        
        self.detailsBox = QTextEdit()
        self.detailsBox.setReadOnly(True)
        rightLayout.addWidget(self.detailsBox)
        
        # Reference Details Box
        self.referenceDetailsBox = QTextEdit()
        self.referenceDetailsBox.setReadOnly(True)
        self.referenceDetailsBox.setAcceptRichText(True)
        rightLayout.addWidget(self.referenceDetailsBox)
        
        mainLayout.addLayout(rightLayout)
        
        layout.addLayout(mainLayout)
        self.setLayout(layout)
        
        self.updateChecklist()
    
    def updateChecklist(self):
        selected_category = self.categoryDropdown.currentText()
        search_query = self.searchBar.text().strip().lower()
        self.checklistBox.clear()
        
        for category, details in self.data["categories"].items():
            if selected_category == "📂 All Categories" or category == selected_category:
                for test in details["tests"]:
                    title = f"✅ {test['id']} - {test['name']}"
                    if search_query in test['name'].lower() or search_query in test['id'].lower():
                        self.checklistBox.addItem(title)
    
    def displayDetails(self, item):
        if item:
            self.showDetails(item.text())
    
    def handleArrowKeyNavigation(self, index):
        item = self.checklistBox.item(index)
        if item:
            self.showDetails(item.text())
    
    def showDetails(self, selected_text):
        selected_text = selected_text.split(" - ", 1)[1] if " - " in selected_text else selected_text
        for category, details in self.data["categories"].items():
            for test in details["tests"]:
                if test["name"] == selected_text:
                    self.detailsBox.clear()
                    
                    cursor = self.detailsBox.textCursor()
                    
                    # Set bold format for headlines
                    bold_format = QTextCharFormat()
                    bold_format.setFontWeight(QFont.Weight.Bold)
                    bold_format.setForeground(QColor("pink"))
                    
                    cursor.insertText(f"📌 Category: {category}\n\n", bold_format)
                    cursor.insertText(f"🆔 ID: {test['id']}\n\n", bold_format)
                    
                    # Display objectives
                    if "objectives" in test:
                        cursor.insertText("🎯 Test Objectives:\n", bold_format)
                        for obj in test["objectives"]:
                            cursor.insertText(f"- {obj}\n")
                        cursor.insertText("\n")
                    
                    cursor.insertText("🔗 Reference: ", bold_format)
                    cursor.insertHtml(f'<a href="{test["reference"]}" style="color:pink;">{test["reference"]}</a>')
                    cursor.insertText("\n\n")
                    
                    self.detailsBox.setTextCursor(cursor)
                    
                    reference_text = fetch_reference_details(test.get("reference", ""))
                    self.referenceDetailsBox.setHtml(reference_text)  # Render HTML correctly
                    return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OWASPChecklistApp()
    window.show()
    sys.exit(app.exec())
