const { Client, GatewayIntentBits, EmbedBuilder } = require('discord.js');
const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages]
});

// ===== CONFIGURATION =====
const CHANNEL_ID = '1420017903717322778'; // Remplace par l'ID du salon où envoyer les messages
const BOT_TOKEN = 'MTQxMzQ2MjY0MzU5ODk1MDQyMQ.GdLZ9l.65LnQlOnzZvK5jsvGrwFLYMNAU0m8X6tytwNbA';     // Remplace par le token de ton bot
// =========================

client.once('ready', () => {
  console.log(${client.user.tag} est connecté !);
  sendStatusMessage('en ligne', 0x00FF00); // vert
});

// Fonction pour envoyer un message stylé
function sendStatusMessage(statusText, color) {
  const channel = client.channels.cache.get(CHANNEL_ID);
  if (!channel) return console.log('Salon introuvable !');

  const embed = new EmbedBuilder()
    .setTitle('Statut du bot')
    .setDescription(statusText === 'en ligne' ? '✅ Le bot est en ligne !' : '⚠️ Le bot est hors ligne !')
    .setColor(color)
    .setTimestamp();

  channel.send({ embeds: [embed] });
}

// Message quand le bot se déconnecte proprement
process.on('exit', () => sendStatusMessage('hors ligne', 0xFF0000)); // rouge
process.on('SIGINT', () => process.exit());
process.on('SIGTERM', () => process.exit());

// Connexion du bot
client.login(BOT_TOKEN);
