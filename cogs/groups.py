import nextcord
from nextcord.ext import commands
from typing import Optional

from config import *
from utils.embeds import *
from utils.logs import Logger
from database.db import db

class GroupsCog(commands.Cog):
    """Cog for group management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger(bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Groups system loaded")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Auto-sync group roles with database"""
        try:
            # Check if group roles changed
            before_group_roles = [role for role in before.roles if role.id in GROUP_ROLES.values()]
            after_group_roles = [role for role in after.roles if role.id in GROUP_ROLES.values()]
            
            if before_group_roles != after_group_roles:
                # Group role changed
                if after_group_roles:
                    # User got a group role
                    new_group = next(name for name, role_id in GROUP_ROLES.items() 
                                   if role_id == after_group_roles[0].id)
                    await db.update_user_group(after.id, new_group)
                    print(f"✅ Auto-synced {after.name} to group {new_group}")
                else:
                    # User lost group role
                    await db.update_user_group(after.id, None)
                    print(f"✅ Removed {after.name} from group")
        except Exception as e:
            print(f"❌ Error in auto-sync: {e}")
    
    @commands.group(name="group", invoke_without_command=True)
    async def group_commands(self, ctx):
        """
        Group management commands
        Usage: !group <subcommand>
        """
        embed = info_embed(
            "Команди управління групами",
            "**Доступні команди:**\n"
            "`!group info <назва>` - Інформація про групу\n"
            "`!group members <назва>` - Список учасників групи\n"
            "`!group transfer @user <група>` - Перенести користувача до іншої групи (Старости/Заступники)\n"
            "`!group remove @user` - Видалити користувача з групи (Старости/Заступники)\n"
            "`!group stats` - Статистика всіх груп (Старости/Заступники)\n"
            "`!group list` - Список всіх груп\n"
            "`!group sync` - Синхронізувати ролі з базою даних (Старости/Заступники)"
        )
        await ctx.send(embed=embed)
    
    @group_commands.command(name="info")
    async def group_info(self, ctx, group_name: str):
        """
        Get information about a group
        Usage: !group info <group_name>
        """
        try:
            # Normalize group name
            group_name = group_name.upper()
            if not group_name.startswith("ІП-"):
                group_name = f"ІП-{group_name}"
            
            # Check if group exists
            if group_name not in GROUP_ROLES:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        f"Група **{group_name}** не знайдена!\n"
                        f"Доступні групи: {', '.join(GROUP_ROLES.keys())}"
                    )
                )
                return
            
            # Get group members
            members = await db.get_group_members(group_name)
            
            # Get group role
            group_role = ctx.guild.get_role(GROUP_ROLES[group_name])
            
            embed = create_embed(
                f"Інформація про групу {group_name}"
            )
            
            embed.add_field(
                name="Кількість учасників",
                value=str(len(members)),
                inline=True
            )
            
            if group_role:
                embed.add_field(
                    name="Роль",
                    value=group_role.mention,
                    inline=True
                )
                embed.add_field(
                    name="Колір ролі",
                    value=str(group_role.color),
                    inline=True
                )
            
            # Show some members
            if members:
                member_list = []
                for member_data in members[:10]:
                    member = ctx.guild.get_member(member_data['user_id'])
                    if member:
                        member_list.append(f"• {member.mention}")
                
                if member_list:
                    embed.add_field(
                        name="Учасники",
                        value="\n".join(member_list) + 
                              (f"\n... та ще {len(members) - 10}" if len(members) > 10 else ""),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Учасники",
                    value="Немає учасників",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in group info: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося отримати інформацію про групу."))
    
    @group_commands.command(name="members")
    async def group_members(self, ctx, group_name: str):
        """
        List all members of a group
        Usage: !group members <group_name>
        """
        try:
            # Normalize group name
            group_name = group_name.upper()
            if not group_name.startswith("ІП-"):
                group_name = f"ІП-{group_name}"
            
            # Check if group exists
            if group_name not in GROUP_ROLES:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        f"Група **{group_name}** не знайдена!\n"
                        f"Доступні групи: {', '.join(GROUP_ROLES.keys())}"
                    )
                )
                return
            
            # Get group members
            members = await db.get_group_members(group_name)
            
            embed = group_stats_embed(group_name, members)
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in group members: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося отримати список учасників."))
    
    @group_commands.command(name="transfer")
    @commands.has_any_role(*MODERATION_ROLES)
    async def group_transfer(self, ctx, member: nextcord.Member, group_name: str):
        """
        Transfer user to another group (Moderators only)
        Usage: !group transfer @user <group_name>
        """
        try:
            # Normalize group name
            group_name = group_name.upper()
            if not group_name.startswith("ІП-"):
                group_name = f"ІП-{group_name}"
            
            # Check if group exists
            if group_name not in GROUP_ROLES:
                await ctx.send(
                    embed=error_embed(
                        "Помилка",
                        f"Група **{group_name}** не знайдена!\n"
                        f"Доступні групи: {', '.join(GROUP_ROLES.keys())}"
                    )
                )
                return
            
            # Check if user already in this group
            user_data = await db.get_user(member.id)
            if user_data and user_data.get('group') == group_name:
                await ctx.send(
                    embed=warning_embed(
                        "Увага",
                        f"Користувач {member.mention} вже в групі **{group_name}**!"
                    )
                )
                return
            
            old_group = user_data.get('group') if user_data else None
            
            # Remove all group roles
            for role_id in GROUP_ROLES.values():
                role = ctx.guild.get_role(role_id)
                if role and role in member.roles:
                    await member.remove_roles(role, reason=f"Перенесення до {group_name} модератором: {ctx.author.name}")
            
            # Add new group role
            new_group_role = ctx.guild.get_role(GROUP_ROLES[group_name])
            if not new_group_role:
                await ctx.send(embed=error_embed("Помилка", "Роль групи не знайдена!"))
                return
            
            await member.add_roles(new_group_role, reason=f"Перенесено до групи модератором: {ctx.author.name}")
            
            # Remove guest role if exists
            guest_role = ctx.guild.get_role(ROLES['GUEST'])
            if guest_role in member.roles:
                await member.remove_roles(guest_role, reason="Додано до групи")
            
            # Update database
            await db.update_user_group(member.id, group_name)
            
            # Send DM to user
            try:
                dm_embed = success_embed(
                    "Вас перенесено до іншої групи!",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Стара група:** {old_group or 'Немає'}\n"
                    f"**Нова група:** {group_name}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Confirm
            embed = success_embed(
                "Користувача перенесено до групи",
                f"**Користувач:** {member.mention}\n"
                f"**Стара група:** {old_group or 'Немає'}\n"
                f"**Нова група:** {group_name}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
            # Log action
            await db.log_action("group_transfer", member.id, ctx.author.id, {
                "old_group": old_group,
                "new_group": group_name
            })
            
        except Exception as e:
            print(f"❌ Error in group transfer: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося перенести користувача до групи."))
    
    @group_commands.command(name="remove")
    @commands.has_any_role(*MODERATION_ROLES)
    async def group_remove(self, ctx, member: nextcord.Member):
        """
        Remove user from their group (Moderators only)
        Usage: !group remove @user
        """
        try:
            # Get user data
            user_data = await db.get_user(member.id)
            if not user_data or not user_data.get('group'):
                await ctx.send(
                    embed=warning_embed(
                        "Увага",
                        f"Користувач {member.mention} не має групи."
                    )
                )
                return
            
            current_group = user_data['group']
            
            # Get and remove group role
            group_role = ctx.guild.get_role(GROUP_ROLES[current_group])
            if group_role and group_role in member.roles:
                await member.remove_roles(group_role, reason=f"Видалено з групи модератором: {ctx.author.name}")
            
            # Add guest role
            guest_role = ctx.guild.get_role(ROLES['GUEST'])
            if guest_role:
                await member.add_roles(guest_role, reason="Видалено з групи")
            
            # Update database
            await db.update_user_group(member.id, None)
            
            # Send DM to user
            try:
                dm_embed = warning_embed(
                    "Вас видалено з групи",
                    f"**Сервер:** {ctx.guild.name}\n"
                    f"**Група:** {current_group}\n"
                    f"**Модератор:** {ctx.author.name}"
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Can't send DM
            
            # Confirm
            embed = success_embed(
                "Користувача видалено з групи",
                f"**Користувач:** {member.mention}\n"
                f"**Група:** {current_group}\n"
                f"**Модератор:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)
            
            # Log action
            await db.log_action("group_remove", member.id, ctx.author.id, {
                "group": current_group
            })
            
        except Exception as e:
            print(f"❌ Error in group remove: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося видалити користувача з групи."))
    
    @group_commands.command(name="sync")
    @commands.has_any_role(*MODERATION_ROLES)
    async def group_sync(self, ctx):
        """
        Sync all group roles with database (Moderators only)
        Usage: !group sync
        """
        try:
            synced = 0
            errors = 0
            
            # Go through all members with group roles
            for group_name, role_id in GROUP_ROLES.items():
                role = ctx.guild.get_role(role_id)
                if not role:
                    continue
                
                for member in role.members:
                    try:
                        # Ensure user exists in database
                        user_data = await db.get_user(member.id)
                        if not user_data:
                            await db.add_user(member.id, member.name, group_name)
                            synced += 1
                        elif user_data.get('group') != group_name:
                            await db.update_user_group(member.id, group_name)
                            synced += 1
                    except Exception as e:
                        print(f"❌ Error syncing {member.name}: {e}")
                        errors += 1
            
            embed = success_embed(
                "Синхронізація завершена",
                f"**Синхронізовано:** {synced} користувачів\n"
                f"**Помилок:** {errors}"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in group sync: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося синхронізувати групи."))
    
    @group_commands.command(name="stats")
    @commands.has_any_role(*MODERATION_ROLES)
    async def group_stats(self, ctx):
        """
        Show statistics for all groups (Moderators only)
        Usage: !group stats
        """
        try:
            embed = create_embed(
                "Статистика груп потоку ІП-5x",
                "Інформація про всі групи:"
            )
            
            total_members = 0
            
            # Get stats for each group
            for group_name in GROUP_ROLES.keys():
                members = await db.get_group_members(group_name)
                member_count = len(members)
                total_members += member_count
                
                # Get role
                group_role = ctx.guild.get_role(GROUP_ROLES[group_name])
                role_mention = group_role.mention if group_role else group_name
                
                embed.add_field(
                    name=f"{group_name}",
                    value=f"{role_mention}\n👥 {member_count} учасників",
                    inline=True
                )
            
            embed.set_footer(text=f"Всього учасників у групах: {total_members}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in group stats: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося отримати статистику груп."))
    
    @group_commands.command(name="list")
    async def group_list(self, ctx):
        """
        List all available groups
        Usage: !group list
        """
        embed = info_embed(
            "Доступні групи",
            "**Групи потоку ІП-5x:**"
        )
        
        for group_name, role_id in GROUP_ROLES.items():
            role = ctx.guild.get_role(role_id)
            if role:
                embed.add_field(
                    name=group_name,
                    value=role.mention,
                    inline=True
                )
        
        embed.set_footer(text="Для вступу до групи перейдіть до каналу отримання ролі")
        await ctx.send(embed=embed)
    
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
            
            # Count bots
            bots = len([m for m in guild.members if m.bot])
            humans = guild.member_count - bots
            
            embed = create_embed(
                f"Інформація про {guild.name}",
                f"**Власник:** {guild.owner.mention}\n"
                f"**Створено:** <t:{int(guild.created_at.timestamp())}:F>\n"
                f"**Створено:** <t:{int(guild.created_at.timestamp())}:R>"
            )
            
            embed.add_field(
                name="👥 Учасники",
                value=f"**Всього:** {guild.member_count}\n"
                      f"**Люди:** {humans}\n"
                      f"**Боти:** {bots}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Статуси",
                value=f"🟢 {online}\n"
                      f"🟡 {idle}\n"
                      f"🔴 {dnd}\n"
                      f"⚫ {offline}",
                inline=True
            )
            
            embed.add_field(
                name="📁 Канали",
                value=f"**Всього:** {len(guild.channels)}\n"
                      f"**Текстові:** {len(guild.text_channels)}\n"
                      f"**Голосові:** {len(guild.voice_channels)}",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Ролі",
                value=f"**Кількість:** {len(guild.roles)}",
                inline=True
            )
            
            embed.add_field(
                name="😊 Емодзі",
                value=f"**Кількість:** {len(guild.emojis)}",
                inline=True
            )
            
            embed.add_field(
                name="🚀 Буст",
                value=f"**Рівень:** {guild.premium_tier}\n"
                      f"**Бустів:** {guild.premium_subscription_count or 0}",
                inline=True
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            if guild.banner:
                embed.set_image(url=guild.banner.url)
            
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
    bot.add_cog(GroupsCog(bot))

