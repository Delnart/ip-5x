import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from config import *
from utils.embeds import *
from utils.logs import Logger
from database.db import db

class ModerationCog(commands.Cog):
    """Cog for moderation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger(bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Setup on bot ready"""
        print("✅ Moderation system loaded")
    
    def has_moderation_role():
        """Check if user has moderation role"""
        async def predicate(ctx):
            user_roles = [role.id for role in ctx.author.roles]
            return any(role in MODERATION_ROLES for role in user_roles)
        return commands.check(predicate)
    
    @commands.command(name="ban")
    @has_moderation_role()
    async def ban_user(self, ctx, member: nextcord.Member, *, reason: str = None):
        """
        Ban a user from the server
        Usage: !ban @user [reason]
        """
        try:
            # Check if target is moderator
            target_roles = [role.id for role in member.roles]
            if any(role in MODERATION_ROLES for role in target_roles):
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Ви не можете забанити модератора!"
                    )
                )
                return
            
            # Check if trying to ban self
            if member.id == ctx.author.id:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Ви не можете забанити самого себе!"
                    )
                )
                return
            
            # Send DM to user before ban
            try:
                dm_embed = error_embed(
                    "Вас забанено",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Модератор:** {ctx.author.name}\n"
                    f"**Причина:** {reason or 'Не вказана'}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Ban user
            await member.ban(reason=f"Забанено {ctx.author.name}: {reason or 'Не вказана'}")
            
            # Log action
            await self.logger.log_moderation_action(
                "ban",
                member,
                ctx.author,
                reason
            )
            
            # Confirm to channel
            embed = success_embed(
                "Користувача забанено",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Модератор:** {ctx.author.mention}\n"
                f"**Причина:** {reason or 'Не вказана'}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error banning user: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося забанити користувача.")
            )
    
    @commands.command(name="kick")
    @has_moderation_role()
    async def kick_user(self, ctx, member: nextcord.Member, *, reason: str = None):
        """
        Kick a user from the server
        Usage: !kick @user [reason]
        """
        try:
            # Check if target is moderator
            target_roles = [role.id for role in member.roles]
            if any(role in MODERATION_ROLES for role in target_roles):
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Ви не можете вигнати модератора!"
                    )
                )
                return
            
            # Check if trying to kick self
            if member.id == ctx.author.id:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Ви не можете вигнати самого себе!"
                    )
                )
                return
            
            # Send DM to user before kick
            try:
                dm_embed = warning_embed(
                    "Вас вигнано",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Модератор:** {ctx.author.name}\n"
                    f"**Причина:** {reason or 'Не вказана'}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Kick user
            await member.kick(reason=f"Вигнано {ctx.author.name}: {reason or 'Не вказана'}")
            
            # Log action
            await self.logger.log_moderation_action(
                "kick",
                member,
                ctx.author,
                reason
            )
            
            # Confirm to channel
            embed = success_embed(
                "Користувача вигнано",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Модератор:** {ctx.author.mention}\n"
                f"**Причина:** {reason or 'Не вказана'}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error kicking user: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося вигнати користувача.")
            )
    
    @commands.command(name="mute")
    @has_moderation_role()
    async def mute_user(self, ctx, member: nextcord.Member, duration: str, *, reason: str = None):
        """
        Mute a user for specified duration
        Usage: !mute @user <duration> [reason]
        Duration format: 10m, 1h, 1d (minutes, hours, days)
        """
        try:
            # Check if target is moderator
            target_roles = [role.id for role in member.roles]
            if any(role in MODERATION_ROLES for role in target_roles):
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Ви не можете заглушити модератора!"
                    )
                )
                return
            
            # Parse duration
            try:
                time_unit = duration[-1]
                time_value = int(duration[:-1])
                
                if time_unit == 'm':
                    mute_duration = timedelta(minutes=time_value)
                    duration_text = f"{time_value} хвилин"
                elif time_unit == 'h':
                    mute_duration = timedelta(hours=time_value)
                    duration_text = f"{time_value} годин"
                elif time_unit == 'd':
                    mute_duration = timedelta(days=time_value)
                    duration_text = f"{time_value} днів"
                else:
                    raise ValueError
            except:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Невірний формат часу! Використовуйте: 10m, 1h, 1d"
                    )
                )
                return
            
            # Calculate unmute time
            unmute_time = datetime.utcnow() + mute_duration
            
            # Timeout user (nextcord built-in timeout)
            await member.timeout(unmute_time, reason=f"Заглушено {ctx.author.name}: {reason or 'Не вказана'}")
            
            # Update database
            await db.update_user_mute(member.id, unmute_time)
            
            # Log action
            await self.logger.log_moderation_action(
                "mute",
                member,
                ctx.author,
                reason,
                duration_text
            )
            
            # Send DM to user
            try:
                dm_embed = warning_embed(
                    "Вас заглушено",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Модератор:** {ctx.author.name}\n"
                    f"**Тривалість:** {duration_text}\n"
                    f"**Причина:** {reason or 'Не вказана'}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Confirm to channel
            embed = success_embed(
                "Користувача заглушено",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Модератор:** {ctx.author.mention}\n"
                f"**Тривалість:** {duration_text}\n"
                f"**До:** <t:{int(unmute_time.timestamp())}:F>\n"
                f"**Причина:** {reason or 'Не вказана'}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error muting user: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося заглушити користувача.")
            )
    
    @commands.command(name="unmute")
    @has_moderation_role()
    async def unmute_user(self, ctx, member: nextcord.Member):
        """
        Unmute a user
        Usage: !unmute @user
        """
        try:
            # Check if user is muted
            if not member.is_timed_out():
                await ctx.send(
                    embed=warning_embed(
                        "Увага",
                        "Користувач не заглушений!"
                    )
                )
                return
            
            # Remove timeout
            await member.timeout(None, reason=f"Розглушено {ctx.author.name}")
            
            # Update database
            await db.update_user_mute(member.id, None)
            
            # Log action
            await self.logger.log_moderation_action(
                "unmute",
                member,
                ctx.author
            )
            
            # Send DM to user
            try:
                dm_embed = success_embed(
                    "Вас розглушено",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Confirm to channel
            embed = success_embed(
                "Користувача розглушено",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error unmuting user: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося розглушити користувача.")
            )
    
    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: nextcord.Member = None):
        """
        Get information about a user
        Usage: !userinfo [@user]
        """
        if member is None:
            member = ctx.author
        
        try:
            # Get user data from database
            user_data = await db.get_user(member.id)
            
            # Create embed
            embed = user_info_embed(member, user_data)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося отримати інформацію про користувача.")
            )
    
    @commands.command(name="serverinfo")
    async def server_info(self, ctx):
        """
        Get server information
        Usage: !serverinfo
        """
        try:
            guild = ctx.guild
            
            # Count members by status
            online = len([m for m in guild.members if m.status == nextcord.Status.online])
            idle = len([m for m in guild.members if m.status == nextcord.Status.idle])
            dnd = len([m for m in guild.members if m.status == nextcord.Status.dnd])
            offline = len([m for m in guild.members if m.status == nextcord.Status.offline])
            
            embed = create_embed(
                f"Інформація про {guild.name}",
                f"**Власник:** {guild.owner.mention}\n"
                f"**Створено:** <t:{int(guild.created_at.timestamp())}:F>\n"
                f"**Учасників:** {guild.member_count}\n"
                f"**Каналів:** {len(guild.channels)}\n"
                f"**Ролей:** {len(guild.roles)}"
            )
            
            embed.add_field(
                name="Статуси",
                value=f"🟢 Online: {online}\n"
                      f"🟡 Idle: {idle}\n"
                      f"🔴 DND: {dnd}\n"
                      f"⚫ Offline: {offline}",
                inline=True
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error getting server info: {e}")
            await ctx.send(
                embed=error_embed("Помилка", "Не вдалося отримати інформацію про сервер.")
            )
    
    @commands.command(name="help")
    async def help_command(self, ctx):
        """
        Show help message
        Usage: !help
        """
        embed = help_embed()
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ModerationCog(bot))