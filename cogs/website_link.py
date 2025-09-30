import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import traceback

class WebsiteLinkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def format_command_recursively(self, command, parent_name=""):
        """
        Fonction récursive améliorée qui construit le nom complet à chaque étape.
        """
        # Construit le nom complet (ex: "automod sanctions")
        full_name = f"{parent_name} {command.name}".strip()
        
        # Cas 1 : La commande est un groupe et a des sous-commandes
        if hasattr(command, 'commands') and command.commands:
            return {
                "name": full_name, # Stocke le nom complet du groupe
                "description": command.description,
                # Appel récursif pour chaque sous-commande, en passant le nom complet du parent
                "subcommands": [self.format_command_recursively(sub, full_name) for sub in command.commands]
            }
        # Cas 2 : C'est une commande finale
        else:
            return {
                "name": full_name, # Le nom final sera "automod sanctions"
                "description": command.description,
                "subcommands": []
            }

    @app_commands.command(name="export-commands", description="[Propriétaire] Exporte la liste des commandes pour le site web.")
    @commands.is_owner()
    async def export_commands(self, interaction: discord.Interaction):
        # ... (le reste de votre commande reste inchangé)
        await interaction.response.defer(ephemeral=True)
        all_commands_data = []
        for command in self.bot.tree.get_commands():
            all_commands_data.append(self.format_command_recursively(command))
        
        try:
            # Assurez-vous que ce chemin est correct
            # Par exemple, si vous avez fusionné les projets :
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.abspath(os.path.join(script_dir, '..', '..', 'static', 'data', 'commands.json'))

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_commands_data, f, indent=4, ensure_ascii=False)
            
            await interaction.followup.send(f"✅ Fichier des commandes exporté avec succès !")

        except Exception as e:
            print(f"[EXPORT] ERREUR LORS DE L'ÉCRITURE DU FICHIER :")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Une erreur est survenue : `{e}`. Vérifiez la console.")

async def setup(bot: commands.Bot):
    await bot.add_cog(WebsiteLinkCog(bot))