# cogs/leveling.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import random
import time
import datetime
import traceback

# --- Dépendances ---
from utils.database import db

# --- Constantes ---
XP_PER_MESSAGE_MIN = 15
XP_PER_MESSAGE_MAX = 25
XP_COOLDOWN_SECONDS = 60

# --- Classe Cog ---
class LevelingCog(commands.Cog, name="Niveaux & XP"):
    def __init__(self, bot: commands.Bot, db_manager):
        self.bot = bot
        self.db = db_manager
        self.user_cooldowns = {} # {guild_id: {user_id: timestamp}}

    def calculate_level(self, xp: int) -> int:
        """Calcule le niveau basé sur l'XP (formule simple)."""
        return 0 if xp <= 0 else int((xp / 150) ** 0.5)

    def calculate_xp_for_level(self, level: int) -> int:
        """Calcule l'XP nécessaire pour atteindre un niveau."""
        return 0 if level <= 0 else int(150 * (level ** 2))

    @commands.Cog.listener("on_message")
    async def on_xp_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # Vérifier si le système de leveling est activé via la DB (si vous avez cette config)
        # config = await self.db.get_guild_settings(guild_id)
        # if not config or not config.get("leveling_config", {}).get("activated", True):
        #     return
            
        now = time.time()
        cooldowns = self.user_cooldowns.setdefault(guild_id, {})
        last_message_time = cooldowns.get(user_id, 0)

        if now - last_message_time < XP_COOLDOWN_SECONDS:
            return
        
        cooldowns[user_id] = now

        try:
            user_data = await self.db.get_user_data(guild_id, user_id)
            old_level = self.calculate_level(user_data.get("xp", 0))
            
            xp_to_add = random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)
            new_xp = user_data.get("xp", 0) + xp_to_add
            new_level = self.calculate_level(new_xp)
            
            await self.db.update_user_xp(guild_id, user_id, new_xp, new_level)

            if new_level > old_level:
                # config_leveling = config.get("leveling_config", {})
                # level_up_message = config_leveling.get("level_up_message", "🎉 Bravo {user}, tu as atteint le niveau **{level}** !")
                level_up_message = "🎉 Bravo {user}, tu as atteint le niveau **{level}** !"
                try:
                    await message.channel.send(level_up_message.format(user=message.author.mention, level=new_level))
                except discord.Forbidden: pass
        
        except Exception as e:
            print(f"Erreur lors de l'attribution d'XP: {e}"); traceback.print_exc()

    @app_commands.command(name="profil", description="Affiche votre profil de niveau ou celui d'un autre membre.")
    @app_commands.describe(membre="Le membre dont afficher le profil.")
    async def profil(self, interaction: discord.Interaction, membre: Optional[discord.Member] = None):
        target = membre or interaction.user
        if target.bot:
            await interaction.response.send_message("Les bots n'ont pas de profil.", ephemeral=True); return
        
        user_data = await self.db.get_user_data(interaction.guild.id, target.id)
        xp = user_data.get("xp", 0)
        level = self.calculate_level(xp)
        
        xp_for_next = self.calculate_xp_for_level(level + 1)
        xp_current_level_base = self.calculate_xp_for_level(level)
        xp_in_level = xp - xp_current_level_base
        xp_needed_for_next = xp_for_next - xp_current_level_base

        progress = int((xp_in_level / xp_needed_for_next) * 20) if xp_needed_for_next > 0 else 20
        bar = "▓" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title=f"Profil de {target.display_name}",
            color=target.color or discord.Color.blue()
        ).set_thumbnail(url=target.display_avatar.url
        ).add_field(name="Niveau", value=f"`{level}`", inline=True
        ).add_field(name="XP Total", value=f"`{xp}`", inline=True
        ).add_field(name="Progression", value=f"`{xp_in_level} / {xp_needed_for_next}` XP\n`{bar}`", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="leaderboard", description="Affiche le classement des membres par XP.")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        top_users = await self.db.get_leaderboard(interaction.guild.id, limit=10)
        
        if not top_users:
            await interaction.followup.send("Personne n'a encore gagné d'XP sur ce serveur."); return
            
        embed = discord.Embed(title=f"🏆 Classement XP - {interaction.guild.name}", color=discord.Color.gold())
        description = []
        for i, user_row in enumerate(top_users):
            member = interaction.guild.get_member(user_row['user_id'])
            if member:
                level = self.calculate_level(user_row['xp'])
                description.append(f"**{i+1}.** {member.mention} - Niveau `{level}` (`{user_row['xp']}` XP)")
        
        embed.description = "\n".join(description) if description else "Aucun membre du classement n'a été trouvé."
        await interaction.followup.send(embed=embed)

# --- Setup du Cog ---
async def setup(bot: commands.Bot):
    if not hasattr(bot, 'db'):
        print("ERREUR CRITIQUE (leveling.py): L'objet bot n'a pas d'attribut 'db'.")
        return
    await bot.add_cog(LevelingCog(bot, bot.db))
    print("Cog Leveling chargé.")