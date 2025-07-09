import json, os
from contract_model import Contract

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CONTRACTS_PATH = os.path.join(DATA_DIR, 'contracts.json')

class ContractManager :
    def __init__(self) :
        self.contracts = []

    def add_contract(self, contract) :
        self.contracts.append(contract)

    def remove_contract(self, name) :
        self.contracts = [c for c in self.contracts if c.name != name]

    def get_contract(self, name) :
        return next((c for c in self.contracts if c.name == name), None)
    
    def get_all_summaries(self) :
        return [c.summary() for c in self.contracts]

    def total_expected_profit(self) :
        return sum(c.total_interest() for c in self.contracts)

    def active_contracts(self, today=None) :
        return [c for c in self.contracts if c.is_active(today)]
    
    def to_dict_list(self) :
        return [c.to_dict() for c in self.contracts]
    
    def from_dict_list(self, dict_list) :
        self.contracts = [Contract.from_dict(d) for d in dict_list]
    
    def save_to_file(self, filepath=CONTRACTS_PATH) :
        with open(filepath, "w", encoding="utf-8") as f :
            json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath=CONTRACTS_PATH) :
        try :
            with open(filepath, "r", encoding="utf-8") as f :
                data = json.load(f)
                self.from_dict_list(data)
        except FileNotFoundError :
            self.contracts = []