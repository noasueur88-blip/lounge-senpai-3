# main.py
import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv
import sys
import json
import asyncio
from utils.database import DatabaseManager

# --- Chargement des Utilitaires ---
# J'ai retiré les imports redondants ou incorrects
# from bot import TOKEN # Redondant
# from utils.database import db # Remplacé par l'import de la classe

# --- Configuration Initiale ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- Configuration ---
# Essaie de charger le token depuis les variables d'environnement (pour Render)
TOKEN = os.getenv("DISCORD_TOKEN")
        
        # Si on est en local et que la variable n'existe pas, on lit le config.json
if not TOKEN:
            try:
                with open('config.json', 'r') as f: config = json.load(f)
                TOKEN = config['token']
            except FileNotFoundError:
                print("ERREUR CRITIQUE: Token introuvable.")
                exit(1)

# --- Intents ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

# --- Liste des Cogs à charger ---
COGS_TO_LOAD = [
    "cogs.utility", "cogs.moderation_bot", "cogs.automod_cog", "cogs.marriage_cog",
    "cogs.shop_cog", "cogs.economie_cog", "cogs.suggestions_tickets_cog",
    "cogs.design_commands", "cogs.prison", "cogs.leveling", "cogs.config_cog",
    "cogs.admin_eco_cog", "cogs.community", "cogs.website_link", "cogs.debug_cog",
]

# --- Définition de la Classe du Bot ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        # ==============================================================================
        # --- CORRECTION APPLIQUÉE ICI ---
        # 1. On définit le chemin vers le fichier de la base de données.
        #    Le fichier sera créé dans le dossier /data s'il n'existe pas.
        db_path = os.path.join('data', 'main_database.db')

        # 2. On passe ce chemin lors de la création de l'instance DatabaseManager.
        #    Ceci résout l'erreur TypeError.
        self.db = DatabaseManager(db_path=db_path)
        # ==============================================================================

    async def setup_hook(self):
        """Fonction appelée une seule fois pour configurer le bot."""
        print("--- Démarrage et Configuration du Bot ---")

        print("Initialisation de la base de données...")
        try:
            await self.db.connect()
            print("  [+] Base de données connectée et initialisée.")
        except Exception as e:
            print(f"  [!] ERREUR CRITIQUE: Impossible de se connecter à la DB.", file=sys.stderr)
            traceback.print_exception(type(e), e, e.__traceback__)
            await self.close()

        print("Chargement des Cogs...")
        for cog_path in COGS_TO_LOAD:
            try:
                await self.load_extension(cog_path)
                print(f"  [+] {cog_path} chargé avec succès.")
            except Exception as e:
                print(f"  [!] ERREUR lors du chargement de '{cog_path}':", file=sys.stderr)
                traceback.print_exception(type(e), e, e.__traceback__)
        print("Traitement des Cogs terminé.")

        print("Synchronisation des commandes slash...")
        try:
            # ==============================================================================
            # --- CORRECTION TEMPORAIRE POUR FORCER LA SYNCHRO ---
            
            # CORRECTION 1 : Toutes ces lignes sont maintenant au même niveau d'indentation.
            # 1. Mettez l'ID de votre serveur de test ici.
            guild_id = 1420017902748307510 # REMPLACEZ CECI PAR L'ID DE VOTRE SERVEUR
            test_guild = discord.Object(id=guild_id)

            # 2. On synchronise SEULEMENT sur ce serveur. C'est instantané.
            synced = await self.tree.sync(guild=test_guild)
            print(f"  [SYNCHRO FORCÉE] {len(synced)} commandes synchronisées sur le serveur de test.")
            
            # Optionnel : Si vous voulez que les commandes restent globales, vous pouvez
            # laisser la synchronisation globale juste après.
            # synced_global = await self.tree.sync()
            # print(f"  [+] {len(synced_global)} commandes synchronisées globalement.")
            # ==============================================================================
        # CORRECTION 2 : Le 'except' est maintenant parfaitement aligné avec le 'try'.
        except Exception as e:
            print(f"ERREUR lors de la synchronisation : {e}")
    async def on_ready(self):
        """Événement appelé quand le bot est prêt et connecté."""
        print('-----------------------------------------')
        print(f'Connecté en tant que {self.user.name} ({self.user.id})')
        print(f'Prêt à fonctionner sur {len(self.guilds)} serveur(s).')
        print('-----------------------------------------')
        
    async def close(self):
        """Surcharge de la méthode close pour un nettoyage propre."""
        print("\nArrêt du bot détecté. Nettoyage en cours...")
        if hasattr(self, 'db') and self.db._connection:
             await self.db.close()
             print("Connexion à la base de données fermée.")
        await super().close()
        print("Bot arrêté proprement.")


# --- Création de l'instance du bot ---
bot = MyBot()

# --- Gestion Globale des Erreurs de Commandes Slash ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    # Votre gestionnaire d'erreurs reste ici
    pass 


# --- Lancement du bot ---
async def main():
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Arrêt manuel détecté.")