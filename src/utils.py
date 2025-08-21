import re
import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class EmailValidator:
    """Email validation utility"""
    
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @classmethod
    def validate(cls, email: str) -> bool:
        """Validate email format"""
        if not isinstance(email, str):
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_strict(cls, email: str) -> str:
        """Validate email and raise exception if invalid"""
        if not cls.validate(email):
            raise ValidationError(f"Invalid email format: {email}")
        return email.lower().strip()

class DataProcessor:
    """Utility class for data processing and calculations"""
    
    @staticmethod
    def calculate_percentage(part: int, total: int) -> float:
        """Calculate percentage with error handling"""
        if total == 0:
            return 0.0
        if part < 0 or total < 0:
            raise ValueError("Values cannot be negative")
        return (part / total) * 100
    
    @staticmethod
    def group_by_key(items: List[Dict], key: str) -> Dict[Any, List[Dict]]:
        """Group list of dictionaries by a key"""
        groups = {}
        for item in items:
            if key not in item:
                raise KeyError(f"Key '{key}' not found in item: {item}")
            
            group_key = item[key]
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
        
        return groups
    
    @staticmethod
    def filter_by_date_range(items: List[Dict], date_field: str, 
                           start_date: Optional[datetime.date] = None,
                           end_date: Optional[datetime.date] = None) -> List[Dict]:
        """Filter items by date range"""
        filtered = []
        
        for item in items:
            if date_field not in item:
                continue
            
            try:
                item_date = datetime.datetime.fromisoformat(item[date_field]).date()
            except (ValueError, TypeError):
                continue
            
            if start_date and item_date < start_date:
                continue
            if end_date and item_date > end_date:
                continue
            
            filtered.append(item)
        
        return filtered

class FileManager:
    """File operations utility"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def read_json(self, filename: str) -> Dict:
        """Read JSON file"""
        file_path = self.base_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filename}: {e}")
    
    def write_json(self, filename: str, data: Dict, indent: int = 2) -> bool:
        """Write data to JSON file"""
        file_path = self.base_path / filename
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=indent, default=str)
            return True
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize data to JSON: {e}")
    
    def list_files(self, extension: Optional[str] = None) -> List[str]:
        """List files in base directory"""
        if not self.base_path.exists():
            return []
        
        files = []
        for file_path in self.base_path.iterdir():
            if file_path.is_file():
                if extension is None or file_path.suffix == extension:
                    files.append(file_path.name)
        
        return sorted(files)

class StringHelper:
    """String manipulation utilities"""
    
    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if max_length < 0:
            raise ValueError("max_length cannot be negative")
        
        if len(text) <= max_length:
            return text
        
        truncated_length = max_length - len(suffix)
        if truncated_length < 0:
            return suffix[:max_length]
        
        return text[:truncated_length] + suffix
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """Extract all integers from text"""
        return [int(match) for match in re.findall(r'-?\d+', text)]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email for privacy (keep first char and domain)"""
        if not EmailValidator.validate(email):
            return email  # Return as-is if not valid email
        
        local, domain = email.split('@')
        if len(local) <= 1:
            masked_local = local
        else:
            masked_local = local[0] + '*' * (len(local) - 1)
        
        return f"{masked_local}@{domain}"

class ConfigManager:
    """Configuration management utility"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.file_manager = FileManager()
        self._config = None
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            self._config = self.file_manager.read_json(self.config_file)
            return self._config
        except FileNotFoundError:
            # Return default config if file doesn't exist
            self._config = self.get_default_config()
            return self._config
    
    def save_config(self, config: Dict) -> bool:
        """Save configuration to file"""
        self._config = config
        return self.file_manager.write_json(self.config_file, config)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        if self._config is None:
            self.load_config()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        if self._config is None:
            self.load_config()
        
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        return self.save_config(self._config)
    
    @staticmethod
    def get_default_config() -> Dict:
        """Get default configuration"""
        return {
            "api": {
                "base_url": "http://localhost:8000",
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "features": {
                "email_validation": True,
                "auto_complete_tasks": False
            }
        }