# External imports
import discord
import logging
import yaml
# No internal imports

# Set basic logging config
logging.basicConfig(filename='discord.log', filemode='a', format='%(asctime)s %(message)s', level='ERROR')

# Loads the yaml file
with open('bot.yml', 'r') as file:
    BOT_YAML = yaml.load(file, Loader=yaml.SafeLoader)
# Initializes the discord bot client
N_RUS_BOT = discord.Client()
# Loads the bot token
with open('token.txt', r) as file:
    TOKEN = file.read()
# Runs the bot
N_RUS_BOT.run(TOKEN)
