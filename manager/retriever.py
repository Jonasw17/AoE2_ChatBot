# -*- coding: utf-8 -*-
from fuzzywuzzy import fuzz, process
from manager.data_manager import DataManager

class DataRetriever:
    """Retrieve and query AoE2 data with proper formatting"""

    def __init__(self, fuzzy_threshold=80):
        """Initialize the retriever"""
        self.data_manager = DataManager()
        self.fuzzy_threshold = fuzzy_threshold

    def fuzzy_match_civ(self, civ_name):
        """Find closest matching civilization name"""
        all_civs = self.data_manager.get_civ_names()

        if not all_civs:
            return None

        match, score = process.extractOne(civ_name, all_civs, scorer=fuzz.ratio)
        if score >= self.fuzzy_threshold:
            return match
        return None

    def fuzzy_match_unit(self, unit_name):
        """Find closest matching unit name"""
        all_units = self.data_manager.get_unit_names()

        if not all_units:
            return None

        match, score = process.extractOne(unit_name, all_units, scorer=fuzz.ratio)
        if score >= self.fuzzy_threshold:
            return match
        return None

    def fuzzy_match_tech(self, tech_name):
        """Find closest matching technology name"""
        all_techs = self.data_manager.get_tech_names()

        if not all_techs:
            return None

        match, score = process.extractOne(tech_name, all_techs, scorer=fuzz.ratio)
        if score >= self.fuzzy_threshold:
            return match
        return None

    def fuzzy_match_building(self, building_name):
        """Find closest matching building name"""
        all_buildings = self.data_manager.get_building_names()

        if not all_buildings:
            return None

        match, score = process.extractOne(building_name, all_buildings, scorer=fuzz.ratio)
        if score >= self.fuzzy_threshold:
            return match
        return None

    def get_civ_info(self, civ_name):
        """Get complete civilization information"""
        matched_name = self.fuzzy_match_civ(civ_name)
        if not matched_name:
            return None

        civ_data = self.data_manager.get_civ_data(matched_name)
        if not civ_data:
            return None

        tech_tree = self.data_manager.load_civ_tree(matched_name)

        result = {
            'name': matched_name,
            'data': civ_data,
            'tech_tree': tech_tree
        }

        parsed = self.data_manager.get_civ_parsed_info(matched_name)
        if parsed:
            result['civ_type'] = parsed.get('civ_type', '')
            result['bonuses'] = parsed.get('bonuses', [])
            result['unique_units'] = parsed.get('unique_units', [])
            result['unique_techs'] = parsed.get('unique_techs', [])
            result['team_bonus'] = parsed.get('team_bonus', '')
        else:
            result['bonuses'] = []
            result['unique_units'] = []
            result['unique_techs'] = []
            result['team_bonus'] = ''

        return result

    def get_unit_info(self, unit_name):
        """Get unit information with parsed armor and attacks"""
        matched_name = self.fuzzy_match_unit(unit_name)
        if not matched_name:
            return None

        # get_unit_data now includes parsed armor, attacks, and counter info
        unit_data = self.data_manager.get_unit_data(matched_name)
        if not unit_data:
            return None

        return unit_data

    def get_tech_info(self, tech_name):
        """Get technology information by name"""
        matched_name = self.fuzzy_match_tech(tech_name)
        if not matched_name:
            return None

        tech_data = self.data_manager.get_tech_data(matched_name)
        if not tech_data:
            return None

        return tech_data

    def get_building_info(self, building_name):
        """Get building information by name"""
        matched_name = self.fuzzy_match_building(building_name)
        if not matched_name:
            return None

        building_data = self.data_manager.get_building_data(matched_name)
        if not building_data:
            return None

        return building_data

    def compare_civs(self, civ1_name, civ2_name):
        """Compare two civilizations"""
        civ1_data = self.get_civ_info(civ1_name)
        civ2_data = self.get_civ_info(civ2_name)

        if not civ1_data or not civ2_data:
            return None

        return {
            'civ1': civ1_data,
            'civ2': civ2_data
        }

    def get_civ_bonuses(self, civ_name):
        """Get civilization bonuses"""
        civ_data = self.get_civ_info(civ_name)
        if not civ_data:
            return None

        return {
            'civilization': civ_data['name'],
            'bonuses': civ_data.get('bonuses', []),
            'team_bonus': civ_data.get('team_bonus', ''),
            'unique_units': civ_data.get('unique_units', []),
            'unique_techs': civ_data.get('unique_techs', [])
        }

    def get_all_civs(self):
        """Get list of all civilizations"""
        return self.data_manager.get_civ_names()

    def get_all_units(self):
        """Get list of all units"""
        return self.data_manager.get_unit_names()

    def get_all_techs(self):
        """Get list of all technologies"""
        return self.data_manager.get_tech_names()

    def get_all_buildings(self):
        """Get list of all buildings"""
        return self.data_manager.get_building_names()

    def search_units(self, query):
        """Search units by partial name match"""
        return self.data_manager.search_units(query)

    def search_buildings(self, query):
        """Search buildings by partial name match"""
        return self.data_manager.search_buildings(query)

    def force_data_update(self):
        """Force update of data from GitHub"""
        self.data_manager.force_update()

    def get_data_info(self):
        """Get information about loaded data"""
        return self.data_manager.get_data_info()


if __name__ == '__main__':
    # Test retriever
    retriever = DataRetriever()

    print("=== Testing fuzzy matching ===")
    briton_match = retriever.fuzzy_match_civ('briton')
    archer_match = retriever.fuzzy_match_unit('archer')
    print(f"'briton' matches: {briton_match}")
    print(f"'archer' matches: {archer_match}")

    print("\n=== All civilizations ===")
    civs = retriever.get_all_civs()
    print(f"Found {len(civs)} civilizations")

    print("\n=== Data info ===")
    info = retriever.get_data_info()
    for key, value in info.items():
        print(f"{key}: {value}")

    print("\n=== Test: Archer unit with proper formatting ===")
    archer = retriever.get_unit_info('Archer')
    if archer:
        print(f"\nUnit: {archer['name']}")
        print(f"HP: {archer.get('HP')}")
        print(f"Attack (raw): {archer.get('Attack')}")
        print(f"Attacks (parsed): {archer.get('Attacks_Parsed')}")
        print(f"Armor (parsed): {archer.get('Armor_Parsed')}")
        print(f"Counter Info: {archer.get('Counter_Info')}")