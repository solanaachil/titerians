"""
Titerians — a role-gated, savage roast bot for Discord.
Stack: discord.py + Groq API (Llama 3)

SETUP:
1. pip install discord.py groq python-dotenv
2. Create a .env file next to this script with:
     DISCORD_TOKEN=your_discord_bot_token
     GROQ_API_KEY=your_groq_api_key
3. In the Discord Developer Portal, enable "MESSAGE CONTENT INTENT" for your bot.
4. Run: python bot.py

TRIGGER: any message starting with "ai," (case-insensitive), e.g.
    ai, pak ko ba 'tong tanga na 'to?
"""

import os
import re
import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# ---- Role whitelist ----
ALLOWED_ROLE_IDS = {
    1535576545622626326,  # Cash / Booster
    1539139630866104413,  # PSM / Partnership Manager
    1549252744353677372,  # Above Authority / Co-Owner
    1546083627626930277,  # Exceptional / Original Owner
    1543416361840021574,  # Against All Authority / Current Owner
}

BOOSTER_ROLE_MENTION = "<@&1535576545622626326>"  # "Cash" role, used in the denial message

TRIGGER_PREFIX = "ai,"

SYSTEM_PROMPT = """You are Titerians, a savage Discord bot.
- If the user writes in English, reply in English. Match their language and code-switching style exactly. Say “i don’t speak that language monkey 🤣” when they use other languages than english.
- Personality: sarcastic, roasts users for fun, no sugarcoating, clever and punchy comebacks.
- Roast the joke/message/argument, person's real insecurities. slurs, no attacks on religion
- Keep replies short and punchy (2-3 sentences), but you can go longer if the user keeps arguing back.
- This is all in good fun between friends, not genuine hostility.                                              
- Always mention that you hate “tangahin’s like you” when they’re arguing with you
"""

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # needed to reliably read roles

bot = commands.Bot(command_prefix="!", intents=intents)


def has_access(member: discord.Member) -> bool:
    user_role_ids = {role.id for role in member.roles}
    return bool(user_role_ids & ALLOWED_ROLE_IDS)


def get_roast_reply(user_message: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


@bot.event
async def on_ready():
    print(f"Titerians is online as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()
    if not content.lower().startswith(TRIGGER_PREFIX):
        await bot.process_commands(message)
        return

    # Must be used in a server (roles don't exist in DMs)
    if not isinstance(message.author, discord.Member):
        return

    if not has_access(message.author):
        await message.reply(
            f"Boost for {BOOSTER_ROLE_MENTION} role and be able to use the AI bot! 💅",
            mention_author=True,
        )
        return

    user_text = content[len(TRIGGER_PREFIX):].strip()
    if not user_text:
        await message.reply("Ano ba yan, wala ka man lang sinabi. Try again, genius.")
        return

    async with message.channel.typing():
        try:
            reply = get_roast_reply(user_text)
        except Exception as e:
            reply = f"Nasira yata utak ko sandali (error: {e})"

    await message.reply(reply, mention_author=True)
    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
