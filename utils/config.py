import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# The sheet or tab name of the data. Must be located in the same spreadsheet as SPREADSHEET_ID
GAME_LOG_SHEET_NAME = os.getenv("GAME_LOG_SHEET_NAME", "Game Log")
TEAM_INFO_SHEET_NAME = os.getenv("TEAM_INFO_SHEET_NAME", "Teams")
STANDINGS_SHEET_ID = os.getenv("STANDINGS_SHEET_ID", "0")  # Sheet ID for the standings tab, i.e. position in sheet list. 0-indexed.

# Wiki configuration
MEDIAWIKI_BOT_USERNAME = os.getenv("MEDIAWIKI_BOT_USERNAME")
MEDIAWIKI_BOT_PASSWORD = os.getenv("MEDIAWIKI_BOT_PASSWORD")
MEDIAWIKI_SITE_URL = os.getenv("MEDIAWIKI_SITE_HOST") # Do not include https:// !!!
MEDIAWIKI_API_PATH = os.getenv("MEDIAWIKI_API_PATH", "/")
MEDIAWIKI_PAGE_TITLE = os.getenv("MEDIAWIKI_PAGE_TITLE")

# The following are optional
# Channel where debug embeds will be sent to
LOGGING_CHANNEL_ID = (int(os.getenv("LOGGING_CHANNEL_ID")) if os.getenv("LOGGING_CHANNEL_ID") else None)
# Channel where standings screenshot will be posted
STANDINGS_CHANNEL_ID = int(os.getenv("STANDINGS_CHANNEL_ID")) if os.getenv("STANDINGS_CHANNEL_ID") else None
# Role to ping for critical failures in the logging channel
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID")) if os.getenv("ADMIN_ROLE_ID") else None