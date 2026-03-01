# -*- coding: utf-8 -*-
"""
Data Manager for AoE2 Discord Bot
Handles downloading and caching data from github.com/SiegeEngineers/aoe2techtree

How the data source is actually structured
-------------------------------------------
data.json
  civs:
    "Britons":
      bons: [list of bonus strings]
      team_bonus: "..."
      unique:
        units: ["Longbowman", ...]
        techs: ["Yeoman", ...]
  data:
    Unit:
      "75":
        LanguageNameId: 5169      <-- look THIS up in strings.json, NOT "75"
        Cost: {Food: 60, Gold: 75}
        HP: 100
        Attack: 10
        Armor: {Melee: 2, Pierce: 3}
        Speed: 1.35
        Range: 0
    Tech:
      "93":
        LanguageNameId: 7082
        Cost: {...}
        ResearchTime: 35
    Building:
      "45":
        LanguageNameId: 5011
        Cost: {...}
        HP: 2400

locales/en/strings.json
  "5169": "Knight"
  "7082": "Ballistics"
  "5011": "Castle"

IMPORTANT: The key in data.json["data"]["Unit"] is a numeric unit ID.
The human name for that unit lives at strings[unit["LanguageNameId"]].
The unit ID and the LanguageNameId are DIFFERENT numbers.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path


BASE_URL = "https://raw.githubusercontent.com/SiegeEngineers/aoe2techtree/master/data"
DATA_URL = f"{BASE_URL}/data.json"
STRINGS_URL = f"{BASE_URL}/locales/en/strings.json"


class DataManager:
    """
    Downloads and caches AoE2 data.
    Uses LanguageNameId inside each unit/tech/building entry to resolve
    the human-readable name from strings.json.
    """

    def __init__(self, data_dir="data", cache_hours=24):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_hours = cache_hours

        self._data = {}
        self._strings = {}

        # name -> internal numeric id (the key in data.json["data"]["Unit"])
        self._unit_name_to_id = {}
        self._unit_id_to_name = {}
        self._tech_name_to_id = {}
        self._tech_id_to_name = {}
        self._building_name_to_id = {}
        self._building_id_to_name = {}

        self.load_all_data()

    # --------------------------------------------------------
    # Cache helpers
    # --------------------------------------------------------

    def _cache_path(self, filename):
        return self.data_dir / filename

    def _cache_valid(self, path):
        if not path.exists():
            return False
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        return age < timedelta(hours=self.cache_hours)

    def _download_json(self, url, cache_filename):
        path = self._cache_path(cache_filename)
        try:
            print(f"Downloading {cache_filename}...")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Saved {cache_filename}")
            return data
        except Exception as e:
            print(f"Download failed for {cache_filename}: {e}")
            return None

    def _load_cached_json(self, cache_filename):
        path = self._cache_path(cache_filename)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache {cache_filename}: {e}")
        return None

    def _get_json(self, url, cache_filename):
        """Return from valid cache if possible, otherwise download.
        Falls back to stale cache if download fails."""
        path = self._cache_path(cache_filename)
        if self._cache_valid(path):
            print(f"Loading {cache_filename} from cache...")
            return self._load_cached_json(cache_filename) or {}

        data = self._download_json(url, cache_filename)
        if data is not None:
            return data

        stale = self._load_cached_json(cache_filename)
        if stale:
            print(f"Using stale cache for {cache_filename}")
            return stale

        print(f"WARNING: No data available for {cache_filename}")
        return {}

    # --------------------------------------------------------
    # Load and build lookups
    # --------------------------------------------------------

    def load_all_data(self):
        print("Loading AoE2 data...")
        self._data = self._get_json(DATA_URL, "data.json")
        self._strings = self._get_json(STRINGS_URL, "strings.json")
        self._build_lookups()
        print(
            f"Ready. Civs: {len(self.get_civ_names())}, "
            f"Units: {len(self._unit_name_to_id)}, "
            f"Techs: {len(self._tech_name_to_id)}, "
            f"Buildings: {len(self._building_name_to_id)}"
        )

    def force_update(self):
        print("Forcing data update...")
        self._data = self._download_json(DATA_URL, "data.json") or self._data
        self._strings = self._download_json(STRINGS_URL, "strings.json") or self._strings
        self._build_lookups()
        print("Update complete.")

    def _build_lookups(self):
        """
        Build name<->id dicts for units, techs, and buildings.

        For each entry in data.json["data"]["Unit"]:
          - The dict key  (e.g. "75")  is the unit's internal ID
          - entry["LanguageNameId"]    is the key to look up in strings.json
          - strings[str(LanguageNameId)] is the human name (e.g. "Knight")

        Entries are skipped if:
          - LanguageNameId is missing or 0
          - The resolved name is empty or longer than 60 chars (help text)
        """
        data_section = self._data.get("data", {})

        def build(section_key):
            name_to_id = {}
            id_to_name = {}
            section = data_section.get(section_key, {})
            for entry_id, entry_data in section.items():
                if not isinstance(entry_data, dict):
                    continue

                lang_id = entry_data.get("LanguageNameId", 0)
                if not lang_id:
                    continue

                name = self._strings.get(str(lang_id), "").strip()
                if not name or len(name) > 60:
                    continue

                name_to_id[name] = str(entry_id)
                id_to_name[str(entry_id)] = name

            return name_to_id, id_to_name

        self._unit_name_to_id, self._unit_id_to_name = build("Unit")
        self._tech_name_to_id, self._tech_id_to_name = build("Tech")
        self._building_name_to_id, self._building_id_to_name = build("Building")

    # --------------------------------------------------------
    # Civilization
    # --------------------------------------------------------

    def get_civ_names(self):
        return sorted(self._data.get("civs", {}).keys())

    def get_civ_data(self, civ_name):
        civs = self._data.get("civs", {})
        for name, data in civs.items():
            if name.lower() == civ_name.lower():
                return {"name": name, **data}
        return None

    # --------------------------------------------------------
    # Units
    # --------------------------------------------------------

    def get_unit_names(self):
        return sorted(self._unit_name_to_id.keys())

    def get_unit_data(self, unit_name):
        target = unit_name.lower()
        unit_id = None
        for name, uid in self._unit_name_to_id.items():
            if name.lower() == target:
                unit_id = uid
                break
        if unit_id is None:
            return None
        raw = self._data.get("data", {}).get("Unit", {}).get(unit_id)
        if raw is None:
            return None
        return {"name": self._unit_id_to_name[unit_id], **raw}

    # --------------------------------------------------------
    # Technologies
    # --------------------------------------------------------

    def get_tech_names(self):
        return sorted(self._tech_name_to_id.keys())

    def get_tech_data(self, tech_name):
        target = tech_name.lower()
        tech_id = None
        for name, tid in self._tech_name_to_id.items():
            if name.lower() == target:
                tech_id = tid
                break
        if tech_id is None:
            return None
        raw = self._data.get("data", {}).get("Tech", {}).get(tech_id)
        if raw is None:
            return None
        return {"name": self._tech_id_to_name[tech_id], **raw}

    # --------------------------------------------------------
    # Buildings
    # --------------------------------------------------------

    def get_building_names(self):
        return sorted(self._building_name_to_id.keys())

    def get_building_data(self, building_name):
        target = building_name.lower()
        building_id = None
        for name, bid in self._building_name_to_id.items():
            if name.lower() == target:
                building_id = bid
                break
        if building_id is None:
            return None
        raw = self._data.get("data", {}).get("Building", {}).get(building_id)
        if raw is None:
            return None
        return {"name": self._building_id_to_name[building_id], **raw}

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    def search_units(self, query):
        q = query.lower()
        results = []
        for name, uid in self._unit_name_to_id.items():
            if q in name.lower():
                raw = self._data.get("data", {}).get("Unit", {}).get(uid, {})
                results.append({"name": name, **raw})
        return results

    def search_techs(self, query):
        q = query.lower()
        results = []
        for name, tid in self._tech_name_to_id.items():
            if q in name.lower():
                raw = self._data.get("data", {}).get("Tech", {}).get(tid, {})
                results.append({"name": name, **raw})
        return results

    def search_buildings(self, query):
        q = query.lower()
        results = []
        for name, bid in self._building_name_to_id.items():
            if q in name.lower():
                raw = self._data.get("data", {}).get("Building", {}).get(bid, {})
                results.append({"name": name, **raw})
        return results

    # --------------------------------------------------------
    # Info
    # --------------------------------------------------------

    def get_data_info(self):
        info = {
            "civs_count": len(self.get_civ_names()),
            "units_count": len(self._unit_name_to_id),
            "techs_count": len(self._tech_name_to_id),
            "buildings_count": len(self._building_name_to_id),
        }
        cache_file = self._cache_path("data.json")
        if cache_file.exists():
            t = datetime.fromtimestamp(cache_file.stat().st_mtime)
            info["last_update"] = t.strftime("%Y-%m-%d %H:%M:%S")
        return info