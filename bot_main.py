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
# J'ai retiré les imports redondants ou incorrects pour éviter les erreurs.
# from bot import TOKEN # Redondant, TOKEN est défini plus bas.
# from utils.database import db # L'instance est créée dans la classe MyBot.

# --- Configuration Initiale ---
load_dotenv()

# --- Configuration du Token ---
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    try:
        with open('config.json', 'r') as f: 
            config = json.load(f)
        TOKEN = config['token']
    except FileNotFoundError:
        print("ERREUR CRITIQUE: Token introuvable dans les variables d'environnement ou dans config.json.")
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
        
        db_path = os.path.join('data', 'main_database.db')
        self.db = DatabaseManager(db_path=db_path)

    # ==============================================================================
    # --- CORRECTIONS D'INDENTATION APPLIQUÉES ICI ---
    # Ces méthodes doivent être à l'intérieur de la classe MyBot.

    async def setup_hook(self):
        print("--- Démarrage et Configuration du Bot ---")
        
        print("Initialisation de la base de données...")
        try:
            await self.db.connect()
            # Assurez-vous que votre classe DatabaseManager a une méthode initialize_tables()
            if hasattr(self.db, 'initialize_tables'):
                await self.db.initialize_tables()
            print("  [+] Base de données connectée et tables initialisées.")
        except Exception as e:
            print(f"  [!] ERREUR CRITIQUE lors de l'initialisation de la DB.", file=sys.stderr)
            traceback.print_exc()
            await self.close()
            return

        print("Chargement des Cogs...")
        for cog_path in COGS_TO_LOAD:
            try:
                await self.load_extension(cog_path)
                print(f"  [+] {cog_path} chargé avec succès.")
            except Exception as e:
                print(f"  [!] ERREUR lors du chargement de '{cog_path}':")
                traceback.print_exception(type(e), e, e.__traceback__)
        
        print("--- DÉBUT DE LA SYNCHRONISATION NUCLÉAIRE ---")
        try:
            print("  [SYNCHRO] Tentative de synchronisation globale...")
            await self.tree.sync()
            print("  [SYNCHRO] Synchronisation globale terminée.")

            guild_id = 1420017902748307510 # REMPLACEZ PAR VOTRE ID DE SERVEUR DE TEST
            test_guild = discord.Object(id=guild_id)

            self.tree.copy_global_to(guild=test_guild)
            synced = await self.tree.sync(guild=test_guild)
            print(f"  [SYNCHRO FORCÉE] {len(synced)} commandes synchronisées sur le serveur de test.")
            
        except Exception as e:
            print(f"ERREUR lors de la synchronisation : {e}")
            traceback.print_exc()

        print("--- SYNCHRONISATION TERMINÉE ---")
    
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
    # ==============================================================================


# --- Création de l'instance du bot ---
bot = MyBot()

# --- Gestion Globale des Erreurs de Commandes Slash ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    # Votre gestionnaire d'erreurs reste ici. C'est une bonne pratique.
    print(f"Erreur non gérée interceptée par le gestionnaire global : {error}")
    traceback.print_exc()
    # Vous pouvez ajouter une réponse à l'utilisateur ici si vous le souhaitez.
    pass 


# --- Lancement du bot ---
async def main():
    # La logique de chargement des cogs est maintenant dans setup_hook,
    # donc cette fonction se contente de démarrer le bot.
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Arrêt manuel détecté.")