from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class DataCache:
    def __init__(self, cache_dir: Path, expiry_hours: int):
        self.cache_dir = cache_dir
        self.expiry_hours = expiry_hours

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        # Check if cache is expired
        if (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).total_seconds() > self.expiry_hours * 3600:
            cache_path.unlink()
            return None

        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def set(self, key: str, value: Any):
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(value, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}") 