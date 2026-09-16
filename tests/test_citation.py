"""
Tests for citation metadata attached to CDC PLACES tool responses.

These tests cover the pure citation-building helpers in places.utils as well
as the response shape of the get_cdc_places_data tool (with the network layer
mocked so no external calls are made).
"""

import datetime
import re
import sys
import os

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from places.utils import (
    build_citation,
    get_measure_name,
    get_brfss_year,
    _socrata_dataset_id,
    _release_year,
    _release_column_for_release_name,
)
from places.config import DATA_DICTIONARY_ENDPOINT, PLACES_METHODOLOGY_URL


ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A representative resolved endpoint: county / places_release_2020
COUNTY_2020_URL = "https://data.cdc.gov/resource/dv4u-3x3q.json"


class TestGetMeasureName:
    """Test suite for get_measure_name."""

    def test_known_measure(self):
        name = get_measure_name("CSMOKING")
        assert name is not None
        assert "smoking" in name.lower()

    def test_another_known_measure(self):
        assert get_measure_name("OBESITY") is not None

    def test_invalid_measure(self):
        assert get_measure_name("NOT_A_REAL_MEASURE") is None


class TestGetBrfssYear:
    """Test suite for get_brfss_year."""

    def test_csmoking_2020_release(self):
        # In the 2020 PLACES release, CSMOKING uses 2018 BRFSS data.
        assert get_brfss_year("CSMOKING", "places_release_2020") == "2018"

    def test_csmoking_2025_release(self):
        assert get_brfss_year("CSMOKING", "places_release_2025") == "2023"

    def test_invalid_measure(self):
        assert get_brfss_year("NOT_A_REAL_MEASURE", "places_release_2020") is None

    def test_unknown_release(self):
        assert get_brfss_year("CSMOKING", "places_release_1999") is None

    def test_none_release(self):
        assert get_brfss_year("CSMOKING", None) is None


class TestReleaseHelpers:
    """Test suite for small release-name parsing helpers."""

    def test_socrata_dataset_id(self):
        assert _socrata_dataset_id(COUNTY_2020_URL) == "dv4u-3x3q"

    def test_socrata_dataset_id_trailing_slash(self):
        assert _socrata_dataset_id("https://data.cdc.gov/resource/abcd-1234.json/") == "abcd-1234"

    def test_socrata_dataset_id_none(self):
        assert _socrata_dataset_id(None) is None

    def test_release_year(self):
        assert _release_year("places_release_2020") == "2020"
        assert _release_year("500cities_release_2019") == "2019"

    def test_release_year_none(self):
        assert _release_year(None) is None

    def test_release_column_places(self):
        assert _release_column_for_release_name("places_release_2020") == "PLACES Release 2020"

    def test_release_column_500cities(self):
        assert _release_column_for_release_name("500cities_release_2019") == "500 Cities Release 2019"

    def test_release_column_unknown(self):
        assert _release_column_for_release_name("bogus") is None


class TestBuildCitation:
    """Test suite for build_citation."""

    @pytest.fixture
    def citation(self):
        return build_citation(
            geo="county",
            year="2020",
            measureid="CSMOKING",
            url=COUNTY_2020_URL,
            release_name="places_release_2020",
        )

    def test_has_all_expected_keys(self, citation):
        expected = {
            "source",
            "dataset",
            "release_year",
            "geography",
            "measure_id",
            "measure_name",
            "brfss_survey_year",
            "socrata_dataset_id",
            "source_url",
            "data_dictionary_url",
            "methodology_url",
            "accessed_date",
            "suggested_citation",
        }
        assert expected.issubset(set(citation.keys()))

    def test_core_fields(self, citation):
        assert citation["source"] == "CDC PLACES"
        assert citation["dataset"] == "places_release_2020"
        assert citation["release_year"] == "2020"
        assert citation["geography"] == "county"
        assert citation["measure_id"] == "CSMOKING"

    def test_dataset_id_extracted(self, citation):
        assert citation["socrata_dataset_id"] == "dv4u-3x3q"

    def test_measure_name_populated(self, citation):
        assert citation["measure_name"] is not None
        assert "smoking" in citation["measure_name"].lower()

    def test_brfss_year(self, citation):
        assert citation["brfss_survey_year"] == "2018"

    def test_urls(self, citation):
        assert citation["source_url"] == COUNTY_2020_URL
        assert citation["data_dictionary_url"] == DATA_DICTIONARY_ENDPOINT
        assert citation["methodology_url"] == PLACES_METHODOLOGY_URL

    def test_accessed_date_is_today_iso(self, citation):
        assert ISO_DATE_RE.match(citation["accessed_date"])
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        assert citation["accessed_date"] == today

    def test_suggested_citation_content(self, citation):
        text = citation["suggested_citation"]
        assert "CDC PLACES".split()[0] in text or "Centers for Disease Control" in text
        assert citation["socrata_dataset_id"] in text
        assert citation["source_url"] in text
        assert citation["measure_name"] in text
        assert citation["accessed_date"] in text

    def test_invalid_measure_still_builds(self):
        # Even with an unknown measure, a citation should be produced
        # (measure_name / brfss_survey_year fall back to None).
        citation = build_citation(
            geo="county",
            year="2020",
            measureid="NOT_A_REAL_MEASURE",
            url=COUNTY_2020_URL,
            release_name="places_release_2020",
        )
        assert citation["measure_id"] == "NOT_A_REAL_MEASURE"
        assert citation["measure_name"] is None
        assert citation["brfss_survey_year"] is None
        # Falls back to the measure id in the suggested citation text.
        assert "NOT_A_REAL_MEASURE" in citation["suggested_citation"]


def _extract_tool_fn(module):
    """Register the given tool module against a stub MCP and return the raw
    async tool function (undecorated) for direct invocation in tests."""
    from fastmcp import FastMCP

    mcp = FastMCP("test")
    captured = {}
    original_tool = mcp.tool

    def patched_tool(*args, **kwargs):
        def decorator(fn):
            captured["fn"] = fn
            return original_tool(*args, **kwargs)(fn)
        return decorator

    mcp.tool = patched_tool
    module.register(mcp)
    return captured["fn"]


class TestToolResponseShape:
    """Test the wrapped {data, citation} response of get_cdc_places_data."""

    @pytest.mark.asyncio
    async def test_success_returns_data_and_citation(self, monkeypatch):
        from places.tools import get_cdc_places_data as tool_module
        from places.models import MeasureID

        fake_records = [
            {"locationname": "Wayne", "data_value": "20.1"},
            {"locationname": "Oakland", "data_value": "15.3"},
        ]

        async def fake_query_api(url, api_params):
            return fake_records

        # Patch the query_api symbol imported into the tool module.
        monkeypatch.setattr(tool_module, "query_api", fake_query_api)

        fn = _extract_tool_fn(tool_module)
        result = await fn(
            year="2020",
            measureid=MeasureID.CSMOKING,
            geo="county",
            datavaluetypeid="CrdPrv",
            locationname="Wayne",
        )

        assert set(result.keys()) == {"data", "citation"}
        assert result["data"] == fake_records
        citation = result["citation"]
        assert citation["measure_id"] == "CSMOKING"
        assert citation["geography"] == "county"
        # CSMOKING requested with year=2020 resolves to the 2022 PLACES
        # release (county dataset duw2-7jbt) which draws on 2020 BRFSS data.
        assert citation["dataset"] == "places_release_2022"
        assert citation["socrata_dataset_id"] == "duw2-7jbt"
        assert citation["brfss_survey_year"] == "2020"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_unresolvable_endpoint_returns_error(self, monkeypatch):
        from places.tools import get_cdc_places_data as tool_module
        from places.models import MeasureID

        # Force get_endpoint to fail resolution.
        monkeypatch.setattr(tool_module, "get_endpoint", lambda geo, year, measureid: None)

        fn = _extract_tool_fn(tool_module)
        result = await fn(
            year="1900",
            measureid=MeasureID.CSMOKING,
            geo="county",
            datavaluetypeid="CrdPrv",
        )

        assert "error" in result
        assert "citation" not in result
        assert "data" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
