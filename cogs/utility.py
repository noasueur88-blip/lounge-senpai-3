# cogs/utility.py
import discord # type: ignore
from discord import app_commands # type: ignore
from discord.ext import commands, tasks # type: ignore
from typing import Optional, List, Literal, Dict
import json
import os
import re
import shutil
import time
import datetime
import traceback
import asyncio

# La fonction doit être ici, au niveau de l'indentation 0
async def is_not_maintenance(interaction: discord.Interaction) -> bool:
    """Check si le serveur n'est pas en maintenance OU si l'utilisateur est admin."""
    # Note: Cette logique dépend de la façon dont vous stockez l'état de maintenance.
    # Ceci est un exemple qui utilise un fichier settings.json.
    
    # Charger les données (cette partie peut varier selon votre code)
    try:
        with open('./data/settings.json', 'r') as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
        
    guild_settings = settings.get(str(interaction.guild_id), {})
    in_maintenance = guild_settings.get("maintenance_mode", False)

    if not in_maintenance:
        return True # Pas en maintenance, tout le monde peut utiliser

    # En maintenance, seuls les admins peuvent utiliser
    if interaction.user.guild_permissions.manage_guild:
        return True # Admin, autorisé même en maintenance
    else:
        # Pas admin et en maintenance, refuser
        await interaction.response.send_message("🚧 Le serveur est actuellement en mode maintenance. Seuls les administrateurs peuvent utiliser les commandes.", ephemeral=True)
        return False # Important de retourner False pour que le check échoue


# --- Classe Cog ---
class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
# --- Constantes et Configuration ---
DATA_DIR = './data'
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
MAINTENANCE_BACKUP_FILE = os.path.join(DATA_DIR, 'maintenance_perms_backup.json')
# *** CORRECTION : AJOUTER CETTE LIGNE ***
SHOP_DATA_FILE = os.path.join(DATA_DIR, 'shop_data.json')

LOCKDOWN_PERMISSIONS = {
    "send_messages": False, "send_messages_in_threads": False, "create_public_threads": False,
    "create_private_threads": False, "add_reactions": False, "speak": False, "stream": False,
    "use_voice_activation": False, "connect": False, "use_application_commands": False,
    "send_tts_messages": False, "request_to_speak": False,
}

# --- Fonctions Helper JSON ---
def load_data(filepath):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(filepath, 'w', encoding='utf-8') as f: json.dump({}, f)
        return {}
    except Exception as e:
        print(f"Erreur chargement {filepath}: {e}"); traceback.print_exc(); return {}

def save_data(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        temp_filepath = filepath + ".tmp"
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        os.replace(temp_filepath, filepath)
    except Exception as e:
        print(f"Erreur critique sauvegarde {filepath}: {e}"); traceback.print_exc()

# --- Classe Cog ---
class UtilityCog(commands.Cog, name="Utilitaires Serveur"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = load_data(SETTINGS_FILE)
        self.maintenance_backup = load_data(MAINTENANCE_BACKUP_FILE)

    def get_guild_settings(self, guild_id: int) -> dict:
        guild_id_str = str(guild_id)
        return self.settings.setdefault(guild_id_str, {})
    
    # ... (autres commandes comme /help, /lock, /unlock, etc. si elles sont ici) ...

import discord # type: ignore
from discord import app_commands # type: ignore
# Importez ici vos autres dépendances (asyncio, datetime, load_data, save_data, etc.)

# =====================================================================
# == AJOUTS NÉCESSAIRES POUR LE VERROUILLAGE DES PERMISSIONS        ==
# =====================================================================
LOCKDOWN_PERMISSIONS = {
    "send_messages": False,             # INTERDIT l'envoi de messages
    "send_messages_in_threads": False,  # INTERDIT l'envoi dans les fils de discussion
    "create_public_threads": False,     # INTERDIT la création de fils de discussion publics
    "create_private_threads": False,    # INTERDIT la création de fils de discussion privés
}

# Assurez-vous que MAINTENANCE_BACKUP_FILE, load_data, save_data et asyncio sont définis dans votre environnement.
# =====================================================================
# ==                VOTRE CODE INITIAL (NON MODIFIÉ)               ==
# =====================================================================

class MaintenanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maintenance_backup = load_data(MAINTENANCE_BACKUP_FILE) # Assurez-vous que ceci est bien défini

    # =============================================
    # ==      COMMANDES MAINTENANCE SERVEUR      ==
    # =============================================
    maintenance_group = app_commands.Group(name="maintenance", description="Gère la maintenance du serveur.")

    @maintenance_group.command(name="activate", description="Active la maintenance (restreint l'accès aux salons).")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def maintenance_activate(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id_str = str(guild.id)

        if guild_id_str in self.maintenance_backup and self.maintenance_backup.get(guild_id_str, {}).get("active", False):
            await interaction.response.send_message("⚠️ Le mode maintenance est déjà activé.", ephemeral=True)
            return

        view = discord.ui.View(timeout=60.0)

        async def confirm_callback(interaction_confirm: discord.Interaction):
            if interaction_confirm.user.id != interaction.user.id:
                await interaction_confirm.response.send_message("Seul l'initiateur peut confirmer.", ephemeral=True); return

            ### CORRECTION 1 : Répondre IMMÉDIATEMENT à l'interaction du bouton ###
            for item in view.children: item.disabled = True
            await interaction_confirm.response.edit_message(content="**Activation en cours, veuillez patienter...**", view=view)
            
            # Utiliser followup pour le message de statut, car l'interaction du bouton a déjà été répondue
            status_message = await interaction.followup.send("Initialisation...", ephemeral=True, wait=True)

            # --- Logique d'activation (longue) ---
            original_perms_backup = {}
            roles_to_restrict = [guild.default_role]
            for role in guild.roles:
                if not (role.is_bot_managed() or role.is_integration() or role.permissions.administrator or role >= guild.me.top_role):
                    roles_to_restrict.append(role)
            
            permission_errors = 0
            all_channels = guild.channels
            total_channels = len(all_channels)

            for i, channel in enumerate(all_channels):
                try:
                    await status_message.edit(content=f"Traitement... `{i+1}/{total_channels}` : {channel.mention}")
                except discord.HTTPException: pass

                channel_perms_for_backup = {}
                for role in roles_to_restrict:
                    current_overwrites = channel.overwrites_for(role)
                    role_perms_to_save = {}
                    new_overwrite = discord.PermissionOverwrite.from_pair(*current_overwrites.pair())
                    needs_update = False

                    for perm, lock_value in LOCKDOWN_PERMISSIONS.items():
                        original_value = getattr(current_overwrites, perm)
                        if original_value != lock_value:
                            role_perms_to_save[perm] = original_value
                            setattr(new_overwrite, perm, lock_value)
                            needs_update = True
                    
                    if getattr(current_overwrites, "view_channel") is False:
                        setattr(new_overwrite, "view_channel", False)

                    if needs_update:
                        try:
                            await channel.set_permissions(role, overwrite=new_overwrite, reason=f"Maintenance ON par {interaction.user}")
                            if role_perms_to_save:
                                channel_perms_for_backup[str(role.id)] = role_perms_to_save
                        except (discord.Forbidden, discord.HTTPException):
                            permission_errors += 1
                        await asyncio.sleep(0.5)

                if channel_perms_for_backup:
                    original_perms_backup[str(channel.id)] = channel_perms_for_backup

            if original_perms_backup:
                self.maintenance_backup[guild_id_str] = {
                    "active": True, "activated_by": interaction.user.id,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "original_perms": original_perms_backup
                }
                save_data(MAINTENANCE_BACKUP_FILE, self.maintenance_backup)
                print("MAINTENANCE: Backup de permissions créé.")
            
            final_message = f"✅ Mode maintenance activé ! ({total_channels} salons traités)."
            if permission_errors > 0: final_message += f"\n⚠️ **{permission_errors} erreur(s)** rencontrée(s)."
            await status_message.edit(content=final_message)


        async def cancel_callback(interaction_cancel: discord.Interaction):
            if interaction_cancel.user.id != interaction.user.id:
                await interaction_cancel.response.send_message("Seul l'initiateur peut annuler.", ephemeral=True); return
            for item in view.children: item.disabled = True
            await interaction_cancel.response.edit_message(content="Activation annulée.", view=view)

        async def on_timeout_callback():
            for item in view.children: item.disabled = True
            try: await interaction.edit_original_response(content="Confirmation expirée.", view=view)
            except discord.NotFound: pass

        confirm_button = discord.ui.Button(label="Confirmer", style=discord.ButtonStyle.danger)
        cancel_button = discord.ui.Button(label="Annuler", style=discord.ButtonStyle.secondary)
        
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.on_timeout = on_timeout_callback
        
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await interaction.response.send_message(
            "**ATTENTION :** Ceci va restreindre l'accès à tous les salons. **Confirmez-vous ?**",
            view=view, ephemeral=True
        )

    @maintenance_group.command(name="deactivate", description="Désactive la maintenance et restaure les permissions.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def maintenance_deactivate(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id_str = str(guild.id)
        
        self.maintenance_backup = load_data(MAINTENANCE_BACKUP_FILE)
        
        if guild_id_str not in self.maintenance_backup or not self.maintenance_backup[guild_id_str].get("active", False):
            await interaction.response.send_message("ℹ️ Le mode maintenance n'est pas actif.", ephemeral=True)
            return
            
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        backup_data = self.maintenance_backup[guild_id_str]
        original_perms_to_restore = backup_data.get("original_perms", {})

        if not original_perms_to_restore:
            del self.maintenance_backup[guild_id_str]
            save_data(MAINTENANCE_BACKUP_FILE, self.maintenance_backup)
            await interaction.followup.send("⚠️ Aucune donnée à restaurer. Mode maintenance désactivé.", ephemeral=True)
            return

        permission_errors = 0
        total_to_restore = len(original_perms_to_restore)
        status_message = await interaction.followup.send(f"Désactivation... Restauration de {total_to_restore} salons.", ephemeral=True, wait=True)

        for i, (channel_id_str, roles_perms) in enumerate(original_perms_to_restore.items()):
            channel = guild.get_channel(int(channel_id_str))
            if not channel: continue

            try: await status_message.edit(content=f"Restauration... {i+1}/{total_to_restore} : {channel.mention}")
            except discord.HTTPException: pass

            for role_id_str, perms_to_restore in roles_perms.items():
                try:
                    target = guild.get_role(int(role_id_str))
                    if not target and int(role_id_str) == guild.id: target = guild.default_role
                    if not target: continue
                    
                    current_overwrite = channel.overwrites_for(target)
                    restored_overwrite = discord.PermissionOverwrite.from_pair(*current_overwrite.pair())
                    
                    for perm_name, original_value in perms_to_restore.items():
                        setattr(restored_overwrite, perm_name, original_value)
                    
                    await channel.set_permissions(target, overwrite=restored_overwrite, reason=f"Maintenance OFF par {interaction.user}")
                except (discord.Forbidden, discord.HTTPException):
                    permission_errors += 1
            await asyncio.sleep(0.5)

        del self.maintenance_backup[guild_id_str]
        save_data(MAINTENANCE_BACKUP_FILE, self.maintenance_backup)

        final_message = f"✅ Mode maintenance désactivé ! ({total_to_restore} salons traités)."
        if permission_errors > 0: final_message += f"\n⚠️ {permission_errors} erreur(s) lors de la restauration."
        await status_message.edit(content=final_message)


    # =============================================
    # ==       GESTIONNAIRE D'ERREURS COG        ==
    # =============================================
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if interaction.response.is_done(): return
        
        print(f"Erreur dans UtilityCog (Cmd: {interaction.command.qualified_name if interaction.command else 'N/A'}): {error.__class__.__name__}: {error}")
        if isinstance(error, app_commands.CommandInvokeError): traceback.print_exception(type(error.original), error.original, error.original.__traceback__)
            
        error_message = "❌ Une erreur inattendue est survenue."
        # ... (logique détaillée pour les différents types d'erreurs)
        
        try:
            if interaction.response.is_done(): await interaction.followup.send(error_message, ephemeral=True)
            else: await interaction.response.send_message(error_message, ephemeral=True)
        except discord.HTTPException as e:
            print(f"Impossible d'envoyer message d'erreur: {e}")

# =============================================
# ==       SETUP DU COG                    ==
# =============================================
async def setup(bot: commands.Bot):
    # ... (votre setup existant) ...
    # NOUVEAU : S'assurer que le fichier de la boutique est créé/chargé
    load_data(SHOP_DATA_FILE)  # type: ignore
    await bot.add_cog(UtilityCog(bot)) # type: ignore
    print("Cog Utility (avec commandes boutique) chargé avec succès.")