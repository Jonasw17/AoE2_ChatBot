# -*- coding: utf-8 -*-
"""
Discord bot commands for AoE2 information
"""
import discord
from discord.ext import commands
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manager.retriever import DataRetriever
from llm.llm_handler import LLMHandler

def _cost_str(cost):
    """Format {'Food': 60, 'Gold': 75} into '60 Food, 75 Gold'."""
    if isinstance(cost, dict):
        return ", ".join(f"{v} {k}" for k, v in cost.items() if v)
    return str(cost)


def _armor_str(armor):
    """Format {'Melee': 2, 'Pierce': 3} into '2/3 (Melee/Pierce)'."""
    if isinstance(armor, dict):
        melee = armor.get("Melee", armor.get("melee", 0))
        pierce = armor.get("Pierce", armor.get("pierce", 0))
        return f"{melee}/{pierce} (Melee/Pierce)"
    return str(armor)


class AoE2Commands(commands.Cog):
    """AoE2 information commands"""

    def __init__(self, bot):
        self.bot = bot
        self.retriever = DataRetriever()
        self.llm_handler = LLMHandler()  # Add this line

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

            bonuses = civ.get("bonuses", [])
            if bonuses:
                embed.add_field(
                    name="Civilization Bonuses",
                    value="\n".join(f"- {b}" for b in bonuses),
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Civilization Bonuses",
                    value="No bonus data found. Check console and run ?debugciv " + civ["name"],
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

            embed.set_footer(text="Data: aoe2techtree.net | Use ?compare <civ1> <civ2> to compare")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilization info: {e}")
            print(f"Error in civ_info: {e}")

    # --------------------------------------------------------
    # ?debugciv  -- dumps raw civ data so we can see the actual keys
    # --------------------------------------------------------

    @commands.command(name="debugciv")
    async def debug_civ(self, ctx, *, civ_name: str):
        """Dump raw civ data for debugging.  Usage: ?debugciv Britons"""
        try:
            raw = self.retriever.data_manager.get_civ_data(civ_name)
            if not raw:
                await ctx.send(f"Could not find civ: {civ_name}")
                return
            keys = list(raw.keys())
            sample = str(raw)[:800]
            await ctx.send(f"Keys: {keys}\n\nSample:\n```\n{sample}\n```")
        except Exception as e:
            await ctx.send(f"Error: {e}")

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
                embed.set_footer(text=f"Total: {len(civs)} civilizations | Use ?civ <n> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilizations: {e}")

    # --------------------------------------------------------
    # ?unit
    # --------------------------------------------------------

    @commands.command(name="unit")
    async def unit_info(self, ctx, *, unit_name: str):
        """Get unit stats.  Usage: ?unit Knight"""
        try:
            unit = self.retriever.get_unit_info(unit_name)
            if not unit:
                await ctx.send(
                    f"Could not find unit: {unit_name}\n"
                    f"Use `?units` to browse all units."
                )
                return

            embed = discord.Embed(title=unit["name"], color=discord.Color.red())

            cost = unit.get("Cost")
            if cost:
                embed.add_field(name="Cost", value=_cost_str(cost), inline=True)

            hp = unit.get("HP")
            if hp is not None:
                embed.add_field(name="HP", value=str(hp), inline=True)

            attack = unit.get("Attack")
            if attack is not None:
                embed.add_field(name="Attack", value=str(attack), inline=True)

            armor = unit.get("Armor")
            if armor is not None:
                embed.add_field(name="Armor", value=_armor_str(armor), inline=True)

            speed = unit.get("Speed")
            if speed is not None:
                embed.add_field(name="Speed", value=str(speed), inline=True)

            rng = unit.get("Range")
            if rng is not None:
                embed.add_field(name="Range", value=str(rng), inline=True)

            rate = unit.get("AttackRate") or unit.get("Rate of Fire")
            if rate is not None:
                embed.add_field(name="Attack Rate", value=str(rate), inline=True)

            los = unit.get("LineOfSight")
            if los is not None:
                embed.add_field(name="Line of Sight", value=str(los), inline=True)

            if not embed.fields:
                embed.description = "Detailed stats not available for this unit."

            embed.set_footer(text="Use ?units to see all units")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving unit info: {e}")
            print(f"Error in unit_info: {e}")

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
                embed.set_footer(text=f"Total: {len(units)} units | Use ?unit <n> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving units: {e}")

    # --------------------------------------------------------
    # ?tech
    # --------------------------------------------------------

    @commands.command(name="tech")
    async def tech_info(self, ctx, *, tech_name: str):
        """Get technology information.  Usage: ?tech Ballistics"""
        try:
            tech = self.retriever.get_tech_info(tech_name)
            if not tech:
                await ctx.send(f"Could not find technology: {tech_name}")
                return

            embed = discord.Embed(title=tech["name"], color=discord.Color.purple())

            cost = tech.get("Cost")
            if cost:
                embed.add_field(name="Cost", value=_cost_str(cost), inline=True)

            research_time = tech.get("ResearchTime") or tech.get("ResearchDuration")
            if research_time is not None:
                embed.add_field(name="Research Time", value=f"{research_time}s", inline=True)

            embed.set_footer(text="Use ?techs to browse all technologies")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving technology info: {e}")

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
                bonuses = civ_data.get("bonuses", [])
                tb = civ_data.get("team_bonus", "")
                uu = civ_data.get("unique_units", [])
                ut = civ_data.get("unique_techs", [])
                lines = [f"- {b}" for b in bonuses[:5]]
                if tb:
                    lines.append(f"Team bonus: {tb}")
                if uu:
                    lines.append(f"Unique units: {', '.join(uu)}")
                if ut:
                    lines.append(f"Unique techs: {', '.join(ut)}")
                return "\n".join(lines) or "No data"

            embed.add_field(name=c1["name"], value=bonus_block(c1), inline=True)
            embed.add_field(name=c2["name"], value=bonus_block(c2), inline=True)
            embed.set_footer(text="Use ?civ <n> for full details")
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
    # ?updatedata  (admin only)
    # --------------------------------------------------------

    @commands.command(name="updatedata")
    @commands.has_permissions(administrator=True)
    async def force_update(self, ctx):
        """Force refresh data from GitHub. Admin only.  Usage: ?updatedata"""
        try:
            await ctx.send("Updating data from GitHub, please wait...")
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

    @commands.command(name="aoe2")
    async def ask_aoe2(self, ctx, *, question: str):
        """Ask any AoE2 question in natural language. Usage: ?aoe2 What are the Britons bonuses?"""
        try:
            msg = await ctx.send("Thinking...")

            question_lower = question.lower()
            response = None

            # Check for civilization queries
            if any(word in question_lower for word in ['civ', 'civilization', 'bonus', 'bonuses', 'team bonus']):
                all_civs = self.retriever.get_all_civs()
                for civ in all_civs:
                    if civ.lower() in question_lower:
                        civ_info = self.retriever.get_civ_info(civ)
                        if civ_info:
                            response = f"**{civ}**\n\n"

                            bonuses = civ_info.get('bonuses', [])
                            if bonuses:
                                response += "**Civilization Bonuses:**\n"
                                for bonus in bonuses:
                                    response += f"- {bonus}\n"

                            team_bonus = civ_info.get('team_bonus', '')
                            if team_bonus:
                                response += f"\n**Team Bonus:** {team_bonus}\n"

                            unique_units = civ_info.get('unique_units', [])
                            if unique_units:
                                response += f"\n**Unique Units:** {', '.join(unique_units)}\n"

                            unique_techs = civ_info.get('unique_techs', [])
                            if unique_techs:
                                response += f"\n**Unique Techs:** {', '.join(unique_techs)}"
                        break

            # Check for unit queries
            elif any(word in question_lower for word in ['unit', 'stats', 'cost', 'hp', 'health', 'attack', 'armor']):
                all_units = self.retriever.get_all_units()
                for unit in all_units:
                    if unit.lower() in question_lower:
                        unit_info = self.retriever.get_unit_info(unit)
                        if unit_info:
                            response = f"**{unit}**\n\n"

                            if 'Cost' in unit_info:
                                response += f"**Cost:** {_cost_str(unit_info['Cost'])}\n"
                            if 'HP' in unit_info:
                                response += f"**HP:** {unit_info['HP']}\n"
                            if 'Attack' in unit_info:
                                response += f"**Attack:** {unit_info['Attack']}\n"
                            if 'Armours' in unit_info or 'MeleeArmor' in unit_info:
                                if 'MeleeArmor' in unit_info and 'PierceArmor' in unit_info:
                                    response += f"**Armor:** {unit_info['MeleeArmor']}/{unit_info['PierceArmor']} (Melee/Pierce)\n"
                            if 'Speed' in unit_info:
                                response += f"**Speed:** {unit_info['Speed']}\n"
                            if 'Range' in unit_info and unit_info['Range'] > 0:
                                response += f"**Range:** {unit_info['Range']}\n"

                            response += f"\nUse `?unit {unit}` for detailed stats"
                        break

            # Check for comparison queries
            elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference']):
                all_civs = self.retriever.get_all_civs()
                found_civs = []
                for civ in all_civs:
                    if civ.lower() in question_lower:
                        found_civs.append(civ)

                if len(found_civs) >= 2:
                    comparison = self.retriever.compare_civs(found_civs[0], found_civs[1])
                    if comparison:
                        civ1 = comparison['civ1']
                        civ2 = comparison['civ2']

                        response = f"**{civ1['name']} vs {civ2['name']}**\n\n"
                        response += f"**{civ1['name']} Bonuses:**\n"
                        for bonus in civ1.get('bonuses', [])[:5]:
                            response += f"- {bonus}\n"

                        response += f"\n**{civ2['name']} Bonuses:**\n"
                        for bonus in civ2.get('bonuses', [])[:5]:
                            response += f"- {bonus}\n"

                        response += f"\nUse `?compare {found_civs[0]} {found_civs[1]}` for full comparison"

            # Counter queries - explain we don't have this yet
            elif 'counter' in question_lower:
                response = (
                    "Counter information isn't available yet in natural language queries.\n\n"
                    "Try using the specific commands:\n"
                    "- `?unit <name>` - See unit stats\n"
                    "- `?civ <name>` - See civ bonuses\n"
                    "- `?civs` - List all civilizations\n"
                    "- `?units` - List all units"
                )

            # Generic search - try to find any civ or unit mentioned
            else:
                all_civs = self.retriever.get_all_civs()
                all_units = self.retriever.get_all_units()

                for civ in all_civs:
                    if civ.lower() in question_lower:
                        civ_info = self.retriever.get_civ_info(civ)
                        if civ_info:
                            response = f"**{civ}**\n\n"
                            bonuses = civ_info.get('bonuses', [])[:5]
                            if bonuses:
                                response += "**Bonuses:**\n"
                                for bonus in bonuses:
                                    response += f"- {bonus}\n"
                            response += f"\nUse `?civ {civ}` for complete info"
                        break

                if not response:
                    for unit in all_units:
                        if unit.lower() in question_lower:
                            unit_info = self.retriever.get_unit_info(unit)
                            if unit_info:
                                response = f"**{unit}**\n\n"
                                if 'Cost' in unit_info:
                                    response += f"Cost: {_cost_str(unit_info['Cost'])}\n"
                                if 'HP' in unit_info:
                                    response += f"HP: {unit_info['HP']}\n"
                                response += f"\nUse `?unit {unit}` for full stats"
                            break

            # Send response
            await msg.delete()
            if response:
                # Split if too long
                if len(response) > 1900:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(response)
            else:
                await ctx.send(
                    "I couldn't understand that question. Try:\n"
                    "- `?civ britons` - Civilization info\n"
                    "- `?unit knight` - Unit stats\n"
                    "- `?compare britons franks` - Compare civs\n"
                    "- `?civs` - List all civilizations\n"
                    "- `?units` - List all units"
                )

        except Exception as e:
            await ctx.send(f"Error: {e}")
            print(f"Error in ask_aoe2: {e}")

async def setup(bot):
    await bot.add_cog(AoE2Commands(bot))