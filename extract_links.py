from telethon import TelegramClient
import re
import json
from datetime import datetime
import os

# Telegram API credentials (loaded from environment variables for GitHub Actions)
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = os.getenv('CHANNEL_USERNAME')

# Check if credentials are provided
if not all([api_id, api_hash, channel_username]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, or CHANNEL_USERNAME")

# Chapter keywords for Class 11 PCM
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

# Initialize Telegram client
client = TelegramClient('session_name', int(api_id), api_hash)

def categorize_lecture(text):
    text = text.lower()
    # Identify subject
    if any(keyword in text for keyword in ['physics', 'phy']):
        subject = 'Physics'
        chapters = chapter_keywords['Physics']
    elif any(keyword in text for keyword in ['chemistry', 'chem']):
        subject = 'Chemistry'
        chapters = chapter_keywords['Chemistry']
    elif any(keyword in text for keyword in ['math', 'mathematics', 'maths']):
        subject = 'Mathematics'
        chapters = chapter_keywords['Mathematics']
    else:
        return 'Unknown', 'Unknown'

    # Identify chapter
    for chapter in chapters:
        if chapter in text:
            return subject, chapter
    return subject, 'Unknown'

async def extract_youtube_links():
    youtube_links = []
    async with client:
        async for message in client.iter_messages(channel_username, limit=100):  # Adjust limit as needed
            if message.text:
                # Extract YouTube URLs
                urls = re.findall(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}|https?://youtu\.be/[\w-]{11})', message.text)
                for url in urls:
                    subject, chapter = categorize_lecture(message.text)
                    youtube_links.append({
                        'url': url,
                        'title': message.text[:50].strip(),  # First 50 chars as title
                        'date': message.date.strftime('%Y-%m-%d'),
                        'subject': subject,
                        'chapter': chapter
                    })
    return youtube_links

async def save_to_json(data, filename='lectures.json'):
    try:
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Avoid duplicates by URL
    existing_urls = {item['url'] for item in existing_data}
    new_data = [item for item in data if item['url'] not in existing_urls]
    updated_data = existing_data + new_data

    with open(filename, 'w') as f:
        json.dump(updated_data, f, indent=4)

async def main():
    links = await extract_youtube_links()
    await save_to_json(links)

if _name_ == '_main_':
    with client:
        client.loop.run_until_complete(main())
