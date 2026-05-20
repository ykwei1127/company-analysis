"""
Migration script: Rename data files to new naming convention.
Run once: python migrate_filenames.py
"""
import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')

renames = {
    'asus_locations.json': 'asus_office.json',
    'nvidia_matched.json': 'nvidia_office.json',
    'asus_matched_country.json': 'asus_country.json',
    'nvidia_matched_country.json': 'nvidia_country.json',
    'dell_technologies_matched_country.json': 'dell_technologies_country.json',
    'msi_matched_country.json': 'msi_country.json',
    'tsmc_matched_country.json': 'tsmc_country.json',
}

if __name__ == '__main__':
    for old, new in renames.items():
        old_path = os.path.join(data_dir, old)
        new_path = os.path.join(data_dir, new)
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                print(f'SKIP (target exists): {old} -> {new}')
            else:
                os.rename(old_path, new_path)
                print(f'OK: {old} -> {new}')
        else:
            print(f'NOT FOUND: {old}')

    print('\nCurrent data files:')
    for f in sorted(os.listdir(data_dir)):
        if f.endswith('.json'):
            print(f'  {f}')

    print('\nDone! You can delete this script now.')
