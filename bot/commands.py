"""
Discord bot commands for AoE2 information - Fixed Formatting
"""
import discord
from discord.ext import commands
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manager.retriever import DataRetriever
from llm.llm_handler import LLMHandler

def _cost_str(cost):
    """Format {'Food': 60, 'Gold': 75} into '60F, 75G'."""
    if isinstance(cost, dict):
        parts = []
        if cost.get('Food'):
            parts.append(f"{cost['Food']}F")
        if cost.get('Wood'):
            parts.append(f"{cost['Wood']}W")
        if cost.get('Gold'):
            parts.append(f"{cost['Gold']}G")
        if cost.get('Stone'):
            parts.append(f"{cost['Stone']}S")
        return ", ".join(parts) if parts else "0"
    return str(cost)


def _armor_str(armor_dict):
    """Format armor dictionary into readable string."""
    if not isinstance(armor_dict, dict):
        return str(armor_dict)

    melee = armor_dict.get('Melee', 0)
    pierce = armor_dict.get('Pierce', 0)

    # Start with base armor
    result = f"{melee}/{pierce}"

    # Add bonus armor classes if any
    bonus_armors = []
    for key, value in armor_dict.items():
        if key not in ['Melee', 'Pierce'] and value > 0:
            bonus_armors.append(f"+{value} {key}")

    if bonus_armors:
        result += " (" + ", ".join(bonus_armors) + ")"

    return result


def _attack_str(attacks_dict, base_attack=None):
    """Format attack dictionary into readable string."""
    if not isinstance(attacks_dict, dict):
        if base_attack:
            return str(base_attack)
        return str(attacks_dict)

    parts = []

    # Base attack first
    if base_attack:
        parts.append(str(base_attack))
    elif 'Base' in attacks_dict:
        parts.append(str(attacks_dict['Base']))

    # Add bonus attacks
    for key, value in attacks_dict.items():
        if key != 'Base' and value > 0:
            parts.append(f"+{value} {key}")

    return ", ".join(parts) if parts else "0"


class AoE2Commands(commands.Cog):
    """AoE2 information commands"""

    def __init__(self, bot):
        self.bot = bot
        self.retriever = DataRetriever()
        self.llm_handler = LLMHandler()

    # --------------------------------------------------------
    # ?civ
    # --------------------------------------------------------

    @commands.command(name="civ")
    async def civ_info(self, ctx, *, civ_name: str):
        """Get information about a civilization.  Usage: ?civ Britons"""
        try:
            civ = self.retriever.get_civ_info(civ_name)
            if not civ:
                await ctx.send(
                    f"Could not find civilization: {civ_name}\n"
                    f"Use `?civs` to see all available civs."
                )
                return

            embed = discord.Embed(title=civ["name"], color=discord.Color.gold())

            civ_type = civ.get('civ_type', '')
            if civ_type:
                embed.description = civ_type

            bonuses = civ.get("bonuses", [])
            if bonuses:
                bonus_text = "\n".join(f"• {b}" for b in bonuses)
                if len(bonus_text) > 1024:
                    bonus_text = bonus_text[:1020] + "..."
                embed.add_field(
                    name="Civilization Bonuses",
                    value=bonus_text,
                    inline=False,
                )

            tb = civ.get("team_bonus", "")
            if tb:
                embed.add_field(name="Team Bonus", value=tb, inline=False)

            uu = civ.get("unique_units", [])
            if uu:
                embed.add_field(name="Unique Units", value=", ".join(uu), inline=True)

            ut = civ.get("unique_techs", [])
            if ut:
                embed.add_field(name="Unique Techs", value=", ".join(ut), inline=True)

            embed.set_footer(text="Use ?compare <civ1> <civ2> to compare")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilization info: {e}")
            print(f"Error in civ_info: {e}")

    # --------------------------------------------------------
    # ?civs
    # --------------------------------------------------------

    @commands.command(name="civs")
    async def list_civs(self, ctx):
        """List all available civilizations.  Usage: ?civs"""
        try:
            civs = self.retriever.get_all_civs()
            if not civs:
                await ctx.send("No civilizations found.")
                return

            chunk_size = 24
            chunks = [civs[i:i + chunk_size] for i in range(0, len(civs), chunk_size)]
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Civilizations ({i + 1}/{len(chunks)})",
                    description=", ".join(chunk),
                    color=discord.Color.blue(),
                )
                embed.set_footer(text=f"Total: {len(civs)} civilizations | Use ?civ <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilizations: {e}")

    # --------------------------------------------------------
    # ?unit - Enhanced with proper formatting
    # --------------------------------------------------------

    @commands.command(name="unit")
    async def unit_info(self, ctx, *, unit_name: str):
        """Get detailed unit stats. Usage: ?unit Archer"""
        try:
            unit = self.retriever.get_unit_info(unit_name)
            if not unit:
                await ctx.send(
                    f"Could not find unit: {unit_name}\n"
                    f"Use `?units` to browse all units."
                )
                return

            embed = discord.Embed(
                title=unit["name"],
                color=discord.Color.red()
            )

            # Build description line: prefer the game's own flavour text.
            # Fall back to the armor-class classification if it is not available.
            desc_info    = unit.get('Description_Info', {})
            counter_info = unit.get('Counter_Info', {})
            classification = counter_info.get('classification', '')

            flavour = desc_info.get('description', '')
            if flavour:
                embed.description = f"*{flavour}*"
            elif classification and classification != 'Other':
                embed.description = f"*{classification} Unit*"

            # === STATS SECTION ===
            stats_lines = []

            # HP
            hp = unit.get("HP")
            if hp is not None:
                stats_lines.append(f"**HP:** {hp}")

            # Attack (with bonuses)
            base_attack = unit.get("Attack")
            attacks_parsed = unit.get("Attacks_Parsed", {})
            if base_attack is not None or attacks_parsed:
                attack_str = _attack_str(attacks_parsed, base_attack)
                stats_lines.append(f"**Attack:** {attack_str}")

            # Armor (with bonuses)
            armor_parsed = unit.get("Armor_Parsed", {})
            if armor_parsed:
                armor_str = _armor_str(armor_parsed)
                stats_lines.append(f"**Armor:** {armor_str}")

            # Range
            rng = unit.get("Range")
            if rng is not None and rng > 0:
                stats_lines.append(f"**Range:** {rng}")

            # Line of Sight
            los = unit.get("LineOfSight") or unit.get("LOS")
            if los is not None:
                stats_lines.append(f"**Line of Sight:** {los}")

            # Speed
            speed = unit.get("Speed")
            if speed is not None:
                stats_lines.append(f"**Speed:** {speed}")

            # Attack Rate / Reload Time
            rate = unit.get("ReloadTime") or unit.get("AttackRate") or unit.get("Rate of Fire")
            if rate is not None:
                stats_lines.append(f"**Attack Rate:** {rate}s")

            # Training Time
            train_time = unit.get("TrainTime")
            if train_time is not None:
                stats_lines.append(f"**Train Time:** {train_time}s")

            if stats_lines:
                embed.add_field(
                    name="Stats",
                    value="\n".join(stats_lines),
                    inline=False
                )

            # === COST ===
            cost = unit.get("Cost")
            if cost:
                embed.add_field(name="Cost", value=_cost_str(cost), inline=True)

            # === COUNTERS SECTION ===
            # Prefer description-based data (straight from the game text).
            # Fall back to the armor-class heuristic when description data is absent.
            desc_info = unit.get('Description_Info', {})
            counter_info = unit.get('Counter_Info', {})

            # Get strong vs and weak vs from both sources, prefer description
            strong_vs = desc_info.get('strong_vs', [])
            weak_vs = desc_info.get('weak_vs', [])

            # If description doesn't have counter info, use heuristic
            if not strong_vs:
                strong_vs = counter_info.get('strong_against', [])
            if not weak_vs:
                weak_vs = counter_info.get('countered_by', [])

            # Bonus damage from armor-class parsing (separate from "strong vs")
            bonus_dmg = counter_info.get('bonus_damage_vs', [])

            # Display strengths (either from description or bonus damage)
            if strong_vs:
                embed.add_field(
                    name="Strong Against",
                    value=", ".join(strong_vs),
                    inline=False
                )
            elif bonus_dmg:
                # Only show bonus damage if we don't have description-based strengths
                embed.add_field(
                    name="Bonus Damage",
                    value=", ".join(bonus_dmg),
                    inline=False
                )

            # Display weaknesses
            if weak_vs:
                embed.add_field(
                    name="Weak Against",
                    value=", ".join(weak_vs),
                    inline=False
                )

            # === ATTACK BREAKDOWN (if complex) ===
            if attacks_parsed and len(attacks_parsed) > 2:
                attack_details = []
                for atk_type, dmg in attacks_parsed.items():
                    if dmg > 0:
                        attack_details.append(f"{atk_type}: {dmg}")

                if attack_details:
                    embed.add_field(
                        name="Attack Breakdown",
                        value="\n".join(attack_details),
                        inline=True
                    )

            # === ARMOR BREAKDOWN (if complex) ===
            if armor_parsed and len(armor_parsed) > 2:
                armor_details = []
                for armor_type, value in armor_parsed.items():
                    if value > 0:
                        armor_details.append(f"{armor_type}: {value}")

                if armor_details:
                    embed.add_field(
                        name="Armor Breakdown",
                        value="\n".join(armor_details),
                        inline=True
                    )

            if not embed.fields:
                embed.description = "Detailed stats not available for this unit."

            embed.set_footer(text="Data from aoe2techtree.net | Use ?units to see all units")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving unit info: {e}")
            print(f"Error in unit_info: {e}")
            import traceback
            traceback.print_exc()

    # --------------------------------------------------------
    # ?units
    # --------------------------------------------------------

    @commands.command(name="units")
    async def list_units(self, ctx):
        """List all units.  Usage: ?units"""
        try:
            units = self.retriever.get_all_units()
            if not units:
                await ctx.send("No units found.")
                return

            chunk_size = 30
            chunks = [units[i:i + chunk_size] for i in range(0, len(units), chunk_size)]
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Units ({i + 1}/{len(chunks)})",
                    description=", ".join(chunk),
                    color=discord.Color.green(),
                )
                embed.set_footer(text=f"Total: {len(units)} units | Use ?unit <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving units: {e}")

    # --------------------------------------------------------
    # ?counter - Show what counters a unit
    # --------------------------------------------------------

    @commands.command(name="counter")
    async def counter_info(self, ctx, *, unit_name: str):
        """Find what counters a specific unit.  Usage: ?counter Knight"""
        try:
            unit = self.retriever.get_unit_info(unit_name)
            if not unit:
                await ctx.send(
                    f"Could not find unit: {unit_name}\n"
                    f"Use `?units` to browse all units."
                )
                return

            desc_info    = unit.get('Description_Info', {})
            counter_info = unit.get('Counter_Info', {})

            embed = discord.Embed(
                title=f"Counters for {unit['name']}",
                color=discord.Color.orange()
            )

            classification = counter_info.get('classification', 'Other')
            if classification != 'Other':
                embed.description = f"*{classification} Unit*"

            # Prefer description-based counters (from game text)
            weak_vs = desc_info.get('weak_vs', [])
            strong_vs = desc_info.get('strong_vs', [])

            # If description doesn't have counter info, use heuristic
            if not weak_vs:
                weak_vs = counter_info.get('countered_by', [])
            if not strong_vs:
                strong_vs = counter_info.get('strong_against', [])

            bonus_dmg = counter_info.get('bonus_damage_vs', [])

            # Countered By
            if weak_vs:
                embed.add_field(
                    name="Countered By",
                    value=", ".join(weak_vs),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Countered By",
                    value="No counter data available",
                    inline=False
                )

            # Effective Against
            if strong_vs:
                embed.add_field(
                    name="Effective Against",
                    value=", ".join(strong_vs),
                    inline=False
                )
            elif bonus_dmg:
                # Only show bonus damage if we don't have description-based strengths
                embed.add_field(
                    name="Bonus Damage",
                    value=", ".join(bonus_dmg),
                    inline=False
                )

            embed.set_footer(text="Use ?unit for full stats | Counter data from game descriptions")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving counter info: {e}")
            print(f"Error in counter_info: {e}")

    # --------------------------------------------------------
    # ?tech
    # --------------------------------------------------------

    @commands.command(name="tech")
    async def tech_info(self, ctx, *, tech_name: str):
        """Get technology information.  Usage: ?tech Ballistics"""
        try:
            tech = self.retriever.get_tech_info(tech_name)
            if not tech:
                await ctx.send(
                    f"Could not find technology: **{tech_name}**\n"
                    f"Use `?techs` to browse all technologies."
                )
                return

            embed = discord.Embed(title=tech["name"], color=discord.Color.purple())

            # Description from strings.json
            desc_info = tech.get('Description_Info', {})
            flavour = desc_info.get('description', '')
            if flavour:
                embed.description = f"*{flavour}*"

            # Effect / what it upgrades (from the Upgrades: line in description)
            effect = desc_info.get('effect', '')
            if effect:
                # Trim long upgrade lists to keep the embed clean
                if len(effect) > 200:
                    effect = effect[:197] + '...'
                embed.add_field(name="Effect", value=effect, inline=False)

            # Cost
            cost = tech.get("Cost")
            if cost:
                embed.add_field(name="Cost", value=_cost_str(cost), inline=True)

            # Research time
            research_time = tech.get("ResearchTime") or tech.get("ResearchDuration")
            if research_time is not None:
                embed.add_field(name="Research Time", value=f"{research_time}s", inline=True)

            # Age / where it is researched
            age = tech.get("Age") or tech.get("RequiredAge")
            if age:
                age_names = {1: "Dark Age", 2: "Feudal Age", 3: "Castle Age", 4: "Imperial Age"}
                embed.add_field(name="Age", value=age_names.get(age, str(age)), inline=True)

            embed.set_footer(text="Use ?techs to browse all technologies")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving technology info: {e}")
            print(f"Error in tech_info: {e}")

    # --------------------------------------------------------
    # ?techs
    # --------------------------------------------------------

    @commands.command(name="techs")
    async def list_techs(self, ctx):
        """List all technologies.  Usage: ?techs"""
        try:
            techs = self.retriever.get_all_techs()
            if not techs:
                await ctx.send("No technologies found.")
                return

            chunk_size = 30
            chunks = [techs[i:i + chunk_size] for i in range(0, len(techs), chunk_size)]
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Technologies ({i + 1}/{len(chunks)})",
                    description=", ".join(chunk),
                    color=discord.Color.purple(),
                )
                embed.set_footer(text=f"Total: {len(techs)} technologies | Use ?tech <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving technologies: {e}")

    # --------------------------------------------------------
    # ?building
    # --------------------------------------------------------

    @commands.command(name="building")
    async def building_info(self, ctx, *, building_name: str):
        """Get information about a building.  Usage: ?building Castle"""
        try:
            building = self.retriever.get_building_info(building_name)
            if not building:
                await ctx.send(
                    f"Could not find building: **{building_name}**\n"
                    f"Use `?buildings` to browse all buildings."
                )
                return

            embed = discord.Embed(
                title=building["name"],
                color=discord.Color.dark_gold()
            )

            # Description from strings.json
            desc_info = building.get('Description_Info', {})
            flavour = desc_info.get('description', '')
            if flavour:
                embed.description = f"*{flavour}*"

            # Stats
            stats_lines = []

            hp = building.get("HP")
            if hp is not None:
                stats_lines.append(f"**HP:** {hp}")

            armor_parsed = building.get("Armor_Parsed", {})
            if armor_parsed:
                melee  = armor_parsed.get('Melee', 0)
                pierce = armor_parsed.get('Pierce', 0)
                stats_lines.append(f"**Armor:** {melee}/{pierce} (melee/pierce)")

            los = building.get("LineOfSight") or building.get("LOS")
            if los is not None:
                stats_lines.append(f"**Line of Sight:** {los}")

            garrison = building.get("GarrisonCapacity") or building.get("Garrison")
            if garrison:
                stats_lines.append(f"**Garrison:** {garrison}")

            population = building.get("Population") or building.get("PopulationCapacity")
            if population:
                stats_lines.append(f"**Population:** +{population}")

            if stats_lines:
                embed.add_field(name="Stats", value="\n".join(stats_lines), inline=False)

            # Cost
            cost = building.get("Cost")
            if cost:
                embed.add_field(name="Cost", value=_cost_str(cost), inline=True)

            # Build time
            build_time = building.get("TrainTime") or building.get("BuildTime")
            if build_time is not None:
                embed.add_field(name="Build Time", value=f"{build_time}s", inline=True)

            # Attack (towers etc.)
            attack = building.get("Attack")
            if attack:
                rng = building.get("Range")
                atk_str = str(attack)
                if rng:
                    atk_str += f" (range {rng})"
                embed.add_field(name="Attack", value=atk_str, inline=True)

            # Strong / weak from description
            strong_vs = desc_info.get('strong_vs', [])
            weak_vs   = desc_info.get('weak_vs', [])

            if strong_vs:
                embed.add_field(name="Strong Against", value=", ".join(strong_vs), inline=False)
            if weak_vs:
                embed.add_field(name="Weak Against", value=", ".join(weak_vs), inline=False)

            embed.set_footer(text="Use ?buildings to see all buildings")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving building info: {e}")
            print(f"Error in building_info: {e}")

    # --------------------------------------------------------
    # ?buildings
    # --------------------------------------------------------

    @commands.command(name="buildings")
    async def list_buildings(self, ctx):
        """List all buildings.  Usage: ?buildings"""
        try:
            buildings = self.retriever.get_all_buildings()
            if not buildings:
                await ctx.send("No buildings found.")
                return

            chunk_size = 30
            chunks = [buildings[i:i + chunk_size] for i in range(0, len(buildings), chunk_size)]
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Buildings ({i + 1}/{len(chunks)})",
                    description=", ".join(chunk),
                    color=discord.Color.dark_gold(),
                )
                embed.set_footer(text=f"Total: {len(buildings)} buildings | Use ?building <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving buildings: {e}")

    # --------------------------------------------------------
    # ?compare
    # --------------------------------------------------------

    @commands.command(name="compare")
    async def compare_civs(self, ctx, civ1: str, *, civ2: str):
        """Compare two civilizations.  Usage: ?compare Britons Franks"""
        try:
            comp = self.retriever.compare_civs(civ1, civ2)
            if not comp:
                await ctx.send(
                    "Could not find one or both civilizations. "
                    "Use `?civs` to see all names."
                )
                return

            c1, c2 = comp["civ1"], comp["civ2"]
            embed = discord.Embed(
                title=f"{c1['name']} vs {c2['name']}",
                color=discord.Color.orange(),
            )

            def bonus_block(civ_data):
                lines = []
                bonuses = civ_data.get("bonuses", [])
                for b in bonuses[:5]:
                    lines.append(f"• {b}")

                tb = civ_data.get("team_bonus", "")
                if tb:
                    lines.append(f"**Team:** {tb}")

                uu = civ_data.get("unique_units", [])
                if uu:
                    lines.append(f"**Units:** {', '.join(uu)}")

                ut = civ_data.get("unique_techs", [])
                if ut:
                    lines.append(f"**Techs:** {', '.join(ut)}")

                result = "\n".join(lines)
                if len(result) > 1024:
                    result = result[:1020] + "..."
                return result or "No data"

            embed.add_field(name=c1["name"], value=bonus_block(c1), inline=True)
            embed.add_field(name=c2["name"], value=bonus_block(c2), inline=True)
            embed.set_footer(text="Use ?civ <name> for full details")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error comparing civilizations: {e}")

    # --------------------------------------------------------
    # ?datainfo
    # --------------------------------------------------------

    @commands.command(name="datainfo")
    async def data_info(self, ctx):
        """Show loaded data statistics.  Usage: ?datainfo"""
        try:
            info = self.retriever.get_data_info()
            embed = discord.Embed(title="AoE2 Data Info", color=discord.Color.blue())
            embed.add_field(name="Civilizations", value=info.get("civs_count", 0), inline=True)
            embed.add_field(name="Units", value=info.get("units_count", 0), inline=True)
            embed.add_field(name="Technologies", value=info.get("techs_count", 0), inline=True)
            embed.add_field(name="Buildings", value=info.get("buildings_count", 0), inline=True)
            if "last_update" in info:
                embed.add_field(name="Cache Updated", value=info["last_update"], inline=False)
            embed.set_footer(text="Data source: github.com/SiegeEngineers/aoe2techtree")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving data info: {e}")

    # --------------------------------------------------------
    # ?updatedata (admin only)
    # --------------------------------------------------------

    @commands.command(name="updatedata")
    @commands.has_permissions(administrator=True)
    async def force_update(self, ctx):
        """Force refresh data from GitHub. Admin only.  Usage: ?updatedata"""
        try:
            await ctx.send("Checking for updates from GitHub, please wait...")
            self.retriever.force_data_update()
            info = self.retriever.get_data_info()
            await ctx.send(
                f"Data updated successfully!\n"
                f"Civs: {info['civs_count']} | "
                f"Units: {info['units_count']} | "
                f"Techs: {info['techs_count']} | "
                f"Buildings: {info['buildings_count']}"
            )
        except Exception as e:
            await ctx.send(f"Error updating data: {e}")

    # --------------------------------------------------------
    # ?checkupdates
    # --------------------------------------------------------

    @commands.command(name="checkupdates")
    async def check_updates(self, ctx):
        """Check if updates are available on GitHub.  Usage: ?checkupdates"""
        try:
            await ctx.send("Checking GitHub for updates...")

            has_updates = self.retriever.data_manager._check_for_updates()

            if has_updates:
                await ctx.send(
                    "Updates are available on GitHub!\n"
                    "Use `?updatedata` (admin only) to download the latest data."
                )
            else:
                await ctx.send(
                    "Your data is up to date!\n"
                    f"Last update: {self.retriever.get_data_info().get('last_update', 'Unknown')}"
                )
        except Exception as e:
            await ctx.send(f"Error checking for updates: {e}")


    # --------------------------------------------------------
    # ?commands - AoE2 command summary
    # --------------------------------------------------------

    @commands.command(name="commands")
    async def list_commands(self, ctx):
        """Show all AoE2 bot commands.  Usage: ?commands"""
        embed = discord.Embed(
            title="AoE2 Bot Commands",
            description="All commands use the `?` prefix.",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Civilizations",
            value=(
                "`?civs` - List all civilizations\n"
                "`?civ <name>` - Details & bonuses for a civ\n"
                "`?compare <civ1> <civ2>` - Side-by-side comparison"
            ),
            inline=False
        )
        embed.add_field(
            name="Units",
            value=(
                "`?units` - List all units\n"
                "`?unit <name>` - Stats, cost, counters\n"
                "`?counter <name>` - What counters this unit"
            ),
            inline=False
        )
        embed.add_field(
            name="Technologies",
            value=(
                "`?techs` - List all technologies\n"
                "`?tech <name>` - Cost, research time, effect"
            ),
            inline=False
        )
        embed.add_field(
            name="Buildings",
            value=(
                "`?buildings` - List all buildings\n"
                "`?building <name>` - HP, armor, cost, description"
            ),
            inline=False
        )
        embed.add_field(
            name="Data & Admin",
            value=(
                "`?datainfo` - Show data cache statistics\n"
                "`?checkupdates` - Check GitHub for new data\n"
                "`?updatedata` - Force refresh (admin only)"
            ),
            inline=False
        )
        embed.set_footer(text="Data from github.com/SiegeEngineers/aoe2techtree")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AoE2Commands(bot))