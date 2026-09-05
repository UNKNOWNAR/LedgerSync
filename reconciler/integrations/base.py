from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DataProvider(ABC):
    """Base interface for all external data providers."""
    
    @abstractmethod
    def fetch_transactions(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch transactions from the provider within a date range."""
        pass

