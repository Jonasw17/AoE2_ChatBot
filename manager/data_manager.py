# -*- coding: utf-8 -*-
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

class DataManager:
    """Manage AoE2 data from GitHub JSON files with proper armor class handling"""

    # Armor class mappings (from AoE2 game data)
    ARMOR_CLASSES = {
        0: "Unused",
        1: "Infantry",
        2: "Turtle Ships",
        3: "Base Pierce",
        4: "Base Melee",
        5: "War Elephant",
        8: "Cavalry",
        11: "All Buildings",
        13: "Stone Defense",
        15: "Archers",
        16: "Ships & Camels",
        17: "Rams",
        19: "Trees",
        20: "Unique Units",
        21: "Siege Weapons",
        22: "Standard Buildings",
        23: "Walls & Gates",
        24: "Gunpowder Units",
        25: "Boars",
        26: "Monks",
        27: "Castle",
        28: "Spearmen",
        29: "Cavalry Archers",
        30: "Eagle Warriors",
        31: "Camels",
        32: "Fishing Ships",
        34: "Mamelukes",
        35: "Heroes",
        36: "Hussite Wagons",
    }

    # Unit type classifications - used only for the display label ("Cavalry Unit" etc.)
    # Counter data (strong_against / countered_by) is intentionally NOT stored here
    # because it is too coarse: Scout-line counters Monks while Knight-line is weak to
    # Monks, but both are classified as "Cavalry". The game's own description strings
    # (parsed by parse_description_string) are the authoritative source for counter info.
    UNIT_CLASSIFICATIONS = {
        'Infantry':       {},
        'Archer':         {},
        'Cavalry':        {},
        'Cavalry Archer': {},
        'Siege':          {},
        'Monk':           {},
    }

    def __init__(self, data_dir="data", cache_hours=24):
        """Initialize the data manager"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_hours = cache_hours

        # GitHub URLs
        self.base_url = "https://raw.githubusercontent.com/SiegeEngineers/aoe2techtree/master/data"
        self.api_base = "https://api.github.com/repos/SiegeEngineers/aoe2techtree/commits"

        self.files = {'main': 'data.json'}
        self.trees_url = f"{self.base_url}/trees"

        # Data caches
        self.data = {}
        self.civ_trees = {}
        self.unit_counters = {}

        # Load data
        self.load_all_data()

    def _get_cache_file(self, filename):
        return self.data_dir / filename

    def _get_metadata_file(self, filename):
        return self.data_dir / f"{filename}.meta"

    def _check_for_updates(self):
        """Check if GitHub data has been updated"""
        try:
            url = f"{self.api_base}?path=data&per_page=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            commits = response.json()
            if commits and len(commits) > 0:
                last_commit_date = commits[0]['commit']['committer']['date']
                last_commit_time = datetime.strptime(last_commit_date, '%Y-%m-%dT%H:%M:%SZ')

                meta_file = self._get_metadata_file('data.json')
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        cached_time = datetime.fromisoformat(meta.get('last_update', '2000-01-01'))

                        if last_commit_time > cached_time:
                            print(f"GitHub data updated: {last_commit_date}")
                            return True
                else:
                    return True

        except Exception as e:
            print(f"Could not check for updates: {e}")

        return False

    def _save_metadata(self, filename):
        """Save metadata about the cached file"""
        meta_file = self._get_metadata_file(filename)
        metadata = {
            'last_update': datetime.now().isoformat(),
            'filename': filename
        }
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def _is_cache_valid(self, filepath):
        """Check if cached file is still valid"""
        if not filepath.exists():
            return False

        if self._check_for_updates():
            print("GitHub data has been updated, invalidating cache...")
            return False

        file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        age = datetime.now() - file_time

        return age < timedelta(hours=self.cache_hours)

    def _download_file(self, filename, url):
        """Download a file from GitHub"""
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            cache_file = self._get_cache_file(filename)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2)

            self._save_metadata(filename)
            print(f"Downloaded {filename} successfully")
            return response.json()
        except requests.RequestException as e:
            print(f"Error downloading {filename}: {e}")
            return None

    def _load_file(self, key, filename):
        """Load a data file (from cache or download)"""
        cache_file = self._get_cache_file(filename)

        if self._is_cache_valid(cache_file):
            print(f"Loading {filename} from cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        url = f"{self.base_url}/{filename}"
        data = self._download_file(filename, url)

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

        # Load strings.json
        strings_data = self._load_strings()
        if strings_data:
            self.data['strings'] = strings_data

    def _load_strings(self):
        """Load strings.json"""
        cache_file = self.data_dir / 'strings.json'

        if self._is_cache_valid(cache_file):
            print("Loading strings.json from cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        url = f"{self.base_url}/locales/en/strings.json"
        try:
            print("Downloading strings.json...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self._save_metadata('strings.json')
            return data
        except requests.RequestException as e:
            print(f"Error downloading strings.json: {e}")
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

    def parse_armor(self, armor_data):
        """
        Parse armor data into readable format

        Input: [{'Amount': 2, 'Class': 4}, {'Amount': 0, 'Class': 8}, ...]
        Output: {'Melee': 2, 'Pierce': 2, 'Cavalry': 0, ...}
        """
        if not armor_data or not isinstance(armor_data, list):
            return {'Melee': 0, 'Pierce': 0}

        armor_dict = {}
        for armor in armor_data:
            if isinstance(armor, dict):
                class_id = armor.get('Class')
                amount = armor.get('Amount', 0)

                # Get armor class name
                class_name = self.ARMOR_CLASSES.get(class_id, f"Class {class_id}")

                # Map base melee/pierce to simple names
                if class_id == 4:
                    armor_dict['Melee'] = amount
                elif class_id == 3:
                    armor_dict['Pierce'] = amount
                elif amount > 0:  # Only include non-zero armor classes
                    armor_dict[class_name] = amount

        # Ensure Melee and Pierce are always present
        if 'Melee' not in armor_dict:
            armor_dict['Melee'] = 0
        if 'Pierce' not in armor_dict:
            armor_dict['Pierce'] = 0

        return armor_dict

    def parse_attacks(self, attack_data):
        """
        Parse attack bonuses into readable format

        Input: [{'Amount': 3, 'Class': 29}, {'Amount': 2, 'Class': 21}, ...]
        Output: {'Base': 4, 'vs Cavalry Archer': 3, 'vs Siege': 2, ...}

        Note: Attacks are ONLY bonus damage. Base damage is stored separately in the 'Attack' field.
        Class IDs 3 and 4 are 'Base Pierce' and 'Base Melee' which are NOT bonuses.
        """
        if not attack_data:
            return {}

        attacks = {}

        # Handle different attack data formats
        if isinstance(attack_data, (int, float)):
            attacks['Base'] = attack_data
        elif isinstance(attack_data, list):
            for atk in attack_data:
                if isinstance(atk, dict):
                    class_id = atk.get('Class')
                    amount = atk.get('Amount', 0)

                    # Skip base melee (4) and base pierce (3) - these are not bonuses
                    if amount > 0 and class_id not in [3, 4]:
                        class_name = self.ARMOR_CLASSES.get(class_id, f"Class {class_id}")
                        # Only add meaningful bonus attacks (not "Unused" etc)
                        if class_name and class_name != 'Unused':
                            attacks[f'vs {class_name}'] = amount

        return attacks

    def parse_description_string(self, help_id):
        """
        Parse any description string from strings.json by its help ID.

        Works for units, technologies, and buildings. The developer-written
        strings are patch-accurate; when the game is updated the strings are
        updated too, so reading them directly keeps the bot correct for free.

        Returns a dict with keys:
            description  - first flavour sentence (after stripping the
                           "Create/Build/Research <name>" opener)
            strong_vs    - list of targets this entity is strong against
            weak_vs      - list of targets this entity is weak against
            effect       - first sentence from upgrade/effect block (techs)
        """
        import re
        import html as html_lib

        strings = self.data.get('strings', {})
        raw = strings.get(str(help_id), '')

        empty = {'description': '', 'strong_vs': [], 'weak_vs': [], 'effect': ''}
        if not raw:
            return empty

        # --- flatten HTML ---
        text = re.sub(r'<br\s*/?>', '\n', raw, flags=re.IGNORECASE)
        text = re.sub(r'<b>(.*?)</b>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<i>(.*?)</i>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = html_lib.unescape(text)
        # Remove angle-bracket template placeholders like hp, attack, etc.
        text = re.sub(r'[<>]', '', text)
        # Remove parenthetical cost/placeholder tokens
        text = re.sub(r'\([\w\s]+\)', '', text)
        # Collapse whitespace, keep newlines
        lines = [' '.join(l.split()) for l in text.splitlines()]
        lines = [l.strip() for l in lines if l.strip()]

        def split_targets(raw_text):
            """'Infantry and Foot Archers, Siege Weapons' -> list"""
            # Clean up the text first
            raw_text = raw_text.strip().rstrip('.')

            # Split by commas and 'and'
            parts = re.split(r',\s*', raw_text)
            result = []
            for part in parts:
                # Split by 'and' but preserve compound names like "Spearman-line"
                for s in re.split(r'\s+and\s+', part):
                    s = re.sub(r'^and\s+', '', s.strip(), flags=re.IGNORECASE)
                    s = s.strip()
                    if s:
                        result.append(s)
            return result

        strong_vs  = []
        weak_vs    = []
        description = ''
        effect     = ''

        full_text = ' '.join(lines)

        # Strong vs. / Weak vs. (units and buildings)
        # Try multiple patterns to catch variations

        # Pattern 1: "Strong vs. X, Y, and Z."
        m = re.search(r'[Ss]trong\s+vs\.?\s+([^.]+?)\.', full_text)
        if m:
            strong_vs = split_targets(m.group(1))

        # Pattern 2: "Weak vs. X, Y, and Z."
        m = re.search(r'[Ww]eak\s+vs\.?\s+([^.]+?)\.', full_text)
        if m:
            weak_vs = split_targets(m.group(1))

        # Pattern 3: Alternative "against" format
        if not strong_vs:
            m = re.search(r'[Ss]trong\s+against\s+([^.]+?)\.', full_text)
            if m:
                strong_vs = split_targets(m.group(1))

        if not weak_vs:
            m = re.search(r'[Ww]eak\s+against\s+([^.]+?)\.', full_text)
            if m:
                weak_vs = split_targets(m.group(1))

        # Effect sentence: content of the <i>Upgrades / Researching...</i> block,
        # expressed as the first sentence inside it (useful for tech descriptions).
        upgrades_match = re.search(
            r'[Uu]pgrades?[:\s]+(.+?)(?:Upgrades?|$)', full_text
        )
        if upgrades_match:
            effect_raw = upgrades_match.group(1).strip().rstrip('.')
            if effect_raw:
                effect = effect_raw[:200]

        # Flavour description: first sentence that is not the "Create/Build/
        # Research <name>" opener and does not contain counter or upgrade text.
        for line in lines:
            sentences = [s.strip() for s in line.split('.') if s.strip()]
            for sentence in sentences:
                low = sentence.lower()
                if re.match(r'^(create|build|research|train)\b', low):
                    continue
                if any(kw in low for kw in ('strong vs', 'weak vs', 'strong against', 'weak against', 'upgrades', 'researching')):
                    continue
                if len(sentence) > 10:
                    description = sentence
                    break
            if description:
                break

        return {
            'description': description,
            'strong_vs':   strong_vs,
            'weak_vs':     weak_vs,
            'effect':      effect,
        }

    # Keep the old name as an alias so existing callers don't break
    def parse_unit_description(self, help_id):
        return self.parse_description_string(help_id)

    def get_unit_classification(self, unit_data, display_name=''):
        """Determine unit classification based on unit data.
        Checks internal_name first, then falls back to the display name so that
        units whose internal_name does not match (e.g. stored as an abbreviation
        or numeric key) are still classified correctly.
        """
        unit_type = unit_data.get('internal_name', '').upper()
        # Combine both so either one can produce a match
        search = unit_type + ' ' + display_name.upper()

        if any(x in search for x in ['ARCH', 'XBOW', 'LARCH', 'ARBALEST', 'CROSSBOW']):
            if any(x in search for x in ['CAVALRY ARCH', 'CAV ARCH', 'HCAVAL', 'AARCH']):
                return 'Cavalry Archer'
            return 'Archer'
        elif any(x in search for x in ['SPEAR', 'PIKE', 'HALBERD']):
            return 'Infantry'
        elif any(x in search for x in ['SWORD', 'MILITIA', 'EAGLE', 'CONDOT',
                                       'CHAMPION', 'LONGSWORD', 'MAN-AT-ARMS']):
            return 'Infantry'
        elif any(x in search for x in ['KNIGHT', 'PALADIN', 'PALAD',
                                       'HUSSAR', 'LANCER', 'CAVALIER']):
            return 'Cavalry'
        elif 'CAVAL' in search and 'ARCH' not in search:
            return 'Cavalry'
        elif any(x in search for x in ['SCORP', 'ONAGER', 'ONAGR', 'TREBUCHET',
                                       'TREB', ' RAM', 'BMBC', 'CANNON',
                                       'MANGONEL', 'BALLISTA']):
            return 'Siege'
        elif any(x in search for x in ['MONK', 'PRIEST']):
            return 'Monk'
        elif any(x in search for x in ['SKIRMISHER', 'SKIRM']):
            return 'Archer'

        return 'Other'

    def get_unit_counters_from_data(self, unit_data, display_name=''):
        """Get counter information based on actual unit data.
        Only returns the unit classification label and any bonus damage targets
        derived from the unit attack classes. Strong-against and countered-by
        lists are intentionally absent; they come from parse_description_string.
        """
        classification = self.get_unit_classification(unit_data, display_name)

        # Parse attack bonuses to determine explicit bonus damage targets.
        # Classes 3 (Base Pierce) and 4 (Base Melee) are the unit's own base
        # damage, not bonus damage vs a target type, so they are skipped.
        attacks = unit_data.get('Attacks', [])
        bonus_damage_vs = []

        if isinstance(attacks, list):
            for atk in attacks:
                if isinstance(atk, dict):
                    class_id = atk.get('Class')
                    amount   = atk.get('Amount', 0)
                    if amount > 0 and class_id not in [3, 4]:
                        class_name = self.ARMOR_CLASSES.get(class_id, '')
                        if class_name and class_name != 'Unused':
                            bonus_damage_vs.append(class_name)

        return {
            'classification': classification,
            'bonus_damage_vs': bonus_damage_vs,
        }

    def _resolve_unit_name(self, unit_data, unit_id, strings):
        """Resolve unit name from unit data"""
        import re

        lang_id = unit_data.get('LanguageNameId')
        if lang_id:
            string_id = str(lang_id + 9000)
            name = strings.get(string_id)
            if name and isinstance(name, str) and len(name) < 100:
                cleaned = name.replace('<br>', ' ').replace('\n', ' ').strip()
                cleaned = re.sub(r'\s+', ' ', cleaned)
                if '<' not in cleaned and '>' not in cleaned and 2 < len(cleaned) < 50:
                    return cleaned

        internal = unit_data.get('internal_name', '')
        if internal and (any(c.islower() for c in internal) or ' ' in internal):
            return internal

        return None

    def get_civ_names(self):
        """Get list of all civilization names"""
        main_data = self.data.get('main', {})
        civs = main_data.get('civs', {})
        return sorted(civs.keys())

    def get_civ_data(self, civ_name):
        """Get civilization data by name"""
        main_data = self.data.get('main', {})
        civs = main_data.get('civs', {})
        civ_name_lower = civ_name.lower()

        for name, data in civs.items():
            if name.lower() == civ_name_lower:
                return {'name': name, **data}
        return None

    def get_civ_parsed_info(self, civ_name):
        """Parse civ help string into structured data"""
        import re
        import html as html_lib

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

        def strip_tags(text):
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<b>(.*?)</b>', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '', text)
            text = html_lib.unescape(text)
            return text

        plain = strip_tags(raw)
        lines = [l.strip() for l in plain.splitlines()]
        lines = [l.lstrip('\u2022\u2023\u25E6\u2043').strip() for l in lines if l.strip()]

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

    def get_unit_names(self):
        """Get all unit names"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})
        strings = self.data.get('strings', {})

        unit_names = []
        for unit_id, unit_data in units.items():
            name = self._resolve_unit_name(unit_data, unit_id, strings)
            if name:
                unit_names.append(name)

        return sorted(unit_names)

    def get_unit_data(self, unit_name):
        """Get unit data by name with parsed armor and attacks"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})
        strings = self.data.get('strings', {})
        unit_name_lower = unit_name.lower()

        for unit_id, unit_data in units.items():
            resolved_name = self._resolve_unit_name(unit_data, unit_id, strings)
            if resolved_name and resolved_name.lower() == unit_name_lower:
                # Parse armor properly
                armor_raw = unit_data.get('Armours') or unit_data.get('Armor')
                unit_data['Armor_Parsed'] = self.parse_armor(armor_raw)

                # Parse attacks
                attacks_raw = unit_data.get('Attacks') or unit_data.get('Attack')
                unit_data['Attacks_Parsed'] = self.parse_attacks(attacks_raw)

                # Counter info from armor-class heuristics (kept as fallback)
                unit_data['Counter_Info'] = self.get_unit_counters_from_data(unit_data, resolved_name)

                # Counter info parsed directly from the official description string
                help_id = unit_data.get('LanguageHelpId')
                unit_data['Description_Info'] = (
                    self.parse_description_string(help_id) if help_id
                    else {'description': '', 'strong_vs': [], 'weak_vs': [], 'effect': ''}
                )

                return {'name': resolved_name, **unit_data}
        return None

    def search_units(self, query):
        """Return all units whose resolved name contains the query string."""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        units = data_section.get('Unit', {})
        strings = self.data.get('strings', {})
        query_lower = query.lower()

        results = []
        for unit_id, unit_data in units.items():
            name = self._resolve_unit_name(unit_data, unit_id, strings)
            if name and query_lower in name.lower():
                results.append({'name': name, **unit_data})
        return sorted(results, key=lambda u: u['name'])

    def get_tech_names(self):
        """Get all technology names"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        techs = data_section.get('Tech', {})
        return sorted(techs.keys())

    def get_tech_data(self, tech_name):
        """Get technology data by name, with description attached."""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        techs = data_section.get('Tech', {})
        tech_name_lower = tech_name.lower()

        for name, data in techs.items():
            if name.lower() == tech_name_lower:
                result = {'name': name, **data}
                help_id = data.get('LanguageHelpId')
                result['Description_Info'] = (
                    self.parse_description_string(help_id) if help_id
                    else {'description': '', 'strong_vs': [], 'weak_vs': [], 'effect': ''}
                )
                return result
        return None

    def get_building_names(self):
        """Get all building names"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})
        return sorted(buildings.keys())

    def get_building_data(self, building_name):
        """Get building data by name, with description and armor attached."""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})
        building_name_lower = building_name.lower()

        for name, data in buildings.items():
            if name.lower() == building_name_lower:
                result = {'name': name, **data}

                # Parse armor so HP/armor fields show correctly
                armor_raw = data.get('Armours') or data.get('Armor')
                result['Armor_Parsed'] = self.parse_armor(armor_raw)

                help_id = data.get('LanguageHelpId')
                result['Description_Info'] = (
                    self.parse_description_string(help_id) if help_id
                    else {'description': '', 'strong_vs': [], 'weak_vs': [], 'effect': ''}
                )
                return result
        return None

    def search_buildings(self, query):
        """Return all buildings whose name contains the query string."""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})
        buildings = data_section.get('Building', {})
        query_lower = query.lower()

        results = []
        for name, data in buildings.items():
            if query_lower in name.lower():
                results.append({'name': name, **data})
        return sorted(results, key=lambda b: b['name'])

    def get_data_info(self):
        """Get information about loaded data"""
        main_data = self.data.get('main', {})
        data_section = main_data.get('data', {})

        info = {}
        info['civs_count'] = len(main_data.get('civs', {}))
        info['units_count'] = len(data_section.get('Unit', {}))
        info['techs_count'] = len(data_section.get('Tech', {}))
        info['buildings_count'] = len(data_section.get('Building', {}))

        data_file = self._get_cache_file('data.json')
        if data_file.exists():
            file_time = datetime.fromtimestamp(data_file.stat().st_mtime)
            info['last_update'] = file_time.strftime('%Y-%m-%d %H:%M:%S')

        return info

    def force_update(self):
        """Force download of fresh data"""
        print("Forcing data update...")

        for key, filename in self.files.items():
            url = f"{self.base_url}/{filename}"
            data = self._download_file(filename, url)
            if data:
                self.data[key] = data

        strings_data = self._load_strings()
        if strings_data:
            self.data['strings'] = strings_data

        print("Data update complete!")

    def load_civ_tree(self, civ_name):
        """Load civ tech tree"""
        if civ_name in self.civ_trees:
            return self.civ_trees[civ_name]

        normalized = civ_name.lower().replace(' ', '_')
        filename = f"{normalized}.json"
        cache_file = self.data_dir / f"tree_{filename}"

        if self._is_cache_valid(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                self.civ_trees[civ_name] = tree_data
                return tree_data

        url = f"{self.trees_url}/{filename}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            tree_data = response.json()

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2)

            self.civ_trees[civ_name] = tree_data
            return tree_data
        except requests.RequestException:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    tree_data = json.load(f)
                    self.civ_trees[civ_name] = tree_data
                    return tree_data

        return None