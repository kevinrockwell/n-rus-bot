# External imports
import discord
import logging
import shlex
# No internal imports

# Set basic logging config
logging.basicConfig(filename='discord.log', filemode='a', format='%(asctime)s %(message)s', level='ERROR')

# Initializes the discord bot client
N_RUS_BOT = discord.Client()

COMMANDS = {
    'quote': [';quote', ';q']
}

@N_RUS_BOT.event
async def on_message(message):
    for alias in COMMANDS['quote']:
        if message.content.startswith(alias):
            content = shlex.split(message.content)
            print(content)

# Loads the bot token
with open('token.txt', 'r') as file:
    TOKEN = file.read()
# Runs the bot
N_RUS_BOT.run(TOKEN)
print('asdmklaskldlkasdkl')
