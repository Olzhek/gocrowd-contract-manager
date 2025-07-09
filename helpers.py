import holidays
import json
import os
from datetime import date, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CONTRACTS_PATH = os.path.join(DATA_DIR, 'contracts.json')

def get_kz_holidays() :
    return holidays.CountryHoliday("KZ")

def shift_to_working_day(d, holiday_calendar) :
    while d.weekday() >= 5 or d in holiday_calendar :
        d += timedelta(days=1)
    return d

def load_contracts(path=CONTRACTS_PATH) :
    from contract_model import Contract
    if os.path.exists(path) :
        with open(path, "r", encoding="utf-8") as f :
            data = json.load(f)
            return [Contract.from_dict(d) for d in data]
    return []

def save_contracts(contracts, path=CONTRACTS_PATH) :
    with open(path, "w", encoding="utf-8") as f :
        json.dump([c.to_dict() for c in contracts], f, default=str)