"""
Verify *_country.json URL consistency.

Checks:
1. URL contains the expected country slug
2. URL contains the expected IN code from COUNTRY_IN_CODES
3. URL is not obviously a redirect (e.g., contains 'aruba')

This is a static check; it cannot verify actual Glassdoor page content.
For full verification, run company_finder.py with a logged-in browser.
"""

import json
import os
import re
import sys

# Read COUNTRY_IN_CODES from company_finder.py without importing selenium
COUNTRY_IN_CODES = {
    'United States': '1',
    'Canada': '3',
    'Mexico': '173',
    'United Kingdom': '4',
    'France': '86',
    'Germany': '96',
    'Spain': '219',
    'Italy': '121',
    'Netherlands': '178',
    'Hungary': '113',
    'Poland': '197',
    'Czech Republic': '62',
    'Turkey': '244',
    'Sweden': '223',
    'Switzerland': '226',
    'Belgium': '17',
    'Austria': '14',
    'Denmark': '57',
    'Norway': '181',
    'Finland': '75',
    'Ireland': '114',
    'Portugal': '192',
    'Greece': '91',
    'Russia': '204',
    'Ukraine': '250',
    'Romania': '203',
    'Israel': '119',
    'United Arab Emirates': '247',
    'Saudi Arabia': '209',
    'South Africa': '211',
    'Egypt': '67',
    'Nigeria': '182',
    'Kenya': '128',
    'Morocco': '160',
    'China': '49',
    'Japan': '126',
    'South Korea': '135',
    'India': '115',
    'Singapore': '215',
    'Australia': '16',
    'Indonesia': '116',
    'Thailand': '239',
    'Vietnam': '251',
    'Malaysia': '170',
    'Philippines': '196',
    'Taiwan': '240',
    'Hong Kong': '104',
    'Brazil': '36',
    'Argentina': '11',
    'Chile': '51',
    'Colombia': '50',
    'Peru': '188',
    'Venezuela': '252',
    'Ecuador': '64',
    'Uruguay': '249',
}


def normalize_country(name):
    """Normalize country name for URL slug comparison."""
    if not name:
        return ''
    return name.strip().replace(' ', '-').lower()


def verify_country_json(path):
    """Verify a single *_country.json file."""
    issues = []
    non_found = []
    with open(path, encoding='utf-8') as f:
        entries = json.load(f)

    for entry in entries:
        company = entry.get('company', os.path.basename(path).replace('_country.json', ''))
        country = entry.get('baseline_country') or entry.get('matched_city') or ''
        location = entry.get('baseline_location', '?')
        status = entry.get('status', '?')
        url = entry.get('url', '')

        if status != 'found' or not url:
            non_found.append({
                'company': company,
                'location': location,
                'country': country,
                'status': status,
            })
            continue

        # Global entry: no country check
        if country.lower() == 'global':
            continue

        # Check 1: URL contains country slug
        expected_slug = normalize_country(country)
        if expected_slug and expected_slug not in url.lower().replace('%20', '-'):
            issues.append({
                'company': company,
                'country': country,
                'url': url,
                'problem': f'URL does not contain country slug "{expected_slug}"',
            })

        # Check 2: URL contains expected IN code
        expected_in = COUNTRY_IN_CODES.get(country)
        if expected_in and f'_IN{expected_in}.htm' not in url:
            issues.append({
                'company': company,
                'country': country,
                'url': url,
                'problem': f'URL IN code mismatch (expected IN{expected_in})',
            })

        # Check 3: URL contains suspicious terms
        suspicious_terms = ['aruba', 'bermuda', 'cayman']
        for term in suspicious_terms:
            if term in url.lower():
                issues.append({
                    'company': company,
                    'country': country,
                    'url': url,
                    'problem': f'URL contains suspicious term "{term}"',
                })

    return issues, non_found


def main():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.isdir(data_dir):
        print(f'Cannot find data directory: {data_dir}')
        sys.exit(1)

    all_issues = []
    all_non_found = []
    all_files = sorted([f for f in os.listdir(data_dir) if f.endswith('_country.json')])

    print(f'Checking {len(all_files)} country JSON files in {data_dir}\n')

    for filename in all_files:
        path = os.path.join(data_dir, filename)
        issues, non_found = verify_country_json(path)
        if issues or non_found:
            all_issues.extend(issues)
            all_non_found.extend([(filename, n) for n in non_found])
            if issues:
                print(f'[WARN] {filename}: {len(issues)} URL issue(s)')
                for issue in issues:
                    print(f'  - {issue["company"]} / {issue["country"]}')
                    print(f'    {issue["url"]}')
                    print(f'    -> {issue["problem"]}')
            if non_found:
                print(f'[INFO] {filename}: {len(non_found)} non-found entry(s)')
                for n in non_found:
                    print(f'  - {n["company"]} / {n["location"]} ({n["country"]}): {n["status"]}')
            print()
        else:
            print(f'[OK]   {filename}')

    print(f'\nTotal files checked: {len(all_files)}')
    print(f'Total URL issues found: {len(all_issues)}')
    print(f'Total non-found entries: {len(all_non_found)}')

    if all_issues or all_non_found:
        print('\nTo fully verify actual page content, run:')
        print('  python company_finder.py --mode country')
        print('with a logged-in Chrome browser.')
        sys.exit(1)
    else:
        print('\nAll country URLs look consistent (static check passed).')


if __name__ == '__main__':
    main()
