"""
Quick test script for the fixed DataManager
Run this to verify everything is working correctly
"""
import sys
sys.path.insert(0, 'manager')

from data_manager import DataManager

def test_data_manager():
    print("=" * 60)
    print("DataManager Test")
    print("=" * 60)

    # Initialize
    print("\nInitializing DataManager...")
    dm = DataManager()

    # Get data info
    print("\n" + "=" * 60)
    print("Data Info")
    print("=" * 60)
    info = dm.get_data_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test civilizations
    print("\n" + "=" * 60)
    print("Civilizations")
    print("=" * 60)
    civs = dm.get_civ_names()
    print(f"Total civilizations: {len(civs)}")
    print(f"First 10: {civs[:10]}")

    # Test getting specific civ data
    if len(civs) > 0:
        test_civ = civs[0]
        print(f"\nTesting get_civ_data('{test_civ}'):")
        civ_data = dm.get_civ_data(test_civ)
        if civ_data:
            print(f"  Name: {civ_data.get('name')}")
            print(f"  Has 'bons' key: {'bons' in civ_data}")
            print(f"  Has 'unique' key: {'unique' in civ_data}")
            if 'bons' in civ_data:
                print(f"  Bonuses: {civ_data['bons'][:2]}")

    # Test units
    print("\n" + "=" * 60)
    print("Units")
    print("=" * 60)
    units = dm.get_unit_names()
    print(f"Total units: {len(units)}")
    print(f"First 10: {units[:10]}")

    # Test getting specific unit data
    if len(units) > 0:
        test_unit = units[0]
        print(f"\nTesting get_unit_data('{test_unit}'):")
        unit_data = dm.get_unit_data(test_unit)
        if unit_data:
            print(f"  Name: {unit_data.get('name')}")
            print(f"  Keys: {list(unit_data.keys())[:5]}")

    # Test search
    print("\n" + "=" * 60)
    print("Search Functions")
    print("=" * 60)

    # Search for archers
    archer_units = dm.search_units('archer')
    print(f"Units matching 'archer': {len(archer_units)}")
    if archer_units:
        print(f"  Examples: {[u['name'] for u in archer_units[:5]]}")

    # Search for castle
    castle_buildings = dm.search_buildings('castle')
    print(f"Buildings matching 'castle': {len(castle_buildings)}")
    if castle_buildings:
        print(f"  Examples: {[b['name'] for b in castle_buildings[:5]]}")

    # Test technologies
    print("\n" + "=" * 60)
    print("Technologies")
    print("=" * 60)
    techs = dm.get_tech_names()
    print(f"Total technologies: {len(techs)}")
    print(f"First 10: {techs[:10]}")

    # Test buildings
    print("\n" + "=" * 60)
    print("Buildings")
    print("=" * 60)
    buildings = dm.get_building_names()
    print(f"Total buildings: {len(buildings)}")
    print(f"First 10: {buildings[:10]}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

    # Summary
    print("\nSummary:")
    if len(civs) > 0:
        print("  Civilizations: PASS")
    else:
        print("  Civilizations: FAIL")

    if len(units) > 0:
        print("  Units: PASS")
    else:
        print("  Units: FAIL")

    if len(techs) > 0:
        print("  Technologies: PASS")
    else:
        print("  Technologies: FAIL")

    if len(buildings) > 0:
        print("  Buildings: PASS")
    else:
        print("  Buildings: FAIL")


if __name__ == '__main__':
    test_data_manager()