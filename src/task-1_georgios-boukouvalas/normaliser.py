from typing import List, Dict
from urllib.parse import urlparse, urlunparse
from models import InputRecord, NormalizedRecord

def get_canonical_url(url: str) -> str:
    """
    Cleans a URL by converting the domain to lowercase and removing 
    query strings (like ?utm=tracking) and fragments.
    """
    parsed = urlparse(str(url))
    # Reconstruct the URL keeping only scheme, network location, and path
    canonical = urlunparse((
        parsed.scheme.lower(), 
        parsed.netloc.lower(), 
        parsed.path, 
        '', # drop params
        '', # drop query
        ''  # drop fragment
    ))
    # Remove trailing slashes for consistent matching
    return canonical.rstrip('/')

def normalize_and_deduplicate(input_records: List[InputRecord]) -> List[NormalizedRecord]:
    """
    Processes a list of raw records, standardizes their URLs, and deduplicates them.
    Merges the provenance of duplicates into a single discovery_lineage.
    """
    seen_records: Dict[str, NormalizedRecord] = {}

    for record in input_records:
        canonical_url = get_canonical_url(str(record.url))
        
        if canonical_url in seen_records:
            # We found a duplicate. Merge the provenance into the existing record.
            existing_record = seen_records[canonical_url]
            
            for item in record.provenance:
                if item not in existing_record.discovery_lineage:
                    existing_record.discovery_lineage.append(item)
        else:
            # First time seeing this record. Create the base NormalizedRecord.
            normalized = NormalizedRecord(
                source_id=record.id,
                canonical_url=canonical_url,
                publisher=record.publisher,
                source_type=record.source_type,
                publication_date=record.publication_date,
                discovery_lineage=list(record.provenance) 
            )
            seen_records[canonical_url] = normalized
            
    # Return the deduplicated records as a list
    return list(seen_records.values())