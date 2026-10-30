import pytest
from pydantic import ValidationError

from models import InputRecord, Eligibility
from normaliser import normalize_and_deduplicate
from policy import apply_policies

def test_malformed_input_raises_validation_error():
    """Malformed or incomplete input must produce a predictable validation failure."""
    with pytest.raises(ValidationError):
        # Missing required fields like 'url' and 'publisher'
        InputRecord(id="bad_001", source_type="primary")

def test_duplicate_records_preserve_provenance():
    """Duplicate records should be identified correctly without losing provenance."""
    record1 = InputRecord(
        id="src_001", 
        url="https://agency.gov/report", 
        publisher="Gov", 
        source_type="primary", 
        provenance=["crawler_1"]
    )
    record2 = InputRecord(
        id="src_002", 
        url="https://agency.gov/report?utm=tracking", 
        publisher="Gov", 
        source_type="primary", 
        provenance=["user_upload"]
    )
    
    normalized = normalize_and_deduplicate([record1, record2])
    
    assert len(normalized) == 1, "The two records should be merged into one"
    assert normalized[0].canonical_url == "https://agency.gov/report"
    assert "crawler_1" in normalized[0].discovery_lineage
    assert "user_upload" in normalized[0].discovery_lineage

def test_unknown_date_remains_unknown():
    """A source with an unknown publication date must remain unknown."""
    record = InputRecord(
        id="src_003", 
        url="https://news.com/article", 
        publisher="News", 
        source_type="primary", 
        publication_date=None
    )
    
    normalized = normalize_and_deduplicate([record])[0]
    assert normalized.publication_date is None

def test_valid_primary_source():
    """A valid primary or authoritative source should pass the policy."""
    record = InputRecord(
        id="src_004", url="https://agency.gov", publisher="Gov", source_type="primary"
    )
    normalized = normalize_and_deduplicate([record])[0]
    result = apply_policies(normalized)
    
    assert result.eligibility == Eligibility.ELIGIBLE
    assert "VALID_PRIMARY_SOURCE" in result.reason_codes

def test_competitor_product_claim():
    """A competitor source containing a product claim must be excluded."""
    record = InputRecord(
        id="src_005", url="https://comp.com/promo", publisher="Comp", source_type="competitor_promo"
    )
    normalized = normalize_and_deduplicate([record])[0]
    result = apply_policies(normalized)
    
    assert result.eligibility == Eligibility.EXCLUDED
    assert "COMPETITOR_PRODUCT_CLAIM" in result.reason_codes

def test_competitor_generic_claim():
    """A generic industry claim from a competitor needs independent verification."""
    record = InputRecord(
        id="src_006", url="https://comp.com/blog", publisher="Comp", source_type="competitor_generic"
    )
    normalized = normalize_and_deduplicate([record])[0]
    result = apply_policies(normalized)
    
    assert result.eligibility == Eligibility.VERIFICATION_REQUIRED
    assert "COMPETITOR_GENERIC_NEEDS_INDEPENDENT_VERIFICATION" in result.reason_codes