import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

class DataManager:
    """Manage AoE2 data from GitHub JSON files"""

    def __init__(self, data_dir="data", cache_hours=24):
        """
        Initialize the data manager

        Args:
            data_dir: Directory to store cached JSON files
            cache_hours: Hours before re-downloading data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_hours = cache_hours

        # GitHub raw content URLs
        self.base_url = "https://raw.githubusercontent.com/SiegeEngineers/aoe2techtree/master/data"

        # Data file paths - data.json contains EVERYTHING
        self.files = {
            'main': 'data.json',  # Contains: civ_names, tech_tree_strings, age_names, building_names, unit_names, tech_names, civ_helptexts
        }

        # Trees directory for per-civ tech trees
        self.trees_url = f"{self.base_url}/trees"

        # Loaded data cache
        self.data = {}
        self.civ_trees = {}  # Separate cache for individual civ trees

        # Load data on initialization
        self.load_all_data()

    def _get_cache_file(self, filename):
        """Get the local cache file path"""
        return self.data_dir / filename

    def _is_cache_valid(self, filepath):
        """Check if cached file is still valid"""
        if not filepath.exists():
            return False

        # Check file age
        file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        age = datetime.now() - file_time

        return age < timedelta(hours=self.cache_hours)

    def _download_file(self, filename, url):
        """Download a file from GitHub"""
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to cache
            cache_file = self._get_cache_file(filename)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2)

            print(f"Downloaded {filename} successfully")
            return response.json()
        except requests.RequestException as e:
            print(f"Error downloading {filename}: {e}")
            return None

    def _load_file(self, key, filename):
        """Load a data file (from cache or download)"""
        cache_file = self._get_cache_file(filename)

        # Use cache if valid
        if self._is_cache_valid(cache_file):
            print(f"Loading {filename} from cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Download if cache invalid or missing
        url = f"{self.base_url}/{filename}"
        data = self._download_file(filename, url)

        # Fallback to cache if download failed
        if data is None and cache_file.exists():
            print(f"Download failed, using cached {filename}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return data

    def load_all_data(self):
        """Load all data files"""
        print("Loading AoE2 data...")

        for key, filename in self.files.items():
            data = self._load_file(key, filename)
            if data:
                self.data[key] = data
            else:
                print(f"Warning: Failed to load {filename}")
                self.data[key] = {}

        print("Data loading complete!")

    def force_update(self):
        """Force download of fresh data"""
        print("Forcing data update...")

        for key, filename in self.files.items():
            url = f"{self.base_url}/{filename}"
            data = self._download_file(filename, url)
            if data:
                self.data[key] = data

        print("Data update complete!")

    def get_civ_names(self):
        """Get list of all civilization names from data.json"""
        main_data = self.data.get('main', {})
        civs = main_data.get('civs', {})
        return sorted(civs.keys())

    def get_civ_data(self, civ_name):
        """Get civilization data by name (case-insensitive)"""
        main_data = self.data.get('main', {})
        civs = main_data.get('civs', {})
        civ_name_lower = civ_name.lower()

        for name, data in civs.items():
            if name.lower() == civ_name_lower:
                return {'name': name, **data}
        return None

    def load_civ_tree(self, civ_name):
        """
        Load individual civ tech tree from data/trees/
        Returns the full tech tree data for a specific civilization
        """
        # Check cache first
        if civ_name in self.civ_trees:
            return self.civ_trees[civ_name]

        # Construct filename (trees use lowercase with underscores)
        filename = f"{civ_name.lower().replace(' ', '_')}.json"
        cache_file = self.data_dir / f"tree_{filename}"

        # Check if cached file is valid
        if self._is_cache_valid(cache_file):
            print(f"Loading {civ_name} tree from cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                self.civ_trees[civ_name] = tree_data
                return tree_data

        # Download from trees directory
        url = f"{self.trees_url}/{filename}"
        try:
            print(f"Downloading {civ_name} tech tree...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            tree_data = response.json()

            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2)

            self.civ_trees[civ_name] = tree_data
            return tree_data
        except requests.RequestException as e:
            print(f"Error downloading {civ_name} tree: {e}")

            # Try to load from cache even if expired
            if cache_file.exists():
                print(f"Using expired cache for {civ_name} tree")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    tree_data = json.load(f)
                    self.civ_trees[civ_name] = tree_data
                    return tree_data

            return None

    def get_unit_names(self):
        """Get all unit names from data.json"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})
        return sorted(units.keys())

    def get_unit_data(self, unit_name):
        """Get unit data by name (case-insensitive)"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})
        unit_name_lower = unit_name.lower()

        for name, data in units.items():
            if name.lower() == unit_name_lower:
                return {'name': name, **data}
        return None

    def get_tech_names(self):
        """Get all technology names from data.json"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        techs = data_section.get('Tech', {})
        return sorted(techs.keys())

    def get_tech_data(self, tech_name):
        """Get technology data by name (case-insensitive)"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        techs = data_section.get('Tech', {})
        tech_name_lower = tech_name.lower()

        for name, data in techs.items():
            if name.lower() == tech_name_lower:
                return {'name': name, **data}
        return None

    def get_building_names(self):
        """Get all building names from data.json"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})
        return sorted(buildings.keys())

    def get_building_data(self, building_name):
        """Get building data by name (case-insensitive)"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})
        building_name_lower = building_name.lower()

        for name, data in buildings.items():
            if name.lower() == building_name_lower:
                return {'name': name, **data}
        return None

    def get_age_names(self):
        """Get all age names from data.json"""
        main_data = self.data.get('main', {})
        age_names = main_data.get('age_names', {})
        # age_names structure has nested data, extract the values
        result = {}
        for age_key, age_data in age_names.items():
            if isinstance(age_data, dict):
                result[age_key] = age_data
            elif isinstance(age_data, list):
                result[age_key] = age_data
        return result

    def get_tech_tree_strings(self):
        """Get tech tree strings from data.json"""
        main_data = self.data.get('main', {})
        return main_data.get('tech_tree_strings', {})

    def search_units(self, query):
        """Search for units matching query"""
        query_lower = query.lower()
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})

        matches = []
        for unit_name, unit_data in units.items():
            if query_lower in unit_name.lower():
                matches.append({'name': unit_name, **unit_data})

        return matches

    def search_techs(self, query):
        """Search for technologies matching query"""
        query_lower = query.lower()
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        techs = data_section.get('Tech', {})

        matches = []
        for tech_name, tech_data in techs.items():
            if query_lower in tech_name.lower():
                matches.append({'name': tech_name, **tech_data})

        return matches

    def search_buildings(self, query):
        """Search for buildings matching query"""
        query_lower = query.lower()
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})

        matches = []
        for building_name, building_data in buildings.items():
            if query_lower in building_name.lower():
                matches.append({'name': building_name, **building_data})

        return matches

    def get_data_info(self):
        """Get information about loaded data"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})

        info = {
            'civs_count': len(main_data.get('civs', {})),
            'units_count': len(data_section.get('Unit', {})),
            'techs_count': len(data_section.get('Tech', {})),
            'buildings_count': len(data_section.get('Building', {})),
            'ages_count': len(main_data.get('age_names', {})),
            'loaded_civ_trees': len(self.civ_trees)
        }

        # Get cache age
        data_file = self._get_cache_file('data.json')
        if data_file.exists():
            file_time = datetime.fromtimestamp(data_file.stat().st_mtime)
            info['last_update'] = file_time.strftime('%Y-%m-%d %H:%M:%S')

        return info


if __name__ == '__main__':
    # Test the data manager
    dm = DataManager()

    print("\n=== Data Info ===")
    info = dm.get_data_info()
    for key, value in info.items():
        print(f"{key}: {value}")

    print("\n=== All Civilizations ===")
    civs = dm.get_civ_names()
    print(f"Found {len(civs)} civilizations")
    print(civs[:10], "...")

    print("\n=== Test: Load Britons Tech Tree ===")
    if 'Britons' in civs:
        tree = dm.load_civ_tree('Britons')
        if tree:
            print(f"Loaded Britons tech tree with keys: {list(tree.keys())[:5]}")

    print("\n=== Sample Units ===")
    units = dm.get_unit_names()
    print(f"Found {len(units)} units")
    print(units[:10])

    print("\n=== Sample Technologies ===")
    techs = dm.get_tech_names()
    print(f"Found {len(techs)} technologies")
    print(techs[:10])

    print("\n=== Sample Buildings ===")
    buildings = dm.get_building_names()
    print(f"Found {len(buildings)} buildings")
    print(buildings[:10])

    print("\n=== Search Test ===")
    archer_units = dm.search_units('archer')
    print(f"Units matching 'archer': {[u['name'] for u in archer_units[:5]]}")