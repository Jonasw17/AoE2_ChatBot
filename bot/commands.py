"""
Discord bot commands for AoE2 information
"""
import discord
from discord.ext import commands
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from manager.data_manager import DataManager
from manager.retriever import DataRetriever

class AoE2Commands(commands.Cog):
    """AoE2 information commands"""

    def __init__(self, bot):
        self.bot = bot
        self.retriever = DataRetriever()

    @commands.command(name='civ')
    async def civ_info(self, ctx, *, civ_name: str):
        """Get information about a civilization
        
        Usage: ?civ <civilization name>
        Example: ?civ Britons
        """
        try:
            # Get civ info
            civ_data = self.retriever.get_civ_info(civ_name)

            if not civ_data:
                await ctx.send(f"Could not find civilization: {civ_name}")
                return

            # Create embed
            embed = discord.Embed(
                title=f"{civ_data['name']}",
                color=discord.Color.gold()
            )

            # Add bonuses
            if 'bonuses' in civ_data and civ_data['bonuses']:
                bonuses_text = '\n'.join([f"- {bonus}" for bonus in civ_data['bonuses'][:5]])
                embed.add_field(name="Bonuses", value=bonuses_text, inline=False)

            # Add team bonus
            if 'team_bonus' in civ_data and civ_data['team_bonus']:
                embed.add_field(name="Team Bonus", value=civ_data['team_bonus'], inline=False)

            # Add unique units
            if 'unique_units' in civ_data and civ_data['unique_units']:
                units_text = ', '.join(civ_data['unique_units'])
                embed.add_field(name="Unique Units", value=units_text, inline=True)

            # Add unique techs
            if 'unique_techs' in civ_data and civ_data['unique_techs']:
                techs_text = ', '.join(civ_data['unique_techs'])
                embed.add_field(name="Unique Techs", value=techs_text, inline=True)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilization info: {str(e)}")
            print(f"Error in civ_info: {e}")

    @commands.command(name='civs')
    async def list_civs(self, ctx):
        """List all available civilizations
        
        Usage: ?civs
        """
        try:
            civs = self.retriever.get_all_civs()

            if not civs:
                await ctx.send("No civilizations found in database.")
                return

            # Split into chunks for multiple embeds if needed
            chunk_size = 20
            civ_chunks = [civs[i:i + chunk_size] for i in range(0, len(civs), chunk_size)]

            for i, chunk in enumerate(civ_chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Civilizations ({i+1}/{len(civ_chunks)})",
                    description=', '.join(chunk),
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Total: {len(civs)} civilizations | Use ?civ <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving civilizations: {str(e)}")
            print(f"Error in list_civs: {e}")

    @commands.command(name='unit')
    async def unit_info(self, ctx, *, unit_name: str):
        """Get information about a unit
        
        Usage: ?unit <unit name>
        Example: ?unit Knight
        """
        try:
            # Get unit info
            unit_data = self.retriever.get_unit_info(unit_name)

            if not unit_data:
                await ctx.send(f"Could not find unit: {unit_name}")
                return

            # Create embed
            embed = discord.Embed(
                title=f"{unit_data['name']}",
                color=discord.Color.red()
            )

            # Add available stats
            stats_added = False

            # Cost
            if 'Cost' in unit_data:
                cost = unit_data['Cost']
                if isinstance(cost, dict):
                    cost_text = ', '.join([f"{v} {k}" for k, v in cost.items()])
                    embed.add_field(name="Cost", value=cost_text, inline=True)
                    stats_added = True

            # HP
            if 'HP' in unit_data:
                embed.add_field(name="HP", value=str(unit_data['HP']), inline=True)
                stats_added = True

            # Attack
            if 'Attack' in unit_data:
                embed.add_field(name="Attack", value=str(unit_data['Attack']), inline=True)
                stats_added = True

            # Armor
            if 'Armor' in unit_data:
                armor = unit_data['Armor']
                if isinstance(armor, dict):
                    armor_text = ', '.join([f"{v} {k}" for k, v in armor.items()])
                    embed.add_field(name="Armor", value=armor_text, inline=True)
                    stats_added = True

            # Speed
            if 'Speed' in unit_data:
                embed.add_field(name="Speed", value=str(unit_data['Speed']), inline=True)
                stats_added = True

            # Range
            if 'Range' in unit_data:
                embed.add_field(name="Range", value=str(unit_data['Range']), inline=True)
                stats_added = True

            if not stats_added:
                embed.description = "Detailed stats not available for this unit."

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving unit info: {str(e)}")
            print(f"Error in unit_info: {e}")

    @commands.command(name='units')
    async def list_units(self, ctx):
        """List all available units
        
        Usage: ?units
        """
        try:
            units = self.retriever.get_all_units()

            if not units:
                await ctx.send("No units found in database.")
                return

            # Split into chunks
            chunk_size = 30
            unit_chunks = [units[i:i + chunk_size] for i in range(0, len(units), chunk_size)]

            for i, chunk in enumerate(unit_chunks):
                embed = discord.Embed(
                    title=f"Age of Empires 2 Units ({i+1}/{len(unit_chunks)})",
                    description=', '.join(chunk),
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Total: {len(units)} units | Use ?unit <name> for details")
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving units: {str(e)}")
            print(f"Error in list_units: {e}")

    @commands.command(name='tech')
    async def tech_info(self, ctx, *, tech_name: str):
        """Get information about a technology
        
        Usage: ?tech <technology name>
        Example: ?tech Ballistics
        """
        try:
            # Get tech info
            tech_data = self.retriever.get_tech_info(tech_name)

            if not tech_data:
                await ctx.send(f"Could not find technology: {tech_name}")
                return

            # Create embed
            embed = discord.Embed(
                title=f"{tech_data['name']}",
                color=discord.Color.purple()
            )

            # Add available info
            if 'Cost' in tech_data:
                cost = tech_data['Cost']
                if isinstance(cost, dict):
                    cost_text = ', '.join([f"{v} {k}" for k, v in cost.items()])
                    embed.add_field(name="Cost", value=cost_text, inline=True)

            if 'ResearchTime' in tech_data:
                embed.add_field(name="Research Time", value=f"{tech_data['ResearchTime']}s", inline=True)

            embed.description = "Use this technology to improve your civilization!"

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving technology info: {str(e)}")
            print(f"Error in tech_info: {e}")

    @commands.command(name='datainfo')
    async def data_info(self, ctx):
        """Get information about the loaded game data
        
        Usage: ?datainfo
        """
        try:
            info = self.retriever.get_data_info()

            embed = discord.Embed(
                title="AoE2 Data Information",
                color=discord.Color.blue()
            )

            embed.add_field(name="Civilizations", value=info.get('civs_count', 0), inline=True)
            embed.add_field(name="Units", value=info.get('units_count', 0), inline=True)
            embed.add_field(name="Technologies", value=info.get('techs_count', 0), inline=True)
            embed.add_field(name="Buildings", value=info.get('buildings_count', 0), inline=True)
            embed.add_field(name="Ages", value=info.get('ages_count', 0), inline=True)
            embed.add_field(name="Loaded Civ Trees", value=info.get('loaded_civ_trees', 0), inline=True)

            if 'last_update' in info:
                embed.add_field(name="Last Update", value=info['last_update'], inline=False)

            embed.set_footer(text="Data source: github.com/SiegeEngineers/aoe2techtree")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error retrieving data info: {str(e)}")
            print(f"Error in data_info: {e}")

    @commands.command(name='compare')
    async def compare_civs(self, ctx, civ1: str, *, civ2: str):
        """Compare two civilizations
        
        Usage: ?compare <civ1> <civ2>
        Example: ?compare Britons Franks
        """
        try:
            comparison = self.retriever.compare_civs(civ1, civ2)

            if not comparison:
                await ctx.send("Could not compare civilizations. Check the names and try again.")
                return

            embed = discord.Embed(
                title=f"{comparison['civ1']['name']} vs {comparison['civ2']['name']}",
                color=discord.Color.orange()
            )

            # Civ 1 bonuses
            if 'bonuses' in comparison['civ1']:
                bonuses1 = '\n'.join([f"- {b}" for b in comparison['civ1']['bonuses'][:3]])
                embed.add_field(name=f"{comparison['civ1']['name']} Bonuses", value=bonuses1, inline=True)

            # Civ 2 bonuses
            if 'bonuses' in comparison['civ2']:
                bonuses2 = '\n'.join([f"- {b}" for b in comparison['civ2']['bonuses'][:3]])
                embed.add_field(name=f"{comparison['civ2']['name']} Bonuses", value=bonuses2, inline=True)

            embed.set_footer(text="Use ?civ <name> for full details")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Error comparing civilizations: {str(e)}")
            print(f"Error in compare_civs: {e}")

    @commands.command(name='updatedata')
    @commands.has_permissions(administrator=True)
    async def force_update(self, ctx):
        """Force update game data from GitHub (Admin only)
        
        Usage: ?updatedata
        """
        try:
            await ctx.send("Updating data from GitHub...")
            self.retriever.force_data_update()
            await ctx.send("Data updated successfully!")

        except Exception as e:
            await ctx.send(f"Error updating data: {str(e)}")
            print(f"Error in force_update: {e}")

async def setup(bot):
    """Setup function to add the cog to the bot"""
    await bot.add_cog(AoE2Commands(bot))