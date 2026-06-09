"""
Tests for the get_release_for_year utility function.

These tests verify that the local CSV lookup table correctly maps
measure IDs and BRFSS years to PLACES data releases.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from places.utils import get_release_for_year


class TestGetReleaseForYear:
    """Test suite for get_release_for_year function."""
    
    def test_2025_release_measures(self):
        """Test measures using 2023 BRFSS data in 2025 release."""
        # Most measures in 2025 use 2023 data
        measures_2023 = [
            "CSMOKING", "ARTHRITIS", "BINGE", "BPHIGH", "CANCER",
            "CASTHMA", "CHD", "CHECKUP", "CHOLSCREEN", "COGNITION",
            "COPD", "DIABETES", "DISABILITY", "DEPRESSION", "EMOTIONSPT",
            "FOODINSECU", "FOODSTAMP", "GHLTH", "HEARING", "HIGHCHOL",
            "HOUSINSECU", "INDEPLIVE", "LACKTRPT", "LPA", "MHLTH",
            "MOBILITY", "OBESITY", "PHLTH", "SELFCARE", "SHUTUTILITY",
            "STROKE", "VISION", "ACCESS2", "BPMED", "LONELINESS"
        ]
        
        for measure in measures_2023:
            result = get_release_for_year(measure, "2023")
            assert result == "places_release_2025", \
                f"{measure} with year 2023 should return places_release_2025, got {result}"
    
    def test_2025_release_even_year_measures(self):
        """Test even-year measures in 2025 release (use 2022 data)."""
        measures_2022 = [
            "TEETHLOST", "SLEEP", "COLON_SCREEN", "DENTAL", "MAMMOUSE"
        ]
        
        for measure in measures_2022:
            result = get_release_for_year(measure, "2022")
            # These measures use 2022 data, which was also in 2024 release
            # Function returns the first match (2024)
            assert result in ["places_release_2024", "places_release_2025"], \
                f"{measure} with year 2022 should return a valid release, got {result}"
    
    def test_new_measure_loneliness(self):
        """Test the new LONELINESS measure added in 2025."""
        result = get_release_for_year("LONELINESS", "2023")
        assert result == "places_release_2025", \
            "LONELINESS is a new measure in 2025 release"
    
    def test_2024_release_measures(self):
        """Test measures using 2022 BRFSS data in 2024 release."""
        measures_2024 = [
            "ARTHRITIS", "CANCER", "CASTHMA", "CHD", "COPD",
            "DEPRESSION", "DIABETES", "OBESITY", "STROKE"
        ]
        
        for measure in measures_2024:
            result = get_release_for_year(measure, "2022")
            assert result == "places_release_2024", \
                f"{measure} with year 2022 should return places_release_2024, got {result}"
    
    def test_2023_release_measures(self):
        """Test measures in 2023 release."""
        result = get_release_for_year("ARTHRITIS", "2021")
        assert result == "places_release_2023", \
            "ARTHRITIS with year 2021 should return places_release_2023"
        
        result = get_release_for_year("KIDNEY", "2021")
        assert result == "places_release_2023", \
            "KIDNEY with year 2021 should return places_release_2023"
    
    def test_discontinued_measures(self):
        """Test measures that were discontinued after certain releases."""
        # KIDNEY was discontinued after 2023 release
        result = get_release_for_year("KIDNEY", "2022")
        assert result is None, \
            "KIDNEY was discontinued and should not have 2022 data"
        
        # CERVICAL, COREM, COREW were discontinued after 2023
        result = get_release_for_year("CERVICAL", "2023")
        assert result is None, \
            "CERVICAL was discontinued and should not have recent data"
    
    def test_odd_year_measures(self):
        """Test measures that are only collected in odd years."""
        # BPHIGH is an odd-year measure
        result = get_release_for_year("BPHIGH", "2021")
        assert result == "places_release_2024", \
            "BPHIGH (odd-year) with 2021 should return places_release_2024"
        
        result = get_release_for_year("BPHIGH", "2023")
        assert result == "places_release_2025", \
            "BPHIGH (odd-year) with 2023 should return places_release_2025"
        
        # HIGHCHOL is an odd-year measure
        result = get_release_for_year("HIGHCHOL", "2023")
        assert result == "places_release_2025", \
            "HIGHCHOL (odd-year) with 2023 should return places_release_2025"
    
    def test_even_year_measures(self):
        """Test measures that are only collected in even years."""
        # TEETHLOST is an even-year measure
        result = get_release_for_year("TEETHLOST", "2022")
        assert result == "places_release_2024", \
            "TEETHLOST (even-year) with 2022 should return places_release_2024"
        
        # SLEEP is an even-year measure
        result = get_release_for_year("SLEEP", "2022")
        assert result == "places_release_2024", \
            "SLEEP (even-year) with 2022 should return places_release_2024"
    
    def test_invalid_measure_id(self):
        """Test with invalid measure ID."""
        result = get_release_for_year("INVALID_MEASURE", "2023")
        assert result is None, \
            "Invalid measure ID should return None"
    
    def test_invalid_year(self):
        """Test with year that doesn't exist for a measure."""
        result = get_release_for_year("CSMOKING", "2030")
        assert result is None, \
            "Future year should return None"
        
        result = get_release_for_year("CSMOKING", "2010")
        # Very old year might still match 500 Cities data
        # If not found, should return None
        assert result is None or "500cities_release" in result, \
            "Old year should either return None or 500 Cities release"
    
    def test_year_as_integer(self):
        """Test that function accepts year as integer."""
        result = get_release_for_year("CSMOKING", 2023)
        assert result == "places_release_2025", \
            "Function should accept year as integer"
    
    def test_year_as_string(self):
        """Test that function accepts year as string."""
        result = get_release_for_year("CSMOKING", "2023")
        assert result == "places_release_2025", \
            "Function should accept year as string"
    
    def test_case_sensitivity(self):
        """Test that measure IDs are case-sensitive."""
        result_upper = get_release_for_year("CSMOKING", "2023")
        result_lower = get_release_for_year("csmoking", "2023")
        
        assert result_upper == "places_release_2025", \
            "Uppercase measure ID should work"
        assert result_lower is None, \
            "Lowercase measure ID should not match (case-sensitive)"
    
    def test_all_categories_represented(self):
        """Test that measures from all categories are accessible."""
        categories = {
            "HLTHOUT": "ARTHRITIS",      # Health Outcomes
            "RISKBEH": "CSMOKING",       # Health Risk Behaviors
            "HLTHSTAT": "GHLTH",         # Health Status
            "PREVENT": "CHECKUP",        # Prevention
            "DISABILT": "HEARING",       # Disability
            "SOCLNEED": "LONELINESS",    # Health-Related Social Needs
        }
        
        for category, measure in categories.items():
            result = get_release_for_year(measure, "2023")
            assert result is not None, \
                f"Measure {measure} from category {category} should be accessible"


class TestLookupTableConsistency:
    """Test the consistency and completeness of the lookup table data."""
    
    def test_2025_release_column_exists(self):
        """Verify that the 2025 release column was added."""
        import pandas as pd
        from places.config import LOOKUP_TABLE_PATH
        
        df = pd.read_csv(LOOKUP_TABLE_PATH)
        assert 'PLACES Release 2025' in df.columns, \
            "Lookup table should have 'PLACES Release 2025' column"
    
    def test_loneliness_measure_exists(self):
        """Verify that LONELINESS measure was added to the table."""
        import pandas as pd
        from places.config import LOOKUP_TABLE_PATH
        
        df = pd.read_csv(LOOKUP_TABLE_PATH)
        assert 'LONELINESS' in df['MeasureID'].values, \
            "LONELINESS measure should exist in lookup table"
        
        # Verify it has correct metadata
        loneliness_row = df[df['MeasureID'] == 'LONELINESS'].iloc[0]
        assert loneliness_row['CategoryID'] == 'SOCLNEED', \
            "LONELINESS should be in SOCLNEED category"
        assert loneliness_row['PLACES Release 2025'] == '2023', \
            "LONELINESS should use 2023 data in 2025 release"
    
    def test_total_measure_count(self):
        """Verify the total number of measures in the table."""
        import pandas as pd
        from places.config import LOOKUP_TABLE_PATH
        
        df = pd.read_csv(LOOKUP_TABLE_PATH)
        # Original table had 44 measures, LONELINESS was added = 45 total
        assert len(df) == 45, \
            f"Lookup table should have 45 measures, found {len(df)}"
    
    def test_no_missing_measure_ids(self):
        """Verify all rows have a MeasureID."""
        import pandas as pd
        from places.config import LOOKUP_TABLE_PATH
        
        df = pd.read_csv(LOOKUP_TABLE_PATH)
        assert df['MeasureID'].notna().all(), \
            "All rows should have a MeasureID"
        assert (df['MeasureID'] != '').all(), \
            "No MeasureID should be empty string"
    
    def test_2025_data_distribution(self):
        """Verify the distribution of years in 2025 release."""
        import pandas as pd
        from places.config import LOOKUP_TABLE_PATH
        
        df = pd.read_csv(LOOKUP_TABLE_PATH)
        release_2025 = df['PLACES Release 2025'].value_counts()
        
        # Should have measures with 2023 data, 2022 data, and X (not available)
        assert '2023' in release_2025.index, \
            "2025 release should have measures with 2023 data"
        assert '2022' in release_2025.index, \
            "2025 release should have measures with 2022 data"
        assert 'X' in release_2025.index, \
            "2025 release should have some measures marked as unavailable"
        
        # Most measures should use 2023 data (35 measures)
        assert release_2025.get('2023', 0) >= 30, \
            "Most 2025 measures should use 2023 data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
