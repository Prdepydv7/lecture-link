from telethon import TelegramClient
import re
import json
from datetime import datetime, timedelta
import os
import asyncio

# Load environment variables
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_username = os.getenv('CHANNEL_USERNAME')
bot_token = os.getenv('BOT_TOKEN')

if not all([api_id, api_hash, channel_username, bot_token]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, CHANNEL_USERNAME, or BOT_TOKEN")

# Keyword mapping
keyword_map = {
    'physics': ('Physics', [
        'physical world', 'units and measurements', 'motion in a straight line', 'motion in a plane',
        'laws of motion', 'work energy power', 'rotational motion', 'gravitation',
        'mechanical properties of solids', 'mechanical properties of fluids',
        'thermal properties', 'thermodynamics', 'kinetic theory', 'oscillations', 'waves'
    ]),
    'phy': ('Physics', []),
    'chemistry': ('Chemistry', [
        'basic concepts of chemistry', 'structure of atom', 'classification of elements',
        'chemical bonding', 'states of matter', 'thermodynamics', 'equilibrium',
        'redox reactions', 'hydrogen', 's-block', 'p-block', 'organic chemistry',
        'hydrocarbons', 'environmental chemistry'
    ]),
    'chem': ('Chemistry', []),
    'math': ('Mathematics', [
        'sets', 'relations and functions', 'trigonometric functions', 'mathematical induction',
        'complex numbers', 'linear inequalities', 'permutations and combinations',
        'binomial theorem', 'sequences and series', 'straight lines', 'conic sections',
        '3d geometry', 'limits and derivatives', 'mathematical reasoning', 'statistics', 'probability'
    ]),
    'mathematics': ('Mathematics', []),
    'maths': ('Mathematics', [])
}

client = TelegramClient('bot_session', api_id, api_hash)

def categorize_lecture(text):
    text = text.lower()
    for keyword, (subject, chapters) in keyword_map.items():
        if keyword in text:
            for chapter in chapters:
                if chapter in text:
                    return subject, chapter
            return subject, 'Unknown'
    return 'Unknown', 'Unknown'

async def extract_youtube_links():
    youtube_links = []
    last_update = datetime.now() - timedelta(days=3650)  # 10 years if you want all messages

    async with client:
        await client.start(bot_token=bot_token)

        async for message in client.iter_messages(channel_username, limit=None):  # Remove limit to get all
            if message.date < last_update:
                break
            if message.text:
                urls = re.findall(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}|https?://youtu\.be/[\w-]{11})', message.text)
                for url in urls:
                    subject, chapter = categorize_lecture(message.text)
                    youtube_links.append({
                        'url': url,
                        'title': message.text[:100].strip(),
                        'date': message.date.strftime('%Y-%m-%d'),
                        'subject': subject,
                        'chapter': chapter
                    })
            await asyncio.sleep(0.05)  # Safer rate limit

    return youtube_links

async def save_to_json(data, filename='lectures.json'):
    try:
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    existing_urls = {item['url'] for item in existing_data}
    new_data = [item for item in data if item['url'] not in existing_urls]
    updated_data = existing_data + new_data

    with open(filename, 'w') as f:
        json.dump(updated_data, f, indent=4)

async def main():
    print("🔁 Extracting YouTube links from Telegram...")
    links = await extract_youtube_links()
    await save_to_json(links)
    print(f"✅ Extracted {len(links)} new links and saved to lectures.json")

# Run the main function
if __name__ == '__main__':
    asyncio.run(main())
