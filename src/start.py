
import os
import sys
import logging
from dotenv import load_dotenv

from webex_bot import WebexBot
from commands.echo import EchoCommand
from commands.llm_chat import LLM_Chat_Command
from commands.help import HelpCommand

logging.basicConfig(level=logging.INFO, format='%(message)s')

log = logging.getLogger(__name__)

load_dotenv()

access_token = os.getenv('WEBEX_API_TOKEN', None)
if not access_token:
    log.error("cannot read 'WEBEX_API_TOKEN' env variable")
    sys.exit(1)

open_ai_token = os.getenv('OPENAI_API_KEY', None)
if not open_ai_token:
    log.error("cannot read 'OPENAI_API_KEY' env variable")
    sys.exit(1)

approved_users = [
    "mani.amoozadeh2@gmail.com",
    "mamoozad@cisco.com"
]

bot = WebexBot(teams_bot_token=access_token, approved_users=approved_users)

#########

me = bot.get_me_info()
all_commands = bot.get_commands()

help_command = HelpCommand(
    bot_name="Webex Bot",
    bot_help_subtitle="Here are my available commands. Click one to begin.",
    bot_help_image=me.avatar,
    commands=all_commands)

#########

bot.add_command(EchoCommand())
bot.add_command(LLM_Chat_Command(open_ai_token))
bot.add_command(help_command)

bot.run()
