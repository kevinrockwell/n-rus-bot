import json
import logging

import n_rus

# Set basic logging config
logging.basicConfig(filename='../../discord.log', filemode='a', format='%(asctime)s %(message)s', level='ERROR')


# Loads the bot token
with open('settings.json') as file:
    settings = json.load(file)

bot = n_rus.NRus(settings)
# Runs the bot
bot.run()
