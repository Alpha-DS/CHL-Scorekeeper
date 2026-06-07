import asyncio
import io
import time
import requests
import discord
import fitz
from PIL import Image, ImageChops
from utils.config import SPREADSHEET_ID, STANDINGS_CHANNEL_ID, STANDINGS_SHEET_ID

# Crop out whitespace from downloaded PDF
def autocrop_whitespace(image_bytes: bytes) -> io.BytesIO:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()

    if bbox:
        padded_bbox = (
            max(0, bbox[0] - 5),
            max(0, bbox[1] - 5),
            min(img.width, bbox[2] + 10),
            min(img.height, bbox[3] + 10),
        )
        img = img.crop(padded_bbox)

    cropped_output = io.BytesIO()
    img.save(cropped_output, format="PNG")
    cropped_output.seek(0)
    return cropped_output


async def update_standings_screenshot(bot: discord.Client, screenshot_delay: int = 3):
    if not STANDINGS_CHANNEL_ID or not SPREADSHEET_ID:
        return

    channel = bot.get_channel(STANDINGS_CHANNEL_ID)
    if not channel:
        return
    
    # Small delay for Google Sheets calculations to finish
    await asyncio.sleep(screenshot_delay)

    export_url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?"
        f"format=pdf&gid={STANDINGS_SHEET_ID}&scale=4&gridlines=true"
        f"&printtitle=false&sheetnames=false&fzr=false"
        f"&top_margin=0.00&bottom_margin=0.00&left_margin=0.00&right_margin=0.00"
    )

    creds = bot.sheets._http.credentials
    if creds and not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())

    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(export_url, headers=headers, timeout=5)

    if response.status_code != 200:
        raise RuntimeError(
            f"❌ Google API rejected PDF export with status code: {response.status_code}"
        )

    # Convert PDF to PNG
    pdf_document = fitz.open(stream=response.content, filetype="pdf")
    page = pdf_document.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
    raw_png_bytes = pix.tobytes("png")
    clean_image_stream = autocrop_whitespace(raw_png_bytes)
    discord_file = discord.File(fp=clean_image_stream, filename="standings.png")
    
    # Message with timestamp
    current_unix_time = int(time.time())
    timestamp_message = f"🏆 **CHL Standings**\nLast Updated: <t:{current_unix_time}:f> (<t:{current_unix_time}:R>)"

    # Locate last bot message to edit it, or post new message if none found
    try:
        last_message = None
        async for message in channel.history(limit=5):
            if message.author == bot.user:
                last_message = message
                break

        if last_message:
            await last_message.edit(attachments=[discord_file], content=timestamp_message)
        else:
            await channel.send(file=discord_file, content=timestamp_message)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to send standings update to Discord: {str(e)}")