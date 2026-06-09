# CHL Scorekeeper
The CHL Scorekeeper is a custom scorekeeping Discord bot written for the Continental Hockey League on the MRT server. The bot provides services by automatically appending an entry to the Google Sheets Game Log, posting an updated standings screenshot to the standings channel, and updating tables on the MediaWiki page.

Since the project is highly specialized for the CHL, prospective users should fork the project and modify the source code to suit their needs.

## Features
The bot provides 3 commands:
* `submit`: The main command of the bot. It runs the pipeline mentioned above and is the main use for the bot.
* `updateteams`: Admin command, updates the team list in the bot's memory by pulling from Google Sheets again.
* `updatestandings`: Admin command, updates the screenshot posted in the standings channel only. Good for refreshing standings after manually updating the sheets.

User input is sanitized and validated to ensure that they conform to the CHL rules. The bot also has a Discord logging feature for debugging purposes. All `submit` runs are logged to a configurable Discord channel as embeds, which includes helpful details such as the command ran, error message, and stage of failure.

## Requirements
Dependency requirements are listed in `requirements.txt`.

We do not provide hosting or API keys. Therefore, you must obtain credentials and find hosting yourself. The bot requires the following API credentials:

* Discord bot token, from the Discord Dev Portal
* A `credentials.json` file from a Google service account with the Sheets API enabled
* MediaWiki account username and bot password

Aside from `credentials.json`, all credentials and settings should be stored in a `.env` file. Please see `utils/config.py` for a list of options that must be configured.

## Gallery
<img width="788" height="470" alt="Standings" src="https://github.com/user-attachments/assets/d7deef7a-f3a8-4737-a8a1-ce374f18c222" />
<img width="615" height="106" alt="Message" src="https://github.com/user-attachments/assets/40579723-74c8-4928-894d-c94df08a6e26" />
<img width="665" height="346" alt="Success" src="https://github.com/user-attachments/assets/ff03a5ce-4dd5-40fa-9965-ebfb4ee12170" />
<img width="671" height="226" alt="Failure" src="https://github.com/user-attachments/assets/6a1c4380-a2ee-4c66-b71d-90971ec3a30a" />
