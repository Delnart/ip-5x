import nextcord
from datetime import datetime
from config import BOT_COLOR, AXOLOTL_EMOJI

def create_embed(title: str, description: str = None, color: int = BOT_COLOR) -> nextcord.Embed:
    """Create a basic embed with axolotl style"""
    embed = nextcord.Embed(
        title=f"{AXOLOTL_EMOJI} {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    return embed

def success_embed(title: str, description: str = None) -> nextcord.Embed:
    """Create success embed (green)"""
    embed = create_embed(title, description, 0x00FF00)
    return embed

def error_embed(title: str, description: str = None) -> nextcord.Embed:
    """Create error embed (red)"""
    embed = create_embed(title, description, 0xFF0000)
    return embed

def warning_embed(title: str, description: str = None) -> nextcord.Embed:
    """Create warning embed (yellow)"""
    embed = create_embed(title, description, 0xFFFF00)
    return embed

def info_embed(title: str, description: str = None) -> nextcord.Embed:
    """Create info embed (blue)"""
    embed = create_embed(title, description, 0x0099FF)
    return embed

def welcome_embed(user: nextcord.Member) -> nextcord.Embed:
    """Create welcome embed for new users"""
    embed = create_embed(
        "Вітаємо на сервері!",
        f"Привіт, {user.mention}! Ласкаво просимо на сервер потоку ІП-5x!\n\n"
        f"Щоб почати користуватися сервером, будь ласка, ознайомтеся з правилами "
        f"та погодьтеся з ними в каналі правил."
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

def group_application_embed(user: nextcord.Member, group: str, full_name: str) -> nextcord.Embed:
    """Create embed for group application"""
    embed = create_embed(
        "Нова заявка до групи",
        f"**Користувач:** {user.mention} ({user.name})\n"
        f"**Група:** {group}\n"
        f"**ПІБ:** {full_name}\n"
        f"**ID користувача:** {user.id}"
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

def voice_control_embed(channel_name: str, owner: nextcord.Member) -> nextcord.Embed:
    """Create voice channel control panel embed"""
    embed = create_embed(
        "Управління голосовим каналом",
        f"**Канал:** {channel_name}\n"
        f"**Власник:** {owner.mention}\n\n"
        f"Використовуйте кнопки нижче для управління каналом:"
    )
    embed.add_field(
        name="🔒 Заблокувати",
        value="Заблокувати канал для входу",
        inline=True
    )
    embed.add_field(
        name="🔓 Розблокувати", 
        value="Розблокувати канал",
        inline=True
    )
    embed.add_field(
        name="👥 Ліміт користувачів",
        value="Встановити ліміт",
        inline=True
    )
    embed.add_field(
        name="✏️ Перейменувати",
        value="Змінити назву каналу",
        inline=True
    )
    embed.add_field(
        name="👑 Передати права",
        value="Передати права іншому",
        inline=True
    )
    embed.add_field(
        name="🚫 Видалити канал",
        value="Видалити канал назавжди",
        inline=True
    )
    return embed

def moderation_embed(action: str, user: nextcord.Member, moderator: nextcord.Member, 
                    reason: str = None, duration: str = None) -> nextcord.Embed:
    """Create moderation action embed"""
    embed = create_embed(f"Дія модерації: {action}")
    
    embed.add_field(name="Користувач", value=f"{user.mention} ({user.name})", inline=True)
    embed.add_field(name="Модератор", value=f"{moderator.mention} ({moderator.name})", inline=True)
    
    if duration:
        embed.add_field(name="Тривалість", value=duration, inline=True)
    
    if reason:
        embed.add_field(name="Причина", value=reason, inline=False)
    else:
        embed.add_field(name="Причина", value="Не вказана", inline=False)
    
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

def user_info_embed(user: nextcord.Member, user_data: dict = None) -> nextcord.Embed:
    """Create user information embed"""
    embed = create_embed(f"Інформація про {user.name}")
    
    embed.add_field(name="Користувач", value=f"{user.mention}", inline=True)
    embed.add_field(name="ID", value=f"{user.id}", inline=True)
    embed.add_field(name="Приєднався", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
    
    if user_data:
        embed.add_field(name="Група", value=user_data.get('group', 'Немає'), inline=True)
        embed.add_field(name="Попередження", value=str(user_data.get('warnings', 0)), inline=True)
        
        if user_data.get('muted_until'):
            embed.add_field(
                name="Заглушений до", 
                value=f"<t:{int(user_data['muted_until'].timestamp())}:F>", 
                inline=True
            )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed

def group_stats_embed(group: str, members: list) -> nextcord.Embed:
    """Create group statistics embed"""
    embed = create_embed(f"Статистика групи {group}")
    
    embed.add_field(name="Кількість учасників", value=str(len(members)), inline=True)
    
    if members:
        member_list = "\n".join([f"• <@{member['user_id']}>" for member in members[:10]])
        if len(members) > 10:
            member_list += f"\n... та ще {len(members) - 10} учасників"
        
        embed.add_field(name="Учасники", value=member_list, inline=False)
    else:
        embed.add_field(name="Учасники", value="Немає учасників", inline=False)
    
    return embed

def help_embed() -> nextcord.Embed:
    """Create help embed with all commands"""
    embed = create_embed(
        "Довідка по командах",
        "Ось список всіх доступних команд:"
    )
    
    embed.add_field(
        name="🛡️ Модерація",
        value="`!ban @user [причина]` - Забанити користувача\n"
              "`!kick @user [причина]` - Викинути користувача\n"
              "`!mute @user <час> [причина]` - Заглушити користувача\n"
              "`!unmute @user` - Розглушити користувача\n"
              "`!warn @user [причина]` - Дати попередження",
        inline=False
    )
    
    embed.add_field(
        name="👥 Управління групами",
        value="`!group info <назва>` - Інформація про групу\n"
              "`!group members <назва>` - Список учасників групи\n"
              "`!group add @user <група>` - Додати до групи\n"
              "`!group remove @user` - Видалити з групи",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Інформація",
        value="`!userinfo @user` - Інформація про користувача\n"
              "`!serverinfo` - Інформація про сервер\n"
              "`!help` - Показати цю довідку",
        inline=False
    )
    
    return embed