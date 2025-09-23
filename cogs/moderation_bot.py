# cogs/moderation_bot.py
import discord
from discord import app_commands # <--- AJOUTEZ CETTE LIGNE
from discord.ext import commands
from typing import Optional # Ajoutez ceci aussi si vous utilisez des arguments optionnels
import os
from dotenv import load_dotenv # type: ignore
import asyncio # Pour le message de confirmation temporaire du clear
from cogs.utility import is_not_maintenance # type: ignore # Importer la fonction check
# ... (votre classe ModerationCog) ...
class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulse un membre du serveur.") # type: ignore
    @app_commands.describe(membre="Le membre à expulser.", raison="La raison de l'expulsion.") # type: ignore
    @app_commands.checks.has_permissions(kick_members=True) # type: ignore
    @app_commands.checks.bot_has_permissions(kick_members=True) # type: ignore
    # @app_commands.check(is_not_maintenance) # Généralement, les commandes de modération doivent rester actives
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        # ... (code existant) ...
        pass # juste pour l'exemple

    @app_commands.command(name="ban", description="Bannit un membre du serveur.") # type: ignore
    # ... permissions ...
    # @app_commands.check(is_not_maintenance) # Laisser les admins bannir même en maintenance
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, jours_messages: app_commands.Range[int, 0, 7] = 1, raison: str = "Aucune raison fournie"): # type: ignore
         # ... (code existant) ...
        pass

    @app_commands.command(name="clear", description="Supprime un nombre spécifié de messages.") # type: ignore
    # ... permissions ...
    # @app_commands.check(is_not_maintenance) # Laisser les admins clearer même en maintenance
    async def clear(self, interaction: discord.Interaction, nombre: app_commands.Range[int, 1, 100]): # type: ignore
        # ... (code existant) ...
        pass

    # ... (erreur handler existant) ...

# ... (setup existant) ...

# --- Configuration ---

# Charger les variables d'environnement (pour le token)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("Erreur: Le token Discord n'a pas été trouvé.")
    print("Assurez-vous d'avoir un fichier .env avec DISCORD_TOKEN=VOTRE_TOKEN")
    exit() # Arrête le script si le token n'est pas trouvé

# Définir le préfixe des commandes (ex: !kick, !ban)
COMMAND_PREFIX = "!"

# Définir les intents nécessaires
# guilds: accès aux informations du serveur
# members: accès aux informations des membres (kick, ban, join, leave) - INTENT PRIVILÉGIÉ
# messages: accès aux messages (pour les commandes)
# message_content: accès au contenu des messages (pour les commandes) - INTENT PRIVILÉGIÉ
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True # Nécessaire pour lire les commandes après les changements de Discord

# Créer l'instance du bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# --- Événements ---

@bot.event
async def on_ready():
    """ Affiche un message quand le bot est connecté et prêt. """
    print(f'Connecté en tant que {bot.user.name} ({bot.user.id})')
    print('Le bot est prêt.')
    print('------')
    # Optionnel: Définir le statut du bot
    await bot.change_presence(activity=discord.Game(name=f"Modérer avec {COMMAND_PREFIX}"))

@bot.event
async def on_command_error(ctx, error):
    """ Gère les erreurs de commandes courantes. """
    if isinstance(error, commands.CommandNotFound):
        # Ignore les commandes inconnues pour ne pas spammer
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Argument manquant. Utilisation : `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("Je n'ai pas les permissions nécessaires pour exécuter cette action.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(f"Membre non trouvé : `{error.argument}`.")
    elif isinstance(error, commands.BadArgument):
         await ctx.send(f"Argument invalide. Vérifiez le type d'argument attendu (ex: un nombre, une mention).")
    else:
        # Pour les autres erreurs, affiche l'erreur dans la console (pour le débogage)
        print(f'Erreur non gérée dans la commande {ctx.command}: {error}')
        await ctx.send("Une erreur est survenue lors de l'exécution de la commande.")

# --- Commandes de Modération ---

@bot.command(name='kick', help='Expulse un membre du serveur.')
@commands.has_permissions(kick_members=True) # Vérifie si l'auteur a la permission
@commands.bot_has_permissions(kick_members=True) # Vérifie si le bot a la permission
async def kick(ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
    """
    Commande pour expulser un membre.
    Utilisation: !kick @membre [raison optionnelle]
    """
    if member == ctx.author:
        await ctx.send("Vous ne pouvez pas vous expulser vous-même !")
        return
    if member == bot.user:
        await ctx.send("Je ne peux pas m'expulser moi-même !")
        return
    # Vérifier la hiérarchie des rôles (on ne peut pas kick qqn avec un rôle plus haut ou égal)
    if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
         await ctx.send("Vous ne pouvez pas expulser un membre ayant un rôle égal ou supérieur au vôtre.")
         return
    if ctx.guild.me.top_role <= member.top_role:
         await ctx.send("Je ne peux pas expulser ce membre car son rôle est égal ou supérieur au mien.")
         return

    try:
        await member.kick(reason=f"{reason} (Par {ctx.author.name})")
        await ctx.send(f"👢 {member.mention} a été expulsé avec succès. Raison : {reason}")
        # Optionnel: Envoyer un message privé au membre expulsé
        try:
            await member.send(f"Vous avez été expulsé du serveur '{ctx.guild.name}'. Raison : {reason}")
        except discord.Forbidden:
            print(f"Impossible d'envoyer un MP à {member.name} (probablement bloqué ou MP désactivés)")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission d'expulser ce membre (vérifiez mes rôles).")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur est survenue lors de l'expulsion : {e}")
        print(f"Erreur HTTP lors du kick: {e}")

@bot.command(name='ban', help='Bannit un membre du serveur.')
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
    """
    Commande pour bannir un membre.
    Utilisation: !ban @membre [raison optionnelle]
    """
    if member == ctx.author:
        await ctx.send("Vous ne pouvez pas vous bannir vous-même !")
        return
    if member == bot.user:
        await ctx.send("Je ne peux pas me bannir moi-même !")
        return
    # Vérifier la hiérarchie des rôles
    if ctx.author.top_role <= member.top_role and ctx.guild.owner != ctx.author:
         await ctx.send("Vous ne pouvez pas bannir un membre ayant un rôle égal ou supérieur au vôtre.")
         return
    if ctx.guild.me.top_role <= member.top_role:
         await ctx.send("Je ne peux pas bannir ce membre car son rôle est égal ou supérieur au mien.")
         return

    try:
        # delete_message_days=1: Supprime les messages de l'utilisateur des dernières 24h
        await member.ban(reason=f"{reason} (Par {ctx.author.name})", delete_message_days=1)
        await ctx.send(f"🔨 {member.mention} a été banni avec succès. Raison : {reason}")
        # Optionnel: Envoyer un message privé au membre banni (peut échouer si déjà parti ou MP bloqués)
        try:
            await member.send(f"Vous avez été banni du serveur '{ctx.guild.name}'. Raison : {reason}")
        except discord.Forbidden:
             print(f"Impossible d'envoyer un MP à {member.name} avant le ban.")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de bannir ce membre (vérifiez mes rôles).")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur est survenue lors du bannissement : {e}")
        print(f"Erreur HTTP lors du ban: {e}")


# Commande pour supprimer des messages (aussi appelée purge)
@bot.command(name='clear', aliases=['purge'], help='Supprime un nombre spécifié de messages dans le salon actuel.')
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """
    Supprime des messages.
    Utilisation: !clear [nombre]
    """
    if amount <= 0:
        await ctx.send("Veuillez entrer un nombre positif de messages à supprimer.")
        return
    # Ajoute 1 pour supprimer aussi la commande !clear elle-même
    # Limite à 100 messages max par commande bulk delete (limitation Discord)
    # On peut faire plusieurs appels si nécessaire, mais gardons simple pour la base.
    limit = min(amount + 1, 101) # +1 pour la commande, max 100 messages à supprimer (+ la commande)

    try:
        deleted = await ctx.channel.purge(limit=limit)
        # Envoie un message de confirmation qui s'auto-détruit après 5 secondes
        confirm_msg = await ctx.send(f"🗑️ {len(deleted) - 1} messages ont été supprimés.", delete_after=5.0)
        # Supprime aussi la commande d'origine (si elle n'a pas été supprimée par purge)
        # await ctx.message.delete() # Généralement inclus dans le purge(limit=amount+1)

    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de supprimer des messages dans ce salon.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur est survenue lors de la suppression des messages : {e}")
        print(f"Erreur HTTP lors du clear/purge: {e}")
    except ValueError:
         await ctx.send("Veuillez entrer un nombre valide.") # Si l'utilisateur entre du texte au lieu d'un nombre

# --- Lancement du Bot ---
if __name__ == "__main__":
    print("Lancement du bot...")
    bot.run(TOKEN)
# =============================================
# ==           SETUP DU COG                  ==
# =============================================
# C'EST CE BLOC QUI EST MANQUANT OU MAL ÉCRIT
async def setup(bot: commands.Bot):
    # Cette ligne crée une instance de votre classe Cog et l'ajoute au bot.
    # Assurez-vous que le nom 'ModerationCog' correspond bien au nom de votre classe.
    await bot.add_cog(ModerationCog(bot))
    print("Cog Moderation (moderation_bot.py) chargé.") # Message de confirmation optionnel