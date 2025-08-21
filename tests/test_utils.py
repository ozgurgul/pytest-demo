import pytest
import json
import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils import (
    ValidationError, EmailValidator, DataProcessor, 
    FileManager, StringHelper, ConfigManager
)

# Mark this module as unit tests
pytestmark = pytest.mark.unit

class TestEmailValidator:
    """Test cases for EmailValidator"""
    
    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("test.email+tag@domain.co.uk", True),
        ("user123@gmail.com", True),
        ("invalid.email", False),
        ("@domain.com", False),
        ("user@", False),
        ("", False),
        ("user@domain", False),  # No TLD
        (None, False),
        (123, False),
    ])
    def test_validate(self, email, expected):
        """Test email validation with various inputs"""
        assert EmailValidator.validate(email) == expected
    
    def test_validate_strict_success(self):
        """Test strict validation with valid email"""
        result = EmailValidator.validate_strict("Test@Example.COM")
        assert result == "test@example.com"  # Should lowercase and strip
    
    def test_validate_strict_failure(self):
        """Test strict validation with invalid email"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            EmailValidator.validate_strict("invalid-email")
    
    def test_validate_strict_with_whitespace(self):
        """Test strict validation removes whitespace"""
        result = EmailValidator.validate_strict("  test@example.com  ")
        assert result == "test@example.com"

class TestDataProcessor:
    """Test cases for DataProcessor"""
    
    @pytest.mark.parametrize("part,total,expected", [
        (50, 100, 50.0),
        (25, 100, 25.0),
        (100, 100, 100.0),
        (0, 100, 0.0),
        (75, 200, 37.5),
    ])
    def test_calculate_percentage_valid(self, part, total, expected):
        """Test percentage calculation with valid inputs"""
        result = DataProcessor.calculate_percentage(part, total)
        assert result == expected
    
    def test_calculate_percentage_zero_total(self):
        """Test percentage calculation with zero total"""
        result = DataProcessor.calculate_percentage(50, 0)
        assert result == 0.0
    
    @pytest.mark.parametrize("part,total", [
        (-10, 100),
        (50, -100),
        (-10, -100),
    ])
    def test_calculate_percentage_negative_values(self, part, total):
        """Test percentage calculation with negative values"""
        with pytest.raises(ValueError, match="Values cannot be negative"):
            DataProcessor.calculate_percentage(part, total)
    
    def test_group_by_key_success(self):
        """Test successful grouping by key"""
        items = [
            {"category": "A", "value": 1},
            {"category": "B", "value": 2},
            {"category": "A", "value": 3},
            {"category": "C", "value": 4},
        ]
        
        result = DataProcessor.group_by_key(items, "category")
        
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert len(result["A"]) == 2
        assert len(result["B"]) == 1
        assert len(result["C"]) == 1
    
    def test_group_by_key_missing_key(self):
        """Test grouping when key is missing from some items"""
        items = [
            {"category": "A", "value": 1},
            {"value": 2},  # Missing category key
        ]
        
        with pytest.raises(KeyError, match="Key 'category' not found"):
            DataProcessor.group_by_key(items, "category")
    
    def test_filter_by_date_range(self):
        """Test filtering by date range"""
        items = [
            {"id": 1, "date": "2023-01-15"},
            {"id": 2, "date": "2023-02-15"},
            {"id": 3, "date": "2023-03-15"},
            {"id": 4, "date": "2023-04-15"},
        ]
        
        start_date = datetime.date(2023, 2, 1)
        end_date = datetime.date(2023, 3, 31)
        
        result = DataProcessor.filter_by_date_range(
            items, "date", start_date, end_date
        )
        
        assert len(result) == 2
        assert result[0]["id"] == 2
        assert result[1]["id"] == 3
    
    def test_filter_by_date_range_invalid_dates(self):
        """Test filtering with invalid date formats"""
        items = [
            {"id": 1, "date": "invalid-date"},
            {"id": 2, "date": "2023-02-15"},
        ]
        
        result = DataProcessor.filter_by_date_range(items, "date")
        
        # Should skip invalid dates
        assert len(result) == 1
        assert result[0]["id"] == 2

class TestFileManager:
    """Test cases for FileManager"""
    
    def test_init_with_custom_path(self, temp_dir):
        """Test FileManager initialization with custom path"""
        fm = FileManager(str(temp_dir))
        assert fm.base_path == temp_dir
    
    def test_write_and_read_json(self, file_manager):
        """Test writing and reading JSON files"""
        test_data = {"key": "value", "number": 42}
        
        # Write JSON
        result = file_manager.write_json("test.json", test_data)
        assert result is True
        
        # Read JSON
        read_data = file_manager.read_json("test.json")
        assert read_data == test_data
    
    def test_read_nonexistent_file(self, file_manager):
        """Test reading a file that doesn't exist"""
        with pytest.raises(FileNotFoundError):
            file_manager.read_json("nonexistent.json")
    
    def test_read_invalid_json(self, temp_dir):
        """Test reading invalid JSON file"""
        # Create invalid JSON file
        invalid_file = temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        fm = FileManager(str(temp_dir))
        with pytest.raises(ValueError, match="Invalid JSON"):
            fm.read_json("invalid.json")
    
    def test_write_json_creates_directory(self, temp_dir):
        """Test that write_json creates directories if needed"""
        fm = FileManager(str(temp_dir))
        
        result = fm.write_json("subdir/nested/file.json", {"test": True})
        assert result is True
        
        # Check file was created
        file_path = temp_dir / "subdir" / "nested" / "file.json"
        assert file_path.exists()
    
    def test_list_files(self, temp_dir):
        """Test listing files in directory"""
        # Create some test files
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file2.json").touch()
        (temp_dir / "file3.py").touch()
        (temp_dir / "subdir").mkdir()  # Directory should be ignored
        
        fm = FileManager(str(temp_dir))
        
        # List all files
        all_files = fm.list_files()
        assert len(all_files) == 3
        assert "file1.txt" in all_files
        assert "file2.json" in all_files
        assert "file3.py" in all_files
        
        # List only JSON files
        json_files = fm.list_files(".json")
        assert json_files == ["file2.json"]
    
    def test_list_files_empty_directory(self, temp_dir):
        """Test listing files in empty directory"""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        fm = FileManager(str(empty_dir))
        files = fm.list_files()
        assert files == []

class TestStringHelper:
    """Test cases for StringHelper"""
    
    @pytest.mark.parametrize("input_text,expected", [
        ("Hello World", "hello-world"),
        ("Hello World!", "hello-world"),
        ("test   123", "test-123"),
        ("---test---", "test"),
        ("CamelCase", "camelcase"),
        ("", ""),
        ("   ", ""),
        ("Test@#$%Case", "testcase"),
    ])
    def test_slugify(self, input_text, expected):
        """Test text slugification"""
        result = StringHelper.slugify(input_text)
        assert result == expected
    
    @pytest.mark.parametrize("text,max_len,suffix,expected", [
        ("Hello World", 20, "...", "Hello World"),
        ("Hello World", 8, "...", "Hello..."),
        ("Hello World", 5, "...", "He..."),
        ("Hello World", 2, "...", ".."),
        ("Hello World", 0, "...", ""),
        ("Test", 10, "", "Test"),
    ])
    def test_truncate(self, text, max_len, suffix, expected):
        """Test text truncation"""
        result = StringHelper.truncate(text, max_len, suffix)
        assert result == expected
    
    def test_truncate_negative_length(self):
        """Test truncate with negative max_length"""
        with pytest.raises(ValueError, match="max_length cannot be negative"):
            StringHelper.truncate("test", -1)
    
    @pytest.mark.parametrize("text,expected", [
        ("abc123def456", [123, 456]),
        ("No numbers here", []),
        ("negative -42 and positive 100", [-42, 100]),
        ("", []),
        ("123", [123]),
    ])
    def test_extract_numbers(self, text, expected):
        """Test number extraction from text"""
        result = StringHelper.extract_numbers(text)
        assert result == expected
    
    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", "t***@example.com"),
        ("a@domain.com", "a@domain.com"),  # Single char local part
        ("long.email.address@example.com", "l*******************@example.com"),
        ("invalid-email", "invalid-email"),  # Invalid email unchanged
    ])
    def test_mask_email(self, email, expected):
        """Test email masking"""
        result = StringHelper.mask_email(email)
        assert result == expected

class TestConfigManager:
    """Test cases for ConfigManager"""
    
    def test_get_default_config(self):
        """Test default configuration structure"""
        config = ConfigManager.get_default_config()
        
        assert "api" in config
        assert "logging" in config
        assert "features" in config
        assert config["api"]["base_url"] == "http://localhost:8000"
    
    def test_load_nonexistent_config(self, config_manager):
        """Test loading config when file doesn't exist"""
        config = config_manager.load_config()
        
        # Should return default config
        default_config = ConfigManager.get_default_config()
        assert config == default_config
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading configuration"""
        test_config = {
            "test_key": "test_value",
            "nested": {"key": "value"}
        }
        
        # Save config
        result = config_manager.save_config(test_config)
        assert result is True
        
        # Load config
        loaded_config = config_manager.load_config()
        assert loaded_config == test_config
    
    def test_get_config_value(self, config_manager):
        """Test getting configuration values"""
        test_config = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            }
        }
        config_manager.save_config(test_config)
        
        # Test getting nested value
        assert config_manager.get("level1.level2.key") == "value"
        
        # Test getting non-existent key with default
        assert config_manager.get("nonexistent.key", "default") == "default"
        
        # Test getting non-existent key without default
        assert config_manager.get("nonexistent.key") is None
    
    def test_set_config_value(self, config_manager):
        """Test setting configuration values"""
        # Set a simple value
        result = config_manager.set("simple_key", "simple_value")
        assert result is True
        assert config_manager.get("simple_key") == "simple_value"
        
        # Set a nested value
        config_manager.set("nested.deep.key", "nested_value")
        assert config_manager.get("nested.deep.key") == "nested_value"
        
        # Verify the structure was created
        config = config_manager.load_config()
        assert config["nested"]["deep"]["key"] == "nested_value"

# Slow tests (marked for selective execution)
class TestSlowOperations:
    """Tests that are marked as slow"""
    
    @pytest.mark.slow
    def test_large_data_processing(self):
        """Test processing large amounts of data"""
        # Simulate processing large dataset
        large_dataset = [{"id": i, "value": i * 2} for i in range(10000)]
        
        result = DataProcessor.group_by_key(large_dataset, "id")
        assert len(result) == 10000
    
    @pytest.mark.slow
    def test_complex_file_operations(self, temp_dir):
        """Test complex file operations"""
        fm = FileManager(str(temp_dir))
        
        # Create many files
        for i in range(100):
            fm.write_json(f"file_{i}.json", {"index": i})
        
        files = fm.list_files(".json")
        assert len(files) == 100