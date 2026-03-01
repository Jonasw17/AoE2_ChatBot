"""
Diagnostic script to check the data.json structure
Run this in your project directory to see what's actually downloaded
"""
import json
from pathlib import Path

def check_data_json():
    """Check the cached data.json file"""
    data_file = Path("data/data.json")

    print("=" * 60)
    print("Data.json Diagnostic Check")
    print("=" * 60)

    if not data_file.exists():
        print(f"\nFile NOT FOUND: {data_file}")
        print("The data manager has not downloaded the file yet.")
        print("Try running your bot or test script first.")
        return

    print(f"\nFile found: {data_file}")
    print(f"File size: {data_file.stat().st_size:,} bytes")

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\nJSON loaded successfully!")
        print(f"\nTop-level keys: {list(data.keys())}")

        print("\n" + "=" * 60)
        print("Data Structure")
        print("=" * 60)

        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                print(f"\n{key}:")
                print(f"  Type: dictionary")
                print(f"  Count: {len(value)} items")
                if len(value) > 0:
                    sample_keys = list(value.keys())[:5]
                    print(f"  Sample keys: {sample_keys}")
                    # Show first entry
                    first_key = list(value.keys())[0]
                    first_value = value[first_key]
                    if isinstance(first_value, str) and len(first_value) < 100:
                        print(f"  First entry: {first_key} = {first_value}")
                    else:
                        print(f"  First entry: {first_key} = {type(first_value).__name__}")
            elif isinstance(value, list):
                print(f"\n{key}:")
                print(f"  Type: list")
                print(f"  Count: {len(value)} items")
                if len(value) > 0:
                    print(f"  First item: {value[0]}")
            else:
                print(f"\n{key}: {type(value).__name__} = {value}")

        # Specific checks for expected keys
        print("\n" + "=" * 60)
        print("Expected Keys Check")
        print("=" * 60)

        expected_keys = {
            'civs': 'Civilization data',
            'data': 'Units, Techs, Buildings',
            'age_names': 'Age names',
            'tech_tree_strings': 'UI strings'
        }

        for key, description in expected_keys.items():
            if key in data:
                if isinstance(data[key], dict):
                    count = len(data[key])
                elif isinstance(data[key], list):
                    count = len(data[key])
                else:
                    count = "N/A"
                print(f"  {key}: FOUND ({count} items) - {description}")
            else:
                print(f"  {key}: MISSING - {description}")

        # Check data subdictionary
        if 'data' in data and isinstance(data['data'], dict):
            print("\n  Data subdictionary:")
            for subkey in ['Building', 'Tech', 'Unit', 'unit_upgrades']:
                if subkey in data['data']:
                    count = len(data['data'][subkey]) if isinstance(data['data'][subkey], dict) else "N/A"
                    print(f"    {subkey}: FOUND ({count} items)")
                else:
                    print(f"    {subkey}: MISSING")

        print("\n" + "=" * 60)
        print("Sample Data")
        print("=" * 60)

        # Show some actual civ names if they exist
        if 'civs' in data and isinstance(data['civs'], dict):
            civs = data['civs']
            if len(civs) > 0:
                print("\nSample Civilizations:")
                for i, civ_name in enumerate(list(civs.keys())[:10]):
                    civ_data = civs[civ_name]
                    # Try to show a bonus if available
                    bonus_info = ""
                    if isinstance(civ_data, dict):
                        if 'bons' in civ_data and isinstance(civ_data['bons'], list) and len(civ_data['bons']) > 0:
                            bonus_info = f" - First bonus: {civ_data['bons'][0][:50]}..."
                    print(f"  {civ_name}{bonus_info}")

        # Show some actual units if they exist
        if 'data' in data and isinstance(data['data'], dict):
            data_section = data['data']
            if 'Unit' in data_section and isinstance(data_section['Unit'], dict):
                units = data_section['Unit']
                if len(units) > 0:
                    print("\nSample Units:")
                    for i, unit_name in enumerate(list(units.keys())[:10]):
                        print(f"  {unit_name}")

            # Show some buildings
            if 'Building' in data_section and isinstance(data_section['Building'], dict):
                buildings = data_section['Building']
                if len(buildings) > 0:
                    print("\nSample Buildings:")
                    for i, building_name in enumerate(list(buildings.keys())[:10]):
                        print(f"  {building_name}")

    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON file!")
        print(f"  {e}")
        print("\nThe file is corrupted. Delete it and let the data manager re-download it.")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    check_data_json()