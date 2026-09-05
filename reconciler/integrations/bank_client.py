from typing import List, Dict, Any
from .base import DataProvider
import time

class BankProvider(DataProvider):
    """Mock integration for a generic Bank API (e.g. Plaid/HDFC)."""
    def __init__(self, account_id: str):
        self.account_id = account_id
        
    def fetch_transactions(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # In a real scenario, we would use an SDK like Plaid here.
        # Simulating API latency
        time.sleep(1)
        return []

