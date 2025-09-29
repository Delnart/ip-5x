import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

from config import COMMAND_PREFIX
from database.db import db
from utils.logs import Logger

# Load environment variables
load_dotenv()

# Bot intents
intents = nextcord.Intents.all()

# Initialize bot
bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None
)

# Global logger instance
logger = None

@bot.event
async def on_ready():
    """Bot startup event"""
    global logger
    
    print("=" * 50)
    print(f"🦎 Bot logged in as {bot.user.name}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print("=" * 50)
    
    # Connect to database
    await db.connect()
    
    # Initialize logger
    logger = Logger(bot)
    
    # Load cogs
    print("\n🔄 Loading cogs...")
    cogs = [
        'cogs.welcome',
        'cogs.voice',
        'cogs.moderation',
        'cogs.groups'
    ]
    
    for cog in cogs:
        try:
            bot.load_extension(cog)
            print(f"✅ Loaded: {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")
    
    print("\n✅ Bot is ready!")
    print("=" * 50)
    
    # Set bot status
    await bot.change_presence(
        activity=nextcord.Game(name="🦎 Керую потоком ІП-5x")
    )

@bot.event
async def on_member_update(before, after):
    """Handle member role updates"""
    if before.roles != after.roles:
        if logger:
            await logger.log_role_update(after, before.roles, after.roles)

@bot.event
async def on_message_delete(message):
    """Handle message deletion"""
    if logger and not message.author.bot:
        await logger.log_message_delete(message)

@bot.event
async def on_message_edit(before, after):
    """Handle message edits"""
    if logger and not before.author.bot:
        await logger.log_message_edit(before, after)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    from utils.embeds import error_embed
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            embed=error_embed(
                "Недостатньо прав",
                "У вас немає прав для використання цієї команди."
            )
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=error_embed(
                "Помилка",
                f"Не вистачає аргументу: `{error.param.name}`"
            )
        )
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(
            embed=error_embed(
                "Помилка",
                "Користувач не знайдений."
            )
        )
    else:
        print(f"❌ Command error: {error}")
        await ctx.send(
            embed=error_embed(
                "Помилка",
                "Сталася несподівана помилка при виконанні команди."
            )
        )

# Run bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ Error: DISCORD_TOKEN not found in .env file")
    else:
        try:
            bot.run(token)
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")