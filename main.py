import discord
from discord.ext import commands
from utils.config import DISCORD_TOKEN, MEDIAWIKI_API_PATH, MEDIAWIKI_BOT_PASSWORD, MEDIAWIKI_BOT_USERNAME, MEDIAWIKI_SITE_URL
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from mwclient import Site
import logging

from utils.teams import load_teams


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "credentials.json"

intents = discord.Intents.default()
logger = logging.getLogger("discord")


class CHLBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)

    async def setup_hook(self):
        try:
            logger.info("Initializing Google Sheets API...")
            creds = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            self.sheets = build("sheets", "v4", credentials=creds).spreadsheets()
            logger.info("Google Sheets API successfully connected.")
            
            logger.info("Initializing MediaWiki API...")
            self.wiki = Site(MEDIAWIKI_SITE_URL, path=MEDIAWIKI_API_PATH)
            self.wiki.login(
                username=MEDIAWIKI_BOT_USERNAME, password=MEDIAWIKI_BOT_PASSWORD
            )
            logger.info("MediaWiki API successfully connected.")
        except Exception as e:
            logger.critical(f"Failed to initialize API connection: {e}")
            raise e
        
        load_teams()

        await self.load_extension("commands.submit")
        await self.load_extension("commands.updateteams")
        await self.load_extension("commands.updatestandings")
        await self.tree.sync()


bot = CHLBot()
bot.run(DISCORD_TOKEN)
