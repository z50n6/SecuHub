import sys
from PyQt6.QtWidgets import QApplication
from .vuln_data_manager import VulnDataManager
from .vuln_ui import VulnManagerUI

def start_vuln_manager():
    # No need for QApplication here as it will be handled by the main app
    data_manager = VulnDataManager()
    ui = VulnManagerUI(data_manager)
    return ui

# Removed the if __name__ == '__main__': block
