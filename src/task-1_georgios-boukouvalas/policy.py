from models import NormalizedRecord, Eligibility

def apply_policies(record: NormalizedRecord) -> NormalizedRecord:
    # Rule 1: Primary sources are eligible
    if record.source_type == "primary":
        record.eligibility = Eligibility.ELIGIBLE
        record.reason_codes.append("VALID_PRIMARY_SOURCE")
        return record
        
    # Rule 2: Competitor promotional claims are excluded
    if record.source_type == "competitor_promo":
        record.eligibility = Eligibility.EXCLUDED
        record.reason_codes.append("COMPETITOR_PRODUCT_CLAIM")
        return record
        
    # Rule 3: Competitor generic claims need verification (not automatically trusted)
    if record.source_type == "competitor_generic":
        record.eligibility = Eligibility.VERIFICATION_REQUIRED
        record.reason_codes.append("COMPETITOR_GENERIC_NEEDS_INDEPENDENT_VERIFICATION")
        return record
        
    # Default fallback
    record.eligibility = Eligibility.EXCLUDED
    record.reason_codes.append("UNRECOGNIZED_SOURCE_TYPE")
    return record