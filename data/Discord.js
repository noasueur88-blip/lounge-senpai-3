const { Client, GatewayIntentBits } = require('discord.js');
const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages]
});

// ID du salon où envoyer le message
const CHANNEL_ID = '1420017903717322778';

client.once('ready', () => {
  console.log(${client.user.tag} est connecté !);

  const channel = client.channels.cache.get(CHANNEL_ID);
  if (channel) {
    channel.send('✅ Le bot est en ligne !');
  }
});

// Connexion du bot
client.login('MTQxMzQ2MjY0MzU5ODk1MDQyMQ.GdLZ9l.65LnQlOnzZvK5jsvGrwFLYMNAU0m8X6tytwNbA');
