# -*- coding: utf-8 -*-
"""
Data Retriever for AoE2 Discord Bot
Uses fuzzy matching to find units/civs/techs by approximate name.
"""
from fuzzywuzzy import fuzz, process
from manager.data_manager import DataManager


class DataRetriever:
    """High-level query interface over DataManager with fuzzy name matching."""

    def __init__(self, fuzzy_threshold=70):
        """
        Args:
            fuzzy_threshold: 0-100 minimum similarity score.
                             70 catches typos without too many false positives.
        """
        self.data_manager = DataManager()
        self.fuzzy_threshold = fuzzy_threshold

    # --------------------------------------------------------
    # Fuzzy match helpers
    # --------------------------------------------------------

    def _fuzzy(self, query, choices):
        if not choices:
            return None
        result = process.extractOne(query, choices, scorer=fuzz.token_set_ratio)
        if result and result[1] >= self.fuzzy_threshold:
            return result[0]
        return None

    def fuzzy_match_civ(self, name):
        return self._fuzzy(name, self.data_manager.get_civ_names())

    def fuzzy_match_unit(self, name):
        return self._fuzzy(name, self.data_manager.get_unit_names())

    def fuzzy_match_tech(self, name):
        return self._fuzzy(name, self.data_manager.get_tech_names())

    def fuzzy_match_building(self, name):
        return self._fuzzy(name, self.data_manager.get_building_names())

    # --------------------------------------------------------
    # Civilization
    # --------------------------------------------------------

    def get_civ_info(self, civ_name):
        """
        Returns a dict with:
          name, bonuses (list), team_bonus (str),
          unique_units (list), unique_techs (list)

        The exact key names in data.json can vary between versions of the repo.
        We try several known variants to be safe.
        """
        matched = self.fuzzy_match_civ(civ_name)
        if not matched:
            return None

        raw = self.data_manager.get_civ_data(matched)
        if not raw:
            return None

        # Debug: print all keys so we can see what the actual data looks like
        print(f"Civ data keys for {matched}: {list(raw.keys())}")
        print(f"Civ data sample: {str(raw)[:300]}")

        # Bonuses: try multiple known key names
        bonuses = (
                raw.get("bons")
                or raw.get("bonuses")
                or raw.get("civBonuses")
                or raw.get("civ_bonuses")
                or []
        )
        if not isinstance(bonuses, list):
            bonuses = []

        # Team bonus: try multiple known key names
        team_bonus = (
                raw.get("team_bonus")
                or raw.get("teamBonus")
                or raw.get("team")
                or ""
        )
        if not isinstance(team_bonus, str):
            team_bonus = str(team_bonus) if team_bonus else ""

        # Unique units and techs: nested under "unique" dict
        unique = raw.get("unique", {})
        if not isinstance(unique, dict):
            unique = {}

        unique_units = unique.get("units", [])
        unique_techs = unique.get("techs", [])

        if not isinstance(unique_units, list):
            unique_units = []
        if not isinstance(unique_techs, list):
            unique_techs = []

        return {
            "name": matched,
            "bonuses": bonuses,
            "team_bonus": team_bonus,
            "unique_units": unique_units,
            "unique_techs": unique_techs,
            "_raw_keys": list(raw.keys()),
        }

    def compare_civs(self, civ1, civ2):
        d1 = self.get_civ_info(civ1)
        d2 = self.get_civ_info(civ2)
        if not d1 or not d2:
            return None
        return {"civ1": d1, "civ2": d2}

    def get_all_civs(self):
        return self.data_manager.get_civ_names()

    # --------------------------------------------------------
    # Units
    # --------------------------------------------------------

    def get_unit_info(self, unit_name):
        matched = self.fuzzy_match_unit(unit_name)
        if not matched:
            return None
        return self.data_manager.get_unit_data(matched)

    def get_all_units(self):
        return self.data_manager.get_unit_names()

    # --------------------------------------------------------
    # Technologies
    # --------------------------------------------------------

    def get_tech_info(self, tech_name):
        matched = self.fuzzy_match_tech(tech_name)
        if not matched:
            return None
        return self.data_manager.get_tech_data(matched)

    def get_all_techs(self):
        return self.data_manager.get_tech_names()

    # --------------------------------------------------------
    # Buildings
    # --------------------------------------------------------

    def get_building_info(self, building_name):
        matched = self.fuzzy_match_building(building_name)
        if not matched:
            return None
        return self.data_manager.get_building_data(matched)

    def get_all_buildings(self):
        return self.data_manager.get_building_names()

    # --------------------------------------------------------
    # Admin
    # --------------------------------------------------------

    def force_data_update(self):
        self.data_manager.force_update()

    def get_data_info(self):
        return self.data_manager.get_data_info()