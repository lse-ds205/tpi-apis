"""
Test script for verifying text sanitization and case-insensitive matching in the DataHandler.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data_utils import BaseDataHandler

class TestDataHandlerSanitization(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        base_dir = Path(__file__).resolve().parent.parent
        base_data_dir = base_dir / "data"
        self.handler = BaseDataHandler(base_data_dir)
    
    def test_text_sanitization(self):
        """
        Test that the _sanitize_text method properly handles whitespace and case.
        
        This test verifies that:
        1. Leading and trailing spaces are removed
        2. Text is converted to lowercase by default
        3. Case is preserved when requested
        4. Special characters are NOT removed (only whitespace is affected)
        """
        # Test with a company name that has leading spaces in the data
        company_id = "yankuang_energy"
        details = self.handler.get_company_details(company_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["name"], "Yankuang Energy", 
                         "Company name should be properly sanitized with preserved case")
        
        test_cases = [
            ("  Company Name  ", "company name"), 
            ("Company & Co.", "company & co."),    
            ("Company   Name", "company   name"), 
        ]
        
        for input_text, expected_output in test_cases:
            sanitized = self.handler._sanitize_text(input_text)
            self.assertEqual(sanitized, expected_output, 
                            f"Failed to sanitize '{input_text}' correctly")
        
        # Test with preserve_case=True
        sanitized_with_case = self.handler._sanitize_text("  Company Name  ", preserve_case=True)
        self.assertEqual(sanitized_with_case, "Company Name", 
                         "Should preserve case but remove extra spaces")
    
    def test_case_insensitive_matching(self):
        """
        Test that case-insensitive matching works correctly for filtering.
        
        This test verifies that:
        1. Searches are case-insensitive for sectors
        2. Searches are case-insensitive for geographies
        3. The same results are returned regardless of case used in the query
        """
        # Test with different case variations of sector
        sector_variations = ["coal mining", "Coal Mining", "COAL MINING", " coal mining "]
        sector_results = []
        
        for sector in sector_variations:
            companies, total = self.handler.get_companies(sector=sector)
            self.assertGreater(total, 0, f"Should find companies for sector '{sector}'")
            sector_results.append(total)
            
            # Verify all returned companies have the correct sector
            for company in companies:
                self.assertEqual(company["sector"].lower(), "coal mining",
                                f"Company {company['name']} should have sector 'coal mining'")
        
        # All variations should return the same number of results
        self.assertEqual(len(set(sector_results)), 1, 
                        "All case variations should return the same number of results")
        
        # Test with different case variations of geography
        geo_variations = ["japan", "Japan", "JAPAN", " japan "]
        geo_results = []
        
        for geography in geo_variations:
            companies, total = self.handler.get_companies(geography=geography)
            self.assertGreater(total, 0, f"Should find companies for geography '{geography}'")
            geo_results.append(total)
        
        # All variations should return the same number of results
        self.assertEqual(len(set(geo_results)), 1,
                        "All case variations should return the same number of results")

if __name__ == "__main__":
    unittest.main() 