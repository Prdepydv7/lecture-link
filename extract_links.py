from telethon import TelegramClient
import re
import json
from datetime import datetime
import os
import asyncio

# Load Telegram credentials from environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = os.getenv('CHANNEL_USERNAME')

# Validation
if not all([api_id, api_hash, channel_username]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, or CHANNEL_USERNAME")

# Chapter keywords
chapter_keywords = {
    'Physics': [
        'physical world', 'units and measurements', 'motion in a straight line', 'motion in a plane',
        'laws of motion', 'work energy power', 'rotational motion', 'gravitation',
        'mechanical properties of solids', 'mechanical properties of fluids',
        'thermal properties', 'thermodynamics', 'kinetic theory', 'oscillations', 'waves'
    ],
    'Chemistry': [
        'basic concepts of chemistry', 'structure of atom', 'classification of elements',
        'chemical bonding', 'states of matter', 'thermodynamics', 'equilibrium',
        'redox reactions', 'hydrogen', 's-block', 'p-block', 'organic chemistry',
        'hydrocarbons', 'environmental chemistry'
    ],
    'Mathematics': [
        'sets', 'relations and functions', 'trigonometric functions', 'mathematical induction',
        'complex numbers', 'linear inequalities', 'permutations and combinations',
        'binomial theorem', 'sequences and series', 'straight lines', 'conic sections',
        '3d geometry', 'limits and derivatives', 'mathematical reasoning', 'statistics', 'probability'
    ]
}

# Create Telegram client
client = TelegramClient('session_name', int(api_id), api_hash)

# Subject + Chapter classifier
def categorize_lecture(text):
    text = text.lower()
    if any(k in text for k in ['physics', 'phy']):
        subject = 'Physics'
        chapters = chapter_keywords['Physics']
    elif any(k in text for k in ['chemistry', 'chem']):
        subject = 'Chemistry'
        chapters = chapter_keywords['Chemistry']
    elif any(k in text for k in ['math', 'mathematics', 'maths']):
        subject = 'Mathematics'
        chapters = chapter_keywords['Mathematics']
    else:
        return 'Unknown', 'Unknown'
    
    for chapter in chapters:
        if chapter in text:
            return subject, chapter
    return subject, 'Unknown'

# Extract YouTube links
async def extract_youtube_links():
    youtube_links = []
    async with client:
        async for message in client.iter_messages(channel_username, limit=1000):
            if message.text:
                urls = re.findall(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}|https?://youtu\.be/[\w-]{11})', message.text)
                for url in urls:
                    subject, chapter = categorize_lecture(message.text)
                    youtube_links.append({
                        'url': url,
                        'title': message.text[:70].strip(),
                        'date': message.date.strftime('%Y-%m-%d'),
                        'subject': subject,
                        'chapter': chapter
                    })
    return youtube_links

# Save to JSON file
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

# Main async function
async def main():
    print("🔁 Extracting YouTube links from Telegram...")
    links = await extract_youtube_links()
    print(f"✅ Found {len(links)} new video(s)")
    await save_to_json(links)
    print("💾 Data saved to lectures.json")

# Runner
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError:
        # For environments like Windows/Jupyter
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
