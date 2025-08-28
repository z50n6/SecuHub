import yaml
import os

class VulnDataManager:
    def __init__(self, file_path='data/vuln_manager.yaml'):
        self.file_path = file_path
        self.vulnerabilities = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('vulnerabilities', []) if data else []

    def _save_data(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            yaml.dump({'vulnerabilities': self.vulnerabilities}, f, allow_unicode=True, sort_keys=False)

    def get_all_vulnerabilities(self):
        return self.vulnerabilities

    def add_vulnerability(self, vuln_data):
        self.vulnerabilities.append(vuln_data)
        self._save_data()

    def update_vulnerability(self, index, new_vuln_data):
        if 0 <= index < len(self.vulnerabilities):
            self.vulnerabilities[index] = new_vuln_data
            self._save_data()
            return True
        return False

    def delete_vulnerability(self, index):
        if 0 <= index < len(self.vulnerabilities):
            del self.vulnerabilities[index]
            self._save_data()
            return True
        return False

    def get_vulnerability_by_index(self, index):
        if 0 <= index < len(self.vulnerabilities):
            return self.vulnerabilities[index]
        return None
