#!/usr/bin/env python3
"""
Script to fix corrupted data in the company table.
Specifically addresses records where website URLs have leaked into other fields.
"""

import sys
import re
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db.session import engine
from app.models.company import Company

def find_corrupted_records(session: Session):
    """Find records with URL-like content in non-URL fields."""
    url_pattern = re.compile(r'^(https?://|www\.)', re.IGNORECASE)
    
    corrupted = []
    companies = session.exec(select(Company)).all()
    
    for c in companies:
        issues = []
        
        # Check market_type for URL-like content
        if c.market_type and url_pattern.match(c.market_type):
            issues.append(f"market_type contains URL: {c.market_type}")
        
        # Check address for URL-like content at the start
        if c.address and url_pattern.match(c.address):
            issues.append(f"address starts with URL: {c.address[:50]}...")
        
        # Check industry for URL-like content
        if c.industry and url_pattern.match(c.industry):
            issues.append(f"industry contains URL: {c.industry}")
        
        if issues:
            corrupted.append({
                "code": c.code,
                "name": c.name,
                "issues": issues
            })
    
    return corrupted

def fix_specific_records(session: Session):
    """Fix known corrupted records."""
    fixes_applied = []
    
    # Known corrupted records based on investigation
    known_issues = {
        "000638": {
            "expected_market_type": "Public",
            "website": "WWW.KUANZHO.COM.TW",
        },
        "000104": {
            "expected_market_type": "Public",
        }
    }
    
    for code, fixes in known_issues.items():
        company = session.exec(
            select(Company).where(Company.code == code)
        ).first()
        
        if not company:
            print(f"Warning: Company {code} not found in database")
            continue
        
        # Check if market_type is corrupted (contains URL-like string)
        if company.market_type and re.match(r'^(https?://|www\.)', company.market_type, re.IGNORECASE):
            old_value = company.market_type
            company.market_type = fixes.get("expected_market_type", "Public")
            fixes_applied.append(f"{code}: Fixed market_type from '{old_value}' to '{company.market_type}'")
        
        # If website was in wrong field, ensure it's in the right place
        if "website" in fixes and (not company.website or company.website != fixes["website"]):
            company.website = fixes["website"]
            fixes_applied.append(f"{code}: Set website to '{company.website}'")
        
        session.add(company)
    
    return fixes_applied

def main():
    print("=" * 60)
    print("Company Data Corruption Fix Script")
    print("=" * 60)
    
    with Session(engine) as session:
        # Step 1: Find all corrupted records
        print("\n[1/3] Scanning for corrupted records...")
        corrupted = find_corrupted_records(session)
        
        if corrupted:
            print(f"Found {len(corrupted)} corrupted record(s):")
            for record in corrupted:
                print(f"  - {record['code']} ({record['name']})")
                for issue in record["issues"]:
                    print(f"      {issue}")
        else:
            print("No corrupted records found.")
        
        # Step 2: Apply fixes
        print("\n[2/3] Applying fixes...")
        fixes = fix_specific_records(session)
        
        if fixes:
            print(f"Applied {len(fixes)} fix(es):")
            for fix in fixes:
                print(f"  - {fix}")
            session.commit()
            print("\nChanges committed to database.")
        else:
            print("No fixes needed or no known issues found.")
        
        # Step 3: Verify
        print("\n[3/3] Verifying fix...")
        remaining = find_corrupted_records(session)
        if remaining:
            print(f"Warning: {len(remaining)} corrupted record(s) still remain.")
        else:
            print("All known corruptions have been fixed!")
    
    print("\n" + "=" * 60)
    print("Script completed.")
    print("=" * 60)

if __name__ == "__main__":
    main()
