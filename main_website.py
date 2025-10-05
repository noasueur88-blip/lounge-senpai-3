# --- Imports nécessaires ---
import threading
import asyncio
import os
import json
from flask import Flask, render_template, redirect, url_for, session, request, jsonify # jsonify est ajouté
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

# --- IMPORTER VOTRE BOT ---
# Cette partie suppose que votre bot est défini dans bot_main.py
from bot_main import MyBot, TOKEN

# --- Configuration initiale ---
load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ==============================================================================
# --- CORRECTION 1 : CRÉER UNE INSTANCE GLOBALE DU BOT ---
# Cela permet au site Flask d'accéder aux informations du bot (comme la liste des serveurs).
bot_instance = MyBot()
# ==============================================================================

# --- Initialisation de l'application Flask (le site web) ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# --- Configuration OAuth2 Discord (inchangée) ---
API_BASE_URL = 'https://discord.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
CLIENT_ID = os.getenv('OAUTH2_CLIENT_ID')
CLIENT_SECRET = os.getenv('OAUTH2_CLIENT_SECRET')
REDIRECT_URI = os.getenv('OAUTH2_REDIRECT_URI')
SCOPE = ['identify', 'guilds']

# --- Liens importants (inchangés) ---
INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=1413462643598950421&permissions=8&scope=bot%20applications.commands"
SUPPORT_SERVER_LINK = "https://discord.gg/SpXQXy3UD2"

# --- Fonctions Helper OAuth2 (inchangées) ---
def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=CLIENT_ID, token=token, state=state, scope=scope,
        redirect_uri=REDIRECT_URI, auto_refresh_kwargs={
            'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL, token_updater=token_updater)

# --- Routes du site (inchangées, sauf /dashboard) ---

@app.route('/')
def home():
    return render_template('index.html', invite_link=INVITE_LINK, support_link=SUPPORT_SERVER_LINK)

@app.route('/commands')
def commands():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, 'static', 'data', 'commands.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            command_categories = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        command_categories = []
        
    return render_template('commands.html', 
                           categories=command_categories,
                           invite_link=INVITE_LINK, 
                           support_link=SUPPORT_SERVER_LINK)

@app.route('/login')
def login():
    discord_session = make_session(scope=SCOPE)
    authorization_url, state = discord_session.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    if request.values.get('error'): return request.values['error']
    discord_session = make_session(state=session.get('oauth2_state'))
    token = discord_session.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'oauth2_token' not in session: return redirect(url_for('login'))
    
    discord_session = make_session(token=session.get('oauth2_token'))
    user = discord_session.get(API_BASE_URL + '/users/@me').json()
    user_guilds = discord_session.get(API_BASE_URL + '/users/@me/guilds').json()

    # ==============================================================================
    # --- CORRECTION 2 : LOGIQUE DE FILTRAGE DES SERVEURS ---
    
    # 1. On récupère la liste des IDs de serveurs où le bot est présent.
    #    On vérifie que le bot est bien prêt avant de demander la liste.
    bot_guild_ids = set()
    if bot_instance.is_ready():
        bot_guild_ids = {guild.id for guild in bot_instance.guilds}

    # 2. On filtre la liste des serveurs de l'utilisateur.
    managed_guilds = []
    for guild in user_guilds:
        # On garde le serveur si l'utilisateur est admin ET le bot est présent.
        is_admin = int(guild['permissions']) & 0x8
        bot_is_present = int(guild['id']) in bot_guild_ids
        
        if is_admin and bot_is_present:
            managed_guilds.append(guild)
    
    # On passe la liste filtrée (managed_guilds) au template.
    return render_template(
        'dashboard.html', 
        user=user, 
        guilds=managed_guilds, # <-- MODIFIÉ
        invite_link=INVITE_LINK,
        support_link=SUPPORT_SERVER_LINK
    )
    # ==============================================================================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- Lancement du bot et du site ---

def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # ==============================================================================
        # --- CORRECTION 3 : UTILISER L'INSTANCE GLOBALE ---
        # On lance l'instance du bot que nous avons créée plus haut.
        bot_instance.run(TOKEN)
        # ==============================================================================

if __name__ == '__main__':
    # ==============================================================================
    # --- TEST DE DIAGNOSTIC : ON DÉSACTIVE LE BOT ---
    # Mettez un '#' devant les 4 lignes suivantes pour empêcher le bot de démarrer.
    # print(">>> Démarrage du bot Discord en arrière-plan...")
    # bot_thread = threading.Thread(target=run_bot)
    # bot_thread.daemon = True
    # bot_thread.start()
    # ==============================================================================

    # On ne démarre QUE le serveur web
    from waitress import serve
    port = int(os.environ.get("PORT", 5001))
    print(f">>> Démarrage du serveur web Waitress SEUL sur le port {port}")
    serve(app, host="0.0.0.0", port=port)