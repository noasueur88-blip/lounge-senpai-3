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
        full_name = f"{parent_name} {command.name}".strip()
        
        if hasattr(command, 'commands') and command.commands:
            return {
                "name": full_name,
                "description": command.description,
                "subcommands": [self.format_command_recursively(sub, full_name) for sub in command.commands]
            }
        else:
            return {
                "name": full_name,
                "description": command.description,
                "subcommands": []
            }

    @app_commands.command(name="export-commands", description="[Propriétaire] Exporte la liste des commandes pour le site web.")
    @commands.is_owner()
    async def export_commands(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        print("[EXPORT] La commande /export-commands a été lancée.")
        all_commands_data = []
        for command in self.bot.tree.get_commands():
            all_commands_data.append(self.format_command_recursively(command))
        
        print(f"[EXPORT] {len(all_commands_data)} commandes trouvées. Préparation à l'écriture...")
            
        try:
            # ==============================================================================
            # --- CORRECTION APPLIQUÉE ICI ---
            # On utilise un chemin d'accès absolu et "en dur" pour une fiabilité maximale.
            
            # 1. On définit le chemin de base vers votre dossier de travail principal.
            #    Python gère bien les anti-slashs (\) dans les chaînes de caractères.
            base_project_path = r"C:\Users\Eleve\OneDrive\OneDrive - Conseil régional Grand Est - Numérique Educatif\Bureau"

            # 2. On construit le chemin complet vers le fichier de destination en utilisant os.path.join.
            #    C'est la méthode la plus propre et elle fonctionne sur tous les systèmes.
            filepath = os.path.join(
                base_project_path, 
                'site-web-bot', 
                'static', 
                'data', 
                'commands.json'
            )
            # ==============================================================================

            print(f"[EXPORT] Le chemin de destination est maintenant fixé à : {filepath}")

            # S'assurer que le dossier de destination existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Écrire le fichier JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_commands_data, f, indent=4, ensure_ascii=False)
            
            print(f"[EXPORT] SUCCÈS : Le fichier a été écrit à l'emplacement ci-dessus.")
            await interaction.followup.send(f"✅ Fichier des commandes exporté avec succès !")

        except Exception as e:
            print(f"[EXPORT] ERREUR CRITIQUE LORS DE L'ÉCRITURE DU FICHIER :")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Une erreur est survenue : `{e}`. Vérifiez la console du bot.")

async def setup(bot: commands.Bot):
    await bot.add_cog(WebsiteLinkCog(bot))
    print("Cog 'WebsiteLink' (version avec chemin absolu) chargé.")