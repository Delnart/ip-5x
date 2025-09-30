import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
import re
from typing import Optional

from config import *
from utils.embeds import *
from utils.logs import Logger
from database.db import db

def parse_time(time_string: str) -> Optional[timedelta]:
    """Parse time string to timedelta (e.g., '1h', '30m', '1d')"""
    time_regex = re.compile(r'(\d+)([smhd])')
    matches = time_regex.findall(time_string.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 's':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
    
    return timedelta(seconds=total_seconds)

def format_timedelta(td: timedelta) -> str:
    """Format timedelta to readable string"""
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}г")
    if minutes > 0:
        parts.append(f"{minutes}хв")
    
    return " ".join(parts) if parts else "менше хвилини"

class ModerationCog(commands.Cog):
    """Cog for moderation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger(bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Moderation system loaded")
    
    @commands.command(name="ban")
    @commands.has_any_role(*MODERATION_ROLES)
    async def ban_user(self, ctx, member: nextcord.Member, *, reason: str = "Не вказана"):
        """
        Ban a user from the server
        Usage: !ban @user [reason]
        """
        try:
            # Check if target is moderator
            if any(role.id in MODERATION_ROLES for role in member.roles):
                await ctx.send(
                    embed=error_embed("Помилка", "Неможливо забанити модератора!")
                )
                return
            
            # Check hierarchy
            if member.top_role >= ctx.author.top_role:
                await ctx.send(
                    embed=error_embed("Помилка", "Ви не можете забанити користувача з вищою або рівною роллю!")
                )
                return
            
            # Send DM to user
            try:
                dm_embed = error_embed(
                    "Ви були забанені",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Причина:** {reason}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Ban user
            await member.ban(reason=f"{reason} | Модератор: {ctx.author.name}")
            
            # Log action
            await self.logger.log_moderation_action("ban", member, ctx.author, reason)
            
            # Confirm
            embed = success_embed(
                "Користувач забанений",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Причина:** {reason}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in ban command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося забанити користувача."))
    
    @commands.command(name="unban")
    @commands.has_any_role(*MODERATION_ROLES)
    async def unban_user(self, ctx, user_id: int, *, reason: str = "Не вказана"):
        """
        Unban a user from the server
        Usage: !unban <user_id> [reason]
        """
        try:
            user = await self.bot.fetch_user(user_id)
            
            # Unban user
            await ctx.guild.unban(user, reason=f"{reason} | Модератор: {ctx.author.name}")
            
            # Log action
            await db.log_action("moderation_unban", user_id, ctx.author.id, {
                "reason": reason,
                "moderator_username": ctx.author.name
            })
            
            # Confirm
            embed = success_embed(
                "Користувач розбанений",
                f"**Користувач:** {user.name} (ID: {user_id})\n"
                f"**Причина:** {reason}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except nextcord.NotFound:
            await ctx.send(embed=error_embed("Помилка", "Користувач не знайдений або не забанений."))
        except Exception as e:
            print(f"❌ Error in unban command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося розбанити користувача."))
    
    @commands.command(name="kick")
    @commands.has_any_role(*MODERATION_ROLES)
    async def kick_user(self, ctx, member: nextcord.Member, *, reason: str = "Не вказана"):
        """
        Kick a user from the server
        Usage: !kick @user [reason]
        """
        try:
            # Check if target is moderator
            if any(role.id in MODERATION_ROLES for role in member.roles):
                await ctx.send(
                    embed=error_embed("Помилка", "Неможливо викинути модератора!")
                )
                return
            
            # Check hierarchy
            if member.top_role >= ctx.author.top_role:
                await ctx.send(
                    embed=error_embed("Помилка", "Ви не можете викинути користувача з вищою або рівною роллю!")
                )
                return
            
            # Send DM to user
            try:
                dm_embed = warning_embed(
                    "Ви були викинуті",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Причина:** {reason}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Kick user
            await member.kick(reason=f"{reason} | Модератор: {ctx.author.name}")
            
            # Log action
            await self.logger.log_moderation_action("kick", member, ctx.author, reason)
            
            # Confirm
            embed = success_embed(
                "Користувач викинутий",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Причина:** {reason}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in kick command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося викинути користувача."))
    
    @commands.command(name="mute")
    @commands.has_any_role(*MODERATION_ROLES)
    async def mute_user(self, ctx, member: nextcord.Member, duration: str, *, reason: str = "Не вказана"):
        """
        Mute a user for specified duration
        Usage: !mute @user <duration> [reason]
        Duration examples: 1h, 30m, 1d, 2h30m
        """
        try:
            # Check if target is moderator
            if any(role.id in MODERATION_ROLES for role in member.roles):
                await ctx.send(
                    embed=error_embed("Помилка", "Неможливо заглушити модератора!")
                )
                return
            
            # Parse duration
            duration_delta = parse_time(duration)
            if not duration_delta:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        "Неправильний формат часу! Використовуйте: 1h, 30m, 1d, 2h30m"
                    )
                )
                return
            
            # Calculate unmute time
            unmute_time = datetime.utcnow() + duration_delta
            
            # Timeout user (Discord native timeout)
            await member.timeout(unmute_time, reason=f"{reason} | Модератор: {ctx.author.name}")
            
            # Save to database
            await db.update_user_mute(member.id, unmute_time)
            
            # Send DM to user
            try:
                dm_embed = warning_embed(
                    "Вас заглушено",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Тривалість:** {format_timedelta(duration_delta)}\n"
                    f"**До:** <t:{int(unmute_time.timestamp())}:F>\n"
                    f"**Причина:** {reason}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Log action
            await self.logger.log_moderation_action(
                "mute", member, ctx.author, reason, format_timedelta(duration_delta)
            )
            
            # Confirm
            embed = success_embed(
                "Користувач заглушений",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Тривалість:** {format_timedelta(duration_delta)}\n"
                f"**До:** <t:{int(unmute_time.timestamp())}:F>\n"
                f"**Причина:** {reason}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in mute command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося заглушити користувача."))
    
    @commands.command(name="unmute")
    @commands.has_any_role(*MODERATION_ROLES)
    async def unmute_user(self, ctx, member: nextcord.Member):
        """
        Unmute a user
        Usage: !unmute @user
        """
        try:
            # Remove timeout
            await member.timeout(None, reason=f"Розглушено модератором: {ctx.author.name}")
            
            # Update database
            await db.update_user_mute(member.id, None)
            
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
            
            # Log action
            await self.logger.log_moderation_action("unmute", member, ctx.author)
            
            # Confirm
            embed = success_embed(
                "Користувач розглушений",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in unmute command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося розглушити користувача."))
    
    @commands.command(name="warn")
    @commands.has_any_role(*MODERATION_ROLES)
    async def warn_user(self, ctx, member: nextcord.Member, *, reason: str = "Не вказана"):
        """
        Warn a user
        Usage: !warn @user [reason]
        """
        try:
            # Check if target is moderator
            if any(role.id in MODERATION_ROLES for role in member.roles):
                await ctx.send(
                    embed=error_embed("Помилка", "Неможливо попередити модератора!")
                )
                return
            
            # Add warning to database
            await db.add_warning(member.id, reason, ctx.author.id)
            
            # Get total warnings
            user_data = await db.get_user(member.id)
            total_warnings = user_data.get('warnings', 1) if user_data else 1
            
            # Send DM to user
            try:
                dm_embed = warning_embed(
                    "Ви отримали попередження",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Причина:** {reason}\n"
                    f"**Модератор:** {ctx.author.name}\n"
                    f"**Всього попереджень:** {total_warnings}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Log action
            await self.logger.log_moderation_action("warn", member, ctx.author, reason)
            
            # Confirm
            embed = warning_embed(
                "Попередження видано",
                f"**Користувач:** {member.mention} ({member.name})\n"
                f"**Причина:** {reason}\n"
                f"**Модератор:** {ctx.author.mention}\n"
                f"**Всього попереджень:** {total_warnings}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in warn command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося видати попередження."))
    
    @commands.command(name="warnings")
    @commands.has_any_role(*MODERATION_ROLES)
    async def view_warnings(self, ctx, member: nextcord.Member):
        """
        View user's warnings
        Usage: !warnings @user
        """
        try:
            warnings = await db.get_user_warnings(member.id)
            
            if not warnings:
                await ctx.send(
                    embed=info_embed(
                        "Попередження",
                        f"У користувача {member.mention} немає попереджень."
                    )
                )
                return
            
            embed = create_embed(
                f"Попередження користувача {member.name}",
                f"**Всього попереджень:** {len(warnings)}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Show last 5 warnings
            for i, warning in enumerate(warnings[:5], 1):
                moderator = ctx.guild.get_member(warning['moderator_id'])
                mod_name = moderator.name if moderator else "Невідомий"
                timestamp = warning['timestamp']
                
                embed.add_field(
                    name=f"Попередження #{i}",
                    value=f"**Причина:** {warning['reason']}\n"
                          f"**Модератор:** {mod_name}\n"
                          f"**Дата:** <t:{int(timestamp.timestamp())}:R>",
                    inline=False
                )
            
            if len(warnings) > 5:
                embed.set_footer(text=f"Показано 5 з {len(warnings)} попереджень")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error viewing warnings: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося отримати попередження."))
    
    @commands.command(name="clear")
    @commands.has_any_role(*MODERATION_ROLES)
    async def clear_messages(self, ctx, amount: int):
        """
        Delete messages in channel
        Usage: !clear <amount>
        """
        try:
            if amount < 1 or amount > 100:
                await ctx.send(
                    embed=error_embed("Помилка", "Кількість повідомлень має бути від 1 до 100!")
                )
                return
            
            # Delete messages
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for command message
            
            # Send confirmation (will auto-delete)
            embed = success_embed(
                "Повідомлення видалено",
                f"Видалено **{len(deleted) - 1}** повідомлень."
            )
            msg = await ctx.send(embed=embed)
            
            # Auto-delete after 5 seconds
            await msg.delete(delay=5)
            
        except Exception as e:
            print(f"❌ Error in clear command: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося видалити повідомлення."))

def setup(bot):
    bot.add_cog(ModerationCog(bot))