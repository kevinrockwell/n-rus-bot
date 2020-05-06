import json
import logging
import sys

import bot

# Set basic logging config
logging.basicConfig(filename='../../discord.log', filemode='a', format='%(asctime)s %(message)s', level='ERROR')


# Loads the bot token
with open(sys.argv[1]) as file:
    settings = json.load(file)

bot = bot.NRus(settings)
# Runs the bot
bot.run()
