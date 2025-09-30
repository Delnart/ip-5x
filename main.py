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
    help_command=None  # We use custom help command
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
    print(f"🔧 Nextcord version: {nextcord.__version__}")
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
                f"Не вистачає аргументу: `{error.param.name}`\n"
                f"Використовуйте `!help` для перегляду команд."
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
    elif isinstance(error, commands.BadArgument):
        await ctx.send(
            embed=error_embed(
                "Помилка",
                "Неправильний аргумент команди.\n"
                f"Використовуйте `!help` для перегляду правильного використання."
            )
        )
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(
            embed=error_embed(
                "Недостатньо прав",
                "У вас немає прав для використання цієї команди."
            )
        )
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            embed=error_embed(
                "Обмеження",
                f"Ця команда на перезарядці. Спробуйте через {error.retry_after:.1f} секунд."
            )
        )
    else:
        print(f"❌ Command error in {ctx.command}: {error}")
        await ctx.send(
            embed=error_embed(
                "Помилка",
                "Сталася несподівана помилка при виконанні команди."
            )
        )

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler for events"""
    import traceback
    print(f"❌ Error in event {event}:")
    traceback.print_exc()

# Simple commands for testing
@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency"""
    from utils.embeds import info_embed
    latency = round(bot.latency * 1000)
    embed = info_embed(
        "Pong! 🏓",
        f"Затримка: **{latency}ms**"
    )
    await ctx.send(embed=embed)

@bot.command(name="invite")
async def invite(ctx):
    """Get bot invite link"""
    from utils.embeds import info_embed
    
    # Generate invite link
    permissions = nextcord.Permissions(
        kick_members=True,
        ban_members=True,
        manage_channels=True,
        manage_roles=True,
        manage_messages=True,
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        moderate_members=True,
        move_members=True,
        connect=True,
        speak=True
    )
    
    invite_link = nextcord.utils.oauth_url(
        bot.user.id,
        permissions=permissions,
        scopes=["bot", "applications.commands"]
    )
    
    embed = info_embed(
        "Запросити бота",
        f"[Натисніть тут щоб запросити бота]({invite_link})"
    )
    await ctx.send(embed=embed)

@bot.command(name="about")
async def about(ctx):
    """Information about the bot"""
    from utils.embeds import create_embed
    
    embed = create_embed(
        "Про бота",
        "Бот для управління сервером Discord потоку ІП-5x"
    )
    
    embed.add_field(
        name="Версія",
        value="1.0.0",
        inline=True
    )
    
    embed.add_field(
        name="Nextcord",
        value=nextcord.__version__,
        inline=True
    )
    
    embed.add_field(
        name="Серверів",
        value=str(len(bot.guilds)),
        inline=True
    )
    
    embed.add_field(
        name="Користувачів",
        value=str(len(bot.users)),
        inline=True
    )
    
    embed.add_field(
        name="Команд",
        value=str(len(bot.commands)),
        inline=True
    )
    
    embed.add_field(
        name="Функції",
        value="• Авторизація через правила\n"
              "• Система груп\n"
              "• Тимчасові голосові канали\n"
              "• Модерація\n"
              "• Логування",
        inline=False
    )
    
    embed.set_footer(text=f"Запущено як {bot.user.name}")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await ctx.send(embed=embed)

# Run bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ Error: DISCORD_TOKEN not found in .env file")
        print("Please create a .env file and add your bot token:")
        print("DISCORD_TOKEN=your_token_here")
    else:
        try:
            print("🚀 Starting bot...")
            bot.run(token)
        except nextcord.LoginFailure:
            print("❌ Failed to login: Invalid token")
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")