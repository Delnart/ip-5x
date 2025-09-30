import nextcord
from datetime import datetime
from typing import Optional
from utils.embeds import create_embed, moderation_embed
from config import CHANNELS
from database.db import db

class Logger:
    def __init__(self, bot):
        self.bot = bot
    
    async def get_log_channel(self) -> Optional[nextcord.TextChannel]:
        """Get the log channel"""
        try:
            channel = self.bot.get_channel(CHANNELS['LOG'])
            return channel
        except Exception as e:
            print(f"❌ Failed to get log channel: {e}")
            return None
    
    async def log_user_join(self, member: nextcord.Member):
        """Log when user joins the server"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        embed = create_embed(
            "Користувач приєднався",
            f"**Користувач:** {member.mention} ({member.name})\n"
            f"**ID:** {member.id}\n"
            f"**Аккаунт створено:** <t:{int(member.created_at.timestamp())}:R>\n"
            f"**Приєднався:** <t:{int(member.joined_at.timestamp())}:F>",
            0x00FF00
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            await db.log_action("user_join", member.id, details={
                "username": member.name,
                "discriminator": member.discriminator
            })
        except Exception as e:
            print(f"❌ Failed to log user join: {e}")
    
    async def log_user_leave(self, member: nextcord.Member):
        """Log when user leaves the server"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        # Get user data from database
        user_data = await db.get_user(member.id)
        group = user_data.get('group', 'Немає') if user_data else 'Немає'
        
        embed = create_embed(
            "Користувач покинув сервер",
            f"**Користувач:** {member.mention} ({member.name})\n"
            f"**ID:** {member.id}\n"
            f"**Група:** {group}\n"
            f"**Покинув:** <t:{int(datetime.utcnow().timestamp())}:F>",
            0xFF0000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            await db.log_action("user_leave", member.id, details={
                "username": member.name,
                "group": group
            })
        except Exception as e:
            print(f"❌ Failed to log user leave: {e}")
    
    async def log_role_update(self, member: nextcord.Member, before_roles, after_roles):
        """Log role changes"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        added_roles = [role for role in after_roles if role not in before_roles]
        removed_roles = [role for role in before_roles if role not in after_roles]
        
        if not added_roles and not removed_roles:
            return
        
        description = f"**Користувач:** {member.mention} ({member.name})\n"
        
        if added_roles:
            roles_list = ", ".join([f"`{role.name}`" for role in added_roles])
            description += f"**Додані ролі:** {roles_list}\n"
        
        if removed_roles:
            roles_list = ", ".join([f"`{role.name}`" for role in removed_roles])
            description += f"**Видалені ролі:** {roles_list}\n"
        
        embed = create_embed("Зміна ролей", description, 0x0099FF)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            await db.log_action("role_update", member.id, details={
                "added_roles": [role.name for role in added_roles],
                "removed_roles": [role.name for role in removed_roles]
            })
        except Exception as e:
            print(f"❌ Failed to log role update: {e}")
    
    async def log_voice_channel_create(self, channel: nextcord.VoiceChannel, owner: nextcord.Member):
        """Log temporary voice channel creation"""
        log_channel = await self.get_log_channel()
        if not log_channel:
            return
        
        embed = create_embed(
            "Створено голосовий канал",
            f"**Канал:** {channel.name}\n"
            f"**Власник:** {owner.mention} ({owner.name})\n"
            f"**ID каналу:** {channel.id}",
            0x00FF00
        )
        
        try:
            await log_channel.send(embed=embed)
            await db.log_action("voice_create", owner.id, details={
                "channel_id": channel.id,
                "channel_name": channel.name
            })
        except Exception as e:
            print(f"❌ Failed to log voice channel creation: {e}")
    
    async def log_voice_channel_delete(self, channel_name: str, owner_id: int):
        """Log temporary voice channel deletion"""
        log_channel = await self.get_log_channel()
        if not log_channel:
            return
        
        embed = create_embed(
            "Видалено голосовий канал",
            f"**Канал:** {channel_name}\n"
            f"**Власник:** <@{owner_id}>",
            0xFF0000
        )
        
        try:
            await log_channel.send(embed=embed)
            await db.log_action("voice_delete", owner_id, details={
                "channel_name": channel_name
            })
        except Exception as e:
            print(f"❌ Failed to log voice channel deletion: {e}")
    
    async def log_moderation_action(self, action: str, target: nextcord.Member, 
                                   moderator: nextcord.Member, reason: str = None, 
                                   duration: str = None):
        """Log moderation actions"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        embed = moderation_embed(action, target, moderator, reason, duration)
        
        try:
            await channel.send(embed=embed)
            await db.log_action(f"moderation_{action}", target.id, moderator.id, {
                "reason": reason,
                "duration": duration,
                "target_username": target.name,
                "moderator_username": moderator.name
            })
        except Exception as e:
            print(f"❌ Failed to log moderation action: {e}")
    
    async def log_application_submitted(self, user: nextcord.Member, group: str, full_name: str):
        """Log group application submission"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        embed = create_embed(
            "Подана заявка до групи",
            f"**Користувач:** {user.mention} ({user.name})\n"
            f"**Група:** {group}\n"
            f"**ПІБ:** {full_name}",
            0x0099FF
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            await db.log_action("application_submitted", user.id, details={
                "group": group,
                "full_name": full_name
            })
        except Exception as e:
            print(f"❌ Failed to log application submission: {e}")
    
    async def log_application_reviewed(self, user_id: int, group: str, status: str, 
                                     reviewer: nextcord.Member):
        """Log application review"""
        channel = await self.get_log_channel()
        if not channel:
            return
        
        status_emoji = "✅" if status == "approved" else "❌"
        status_text = "Схвалена" if status == "approved" else "Відхилена"
        
        embed = create_embed(
            f"Заявка {status_text}",
            f"**Користувач:** <@{user_id}>\n"
            f"**Група:** {group}\n"
            f"**Статус:** {status_emoji} {status_text}\n"
            f"**Переглянув:** {reviewer.mention}",
            0x00FF00 if status == "approved" else 0xFF0000
        )
        
        try:
            await channel.send(embed=embed)
            await db.log_action("application_reviewed", user_id, reviewer.id, {
                "group": group,
                "status": status
            })
        except Exception as e:
            print(f"❌ Failed to log application review: {e}")
    
    async def log_message_delete(self, message: nextcord.Message):
        """Log deleted messages"""
        if message.author.bot:
            return
            
        channel = await self.get_log_channel()
        if not channel:
            return
        
        embed = create_embed(
            "Повідомлення видалено",
            f"**Автор:** {message.author.mention} ({message.author.name})\n"
            f"**Канал:** {message.channel.mention}\n"
            f"**Зміст:** {message.content[:1000] if message.content else 'Немає тексту'}",
            0xFF0000
        )
        
        if message.attachments:
            attachments_info = "\n".join([f"• {att.filename}" for att in message.attachments])
            embed.add_field(name="Вкладення", value=attachments_info, inline=False)
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Failed to log message deletion: {e}")
    
    async def log_message_edit(self, before: nextcord.Message, after: nextcord.Message):
        """Log edited messages"""
        if before.author.bot or before.content == after.content:
            return
            
        channel = await self.get_log_channel()
        if not channel:
            return
        
        embed = create_embed(
            "Повідомлення відредаговано",
            f"**Автор:** {before.author.mention} ({before.author.name})\n"
            f"**Канал:** {before.channel.mention}",
            0xFFFF00
        )
        
        if before.content:
            embed.add_field(
                name="До редагування",
                value=before.content[:1000] + ("..." if len(before.content) > 1000 else ""),
                inline=False
            )
        
        if after.content:
            embed.add_field(
                name="Після редагування", 
                value=after.content[:1000] + ("..." if len(after.content) > 1000 else ""),
                inline=False
            )
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Failed to log message edit: {e}")