# --- Imports nécessaires ---
import threading
import asyncio
import os
import json # Assurez-vous que json est importé
from flask import Flask, render_template, redirect, url_for, session, request
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session # Importation nécessaire

# --- IMPORTER VOTRE BOT ---
# Assurez-vous d'avoir renommé votre ancien "main.py" du bot en "bot_main.py"
# et qu'il se trouve dans le même dossier que ce fichier.
from bot_main import MyBot, TOKEN # type: ignore

# --- Configuration initiale ---
load_dotenv()
# Permet à OAuthlib d'utiliser HTTP pour le développement local
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- Initialisation de l'application Flask (le site web) ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# --- Configuration OAuth2 Discord ---
API_BASE_URL = 'https://discord.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
CLIENT_ID = os.getenv('OAUTH2_CLIENT_ID')
CLIENT_SECRET = os.getenv('OAUTH2_CLIENT_SECRET')
REDIRECT_URI = os.getenv('OAUTH2_REDIRECT_URI')
SCOPE = ['identify', 'guilds']

# --- Liens importants (personnalisés) ---
INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=1413462643598950421&permissions=8&scope=bot%20applications.commands"
SUPPORT_SERVER_LINK = "https://discord.gg/SpXQXy3UD2"

# --- Fonctions Helper OAuth2 ---
def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=CLIENT_ID, token=token, state=state, scope=scope,
        redirect_uri=REDIRECT_URI, auto_refresh_kwargs={
            'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL, token_updater=token_updater)

# --- Routes du site ---

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
                           support_link=SUPPORT_SERVER_LINK
    )

# ... (vos routes /login, /callback, /dashboard, /logout restent inchangées) ...
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
    guilds = discord_session.get(API_BASE_URL + '/users/@me/guilds').json()
    admin_guilds = [g for g in guilds if int(g['permissions']) & 0x8]
    return render_template(
        'dashboard.html', 
        user=user, 
        guilds=admin_guilds,
        invite_link=INVITE_LINK,
        support_link=SUPPORT_SERVER_LINK)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================================================================
# --- CORRECTION APPLIQUÉE ICI : Lancement du bot et du site ---

def run_bot():
    """Fonction qui sera exécutée dans un thread séparé pour lancer le bot."""
    # Chaque thread a besoin de sa propre boucle d'événements asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = MyBot()
    # bot.run() est bloquant, il va donc faire tourner la boucle pour nous
    bot.run(TOKEN)

if __name__ == '__main__':
        # 1. Démarrer le bot Discord en arrière-plan
        print(">>> Démarrage du bot Discord en arrière-plan...")
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()

        # 2. Démarrer le serveur web Gunicorn (pour Render)
        print(">>> Démarrage du serveur web Gunicorn...")
        # Cette partie est différente du code de développement local
        from waitress import serve
        serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))

# ==============================================================================
