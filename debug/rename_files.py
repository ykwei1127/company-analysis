import os
data_dir = r'c:\Users\William_Yang\Desktop\Side\company-analysis\data'
renames = {
    'asus_locations.json': 'asus_office.json',
    'nvidia_matched.json': 'nvidia_office.json',
    'asus_matched_country.json': 'asus_country.json',
    'nvidia_matched_country.json': 'nvidia_country.json',
    'dell_technologies_matched_country.json': 'dell_technologies_country.json',
    'msi_matched_country.json': 'msi_country.json',
    'tsmc_matched_country.json': 'tsmc_country.json',
}
for old, new in renames.items():
    old_path = os.path.join(data_dir, old)
    new_path = os.path.join(data_dir, new)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f'Renamed: {old} -> {new}')
    else:
        print(f'NOT FOUND: {old}')

print('\nJSON files after rename:')
for f in sorted(os.listdir(data_dir)):
    if f.endswith('.json'):
        print(f'  {f}')
