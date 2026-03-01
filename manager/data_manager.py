import json
import requests
import difflib
from datetime import datetime, timedelta
from pathlib import Path

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

        # Data file paths
        self.files = {
            'main': 'data.json',       # Contains: civ_names, tech_tree_strings, age_names, building_names, unit_names, tech_names
            'strings': 'strings.json', # Contains: localized text for civs, units, techs (bonus descriptions etc.)
        }

        # Trees directory for per-civ tech trees
        self.trees_url = f"{self.base_url}/trees"

        # Loaded data cache
        self.data = {}
        self.civ_trees = {}  # Separate cache for individual civ trees
        # Remote trees index cache (filename list from GitHub API)
        self._trees_index = None
        self._trees_index_time = None
        # Whether remote per-civ tree files are available (None = unknown)
        self.trees_available = None

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

        # After loading main data.json, attempt to download all per-civ tech trees so commands don't trigger on-demand downloads
        try:
            self._download_all_trees()
        except Exception as e:
            print(f"Warning: could not download all civ trees on startup: {e}")

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

    def get_civ_parsed_info(self, civ_name):
        """Parse the help string for a civ into structured bonus data.

        Returns a dict with keys:
            civ_type   - e.g. "Cavalry civilization"
            bonuses    - list of bonus strings
            unique_units - list of unique unit name strings
            unique_techs - list of unique tech name strings
            team_bonus - string
        """
        import re, html as html_lib

        civ_data = self.get_civ_data(civ_name)
        if not civ_data:
            return None

        help_id = str(civ_data.get('help_string_id', ''))
        strings = self.data.get('strings', {})
        raw = strings.get(help_id, '')

        if not raw:
            return {
                'name': civ_data.get('name', civ_name),
                'civ_type': '',
                'bonuses': [],
                'unique_units': [],
                'unique_techs': [],
                'team_bonus': '',
            }

        # Strip HTML tags but keep structure
        def strip_tags(text):
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<b>(.*?)</b>', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '', text)
            text = html_lib.unescape(text)
            return text

        plain = strip_tags(raw)
        lines = [l.strip() for l in plain.splitlines()]
        lines = [l.lstrip('\u2022').strip() for l in lines if l.strip()]

        result = {
            'name': civ_data.get('name', civ_name),
            'civ_type': '',
            'bonuses': [],
            'unique_units': [],
            'unique_techs': [],
            'team_bonus': '',
        }

        section = 'bonuses'
        for line in lines:
            low = line.lower()
            if not result['civ_type'] and 'civilization' in low:
                result['civ_type'] = line
                continue
            if low.startswith('unique unit'):
                section = 'unique_units'
                continue
            if low.startswith('unique tech'):
                section = 'unique_techs'
                continue
            if low.startswith('team bonus'):
                section = 'team_bonus'
                continue

            if section == 'bonuses':
                result['bonuses'].append(line)
            elif section == 'unique_units':
                result['unique_units'].append(line)
            elif section == 'unique_techs':
                result['unique_techs'].append(line)
            elif section == 'team_bonus':
                if result['team_bonus']:
                    result['team_bonus'] += ' ' + line
                else:
                    result['team_bonus'] = line

        return result

    def load_civ_tree(self, civ_name):
        """
        Load individual civ tech tree from data/trees/
        Returns the full tech tree data for a specific civilization
        """
        # Check cache first
        if civ_name in self.civ_trees:
            return self.civ_trees[civ_name]

        # Construct filename (trees use lowercase with underscores)
        # Normalized cache filename (always use lowercase with underscores for local cache)
        normalized = civ_name.lower().replace(' ', '_')
        filename = f"{normalized}.json"
        cache_file = self.data_dir / f"tree_{filename}"

        # Check if cached file is valid
        if self._is_cache_valid(cache_file):
            print(f"Loading {civ_name} tree from cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                self.civ_trees[civ_name] = tree_data
                return tree_data

        # Discover remote tree filenames and get best-matching remote candidates
        remote_candidates = self._discover_remote_trees(normalized)

        # If remote trees are not available, avoid making raw download attempts and use cache only
        if not self.trees_available:
            print(f"Remote per-civ tree files not available; using local cache only for {civ_name}.")
            if cache_file.exists():
                try:
                    print(f"Using expired cache for {civ_name} tree")
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        tree_data = json.load(f)
                        self.civ_trees[civ_name] = tree_data
                        return tree_data
                except Exception as e:
                    print(f"Error loading expired cache for {civ_name}: {e}")
            return None

        # Fallback: try common variants locally if remote discovery didn't find anything
        fallback_variants = [
            f"{civ_name}.json",
            f"{civ_name.replace(' ', '_')}.json",
            f"{civ_name.title()}.json",
            f"{civ_name.capitalize()}.json",
            f"{civ_name.lower()}.json",
            f"{normalized}.json",
            f"{civ_name.title().replace(' ', '_')}.json",
        ]

        # Compose final candidate list: discovered remote candidates first, then fallback unique variants
        candidates = []
        for rc in (remote_candidates or []):
            if rc and rc not in candidates:
                candidates.append(rc)
        for fv in fallback_variants:
            if fv not in candidates:
                candidates.append(fv)

        last_error = None
        print(f"Attempting to download tech tree for {civ_name} (trying {len(candidates)} variants)...")
        for cand in candidates:
            url = f"{self.trees_url}/{cand}"
            try:
                print(f"Downloading {cand} from {url}...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                tree_data = response.json()

                # Save to cache (always under normalized cache filename)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(tree_data, f, indent=2)

                self.civ_trees[civ_name] = tree_data
                print(f"Downloaded {cand} successfully")
                return tree_data
            except requests.RequestException as e:
                last_error = e
                print(f"Error downloading {cand}: {e}")
                continue

        # If we reach here, all download attempts failed
        print(f"Failed to download tech tree for {civ_name}. Last error: {last_error}")

        # Try to load from cache even if expired
        if cache_file.exists():
            try:
                print(f"Using expired cache for {civ_name} tree")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    tree_data = json.load(f)
                    self.civ_trees[civ_name] = tree_data
                    return tree_data
            except Exception as e:
                print(f"Error loading expired cache for {civ_name}: {e}")

        # Mark remote trees as unavailable to avoid repeated 404s on future calls
        self.trees_available = False
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

        info = {}
        info['civs_count'] = len(main_data.get('civs', {}))
        info['units_count'] = len(data_section.get('Unit', {}))
        info['techs_count'] = len(data_section.get('Tech', {}))
        info['buildings_count'] = len(data_section.get('Building', {}))
        info['ages_count'] = len(main_data.get('age_names', {}))
        info['loaded_civ_trees'] = len(self.civ_trees)

        # Get cache age
        data_file = self._get_cache_file('data.json')
        if data_file.exists():
            file_time = datetime.fromtimestamp(data_file.stat().st_mtime)
            info['last_update'] = file_time.strftime('%Y-%m-%d %H:%M:%S')

        return info

    def _fetch_remote_trees_index(self):
        """Fetch the list of files in data/trees from the GitHub API and cache the result."""
        # Use cached index if fresh
        if self._trees_index and self._trees_index_time and (datetime.now() - self._trees_index_time) < timedelta(hours=self.cache_hours):
            return self._trees_index

        api_url = "https://api.github.com/repos/SiegeEngineers/aoe2techtree/contents/data/trees"
        try:
            r = requests.get(api_url, timeout=30)
            r.raise_for_status()
            items = r.json()
            remote_list = [it['name'] for it in items if it.get('type') == 'file']
            self._trees_index = remote_list
            self._trees_index_time = datetime.now()
            self.trees_available = bool(remote_list)
            return remote_list
        except requests.RequestException as e:
            print(f"Could not fetch remote trees index: {e}")
            self.trees_available = False
            return None

    def _download_all_trees(self):
        """Download all civilization tree files discovered in the repo's data/trees directory.

        Saves each tree under the local cache filename 'tree_{normalized}.json' where normalized is the remote file name
        without extension lowercased (underscores preserved). Also populates self.civ_trees for any civs present
        in data.json so `?civ` commands won't trigger on-demand downloads.
        """
        # Ensure main data loaded
        main = self.data.get('main')
        if not main:
            return

        remote_list = self._fetch_remote_trees_index()
        if not remote_list:
            return

        civs = main.get('civs', {})
        civ_names = list(civs.keys())

        for remote_name in remote_list:
            # remote_name is like 'MAGYARS.json' or 'magyars.json'
            if not remote_name.lower().endswith('.json'):
                continue
            base = remote_name[:-5]
            normalized = base.lower().replace(' ', '_')
            cache_filename = f"tree_{normalized}.json"
            cache_file = self.data_dir / cache_filename

            # Skip download if cache is valid
            if self._is_cache_valid(cache_file):
                # Load into memory mapping if possible
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        tree_data = json.load(f)
                    # Find matching civ display names and set mapping (prefer exact normalized match, else fuzzy match)
                    matched = False
                    for civ_display in civ_names:
                        if civ_display.lower().replace(' ', '_') == normalized:
                            self.civ_trees[civ_display] = tree_data
                            matched = True
                            break
                    if not matched:
                        # Try fuzzy match on normalized civ names
                        civ_norms = [c.lower().replace(' ', '_') for c in civ_names]
                        matches = difflib.get_close_matches(normalized, civ_norms, n=1, cutoff=0.6)
                        if matches:
                            idx = civ_norms.index(matches[0])
                            self.civ_trees[civ_names[idx]] = tree_data
                except Exception:
                    pass
                continue

            # Download the raw file
            url = f"{self.trees_url}/{remote_name}"
            try:
                print(f"Downloading {remote_name} from {url}...")
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                tree_data = r.json()
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(tree_data, f, indent=2)
                # Populate mapping for matching civ(s) (exact normalized or fuzzy)
                matched = False
                for civ_display in civ_names:
                    if civ_display.lower().replace(' ', '_') == normalized:
                        self.civ_trees[civ_display] = tree_data
                        matched = True
                        break
                if not matched:
                    civ_norms = [c.lower().replace(' ', '_') for c in civ_names]
                    matches = difflib.get_close_matches(normalized, civ_norms, n=1, cutoff=0.6)
                    if matches:
                        idx = civ_norms.index(matches[0])
                        self.civ_trees[civ_names[idx]] = tree_data
            except requests.RequestException as e:
                print(f"Failed to download {remote_name}: {e}")
                # continue trying other files
                continue

        # Summary: report which civs we populated and which remain missing
        loaded = list(self.civ_trees.keys())
        missing = [c for c in civ_names if c not in loaded]
        print(f"Downloaded/loaded {len(loaded)} civ tree(s) into memory: {loaded}")
        if missing:
            print(f"Civs without tree data after startup: {missing}")
        else:
            print("All civs have tree data loaded into memory.")

    def _discover_remote_trees(self, target):
        """Discover available remote tree files via GitHub API"""
        remote_candidates = []
        api_failed = False
        try:
            # Use GitHub API to list files in data/trees
            api_url = "https://api.github.com/repos/SiegeEngineers/aoe2techtree/contents/data/trees"
            # Cache the index for cache_hours to avoid repeated API calls
            if self._trees_index and self._trees_index_time and (datetime.now() - self._trees_index_time) < timedelta(hours=self.cache_hours):
                remote_list = self._trees_index
            else:
                print(f"Querying GitHub API for available tree files...")
                r = requests.get(api_url, timeout=30)
                r.raise_for_status()
                items = r.json()
                remote_list = [it['name'] for it in items if it.get('type') == 'file']
                self._trees_index = remote_list
                self._trees_index_time = datetime.now()

            if remote_list:
                # Build normalized -> filename mapping for fuzzy matching
                norm_map = {}
                norm_keys = []
                for name in remote_list:
                    key = name.lower()
                    # strip extension for better matching
                    if key.endswith('.json'):
                        key = key[:-5]
                    norm_map[key] = name
                    norm_keys.append(key)

                # Use passed target (normalized civ name) to pick best matches
                matches = difflib.get_close_matches(target, norm_keys, n=5, cutoff=0.5)
                for m in matches:
                    remote_candidates.append(norm_map.get(m))
        except requests.RequestException as e:
            print(f"Could not query GitHub API for tree filenames: {e}")
            api_failed = True

        # If API failed or returned no files, mark trees as unavailable
        if api_failed or not (self._trees_index and len(self._trees_index) > 0):
            if api_failed:
                print("GitHub API query failed; remote tree files discovery aborted.")
            else:
                print("No remote tree files discovered via GitHub API; remote trees marked as unavailable.")

            self.trees_available = False
            return None

        # If we reach here, remote trees were discovered
        self.trees_available = True

        # Optionally: log discovered remote candidates
        print(f"Discovered remote tree files: {remote_candidates}")

        # You can also return the list of discovered candidates if needed
        return remote_candidates

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