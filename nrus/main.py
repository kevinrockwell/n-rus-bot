import json
import logging
import os
import sys

import bot


def main():
    # Set basic logging config
    dir_name = os.path.split(__file__)[:-1]
    logging.basicConfig(
        filename=os.path.join(*dir_name, 'discord.log'),
        filemode='a',
        format='%(asctime)s %(message)s',
        level='ERROR',
    )

    # Loads the bot token
    with open(os.path.join(*dir_name, 'settings.json')) as file:
        settings = json.load(file)

    nrus = bot.NRus(settings)
    # Runs the bot
    nrus.run()


if __name__ == '__main__':
    main()
