import nextcord
from nextcord.ext import commands
from typing import Dict, Optional
import asyncio

from config import *
from utils.embeds import *
from utils.logs import Logger
from database.db import db

class VoiceControlView(nextcord.ui.View):
    """Voice channel control panel"""
    
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id
    
    @nextcord.ui.button(
        label="Заблокувати",
        style=nextcord.ButtonStyle.secondary,
        emoji="🔒",
        custom_id="voice_lock"
    )
    async def lock_channel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Lock voice channel"""
        await self._handle_voice_action(interaction, "lock")
    
    @nextcord.ui.button(
        label="Розблокувати",
        style=nextcord.ButtonStyle.secondary,
        emoji="🔓",
        custom_id="voice_unlock"
    )
    async def unlock_channel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Unlock voice channel"""
        await self._handle_voice_action(interaction, "unlock")
    
    @nextcord.ui.button(
        label="Ліміт користувачів",
        style=nextcord.ButtonStyle.secondary,
        emoji="👥",
        custom_id="voice_limit"
    )
    async def set_user_limit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Set user limit for voice channel"""
        await self._handle_voice_action(interaction, "limit")
    
    @nextcord.ui.button(
        label="Перейменувати",
        style=nextcord.ButtonStyle.secondary,
        emoji="✏️",
        custom_id="voice_rename"
    )
    async def rename_channel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Rename voice channel"""
        await self._handle_voice_action(interaction, "rename")
    
    @nextcord.ui.button(
        label="Передати права",
        style=nextcord.ButtonStyle.secondary,
        emoji="👑",
        custom_id="voice_transfer"
    )
    async def transfer_ownership(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Transfer channel ownership"""
        await self._handle_voice_action(interaction, "transfer")
    
    @nextcord.ui.button(
        label="Видалити канал",
        style=nextcord.ButtonStyle.danger,
        emoji="🗑️",
        custom_id="voice_delete"
    )
    async def delete_channel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Delete voice channel"""
        await self._handle_voice_action(interaction, "delete")
    
    async def _handle_voice_action(self, interaction: nextcord.Interaction, action: str):
        """Handle voice channel actions"""
        try:
            # Get voice channel
            voice_channel = interaction.guild.get_channel(self.channel_id)
            if not voice_channel:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Голосовий канал не знайдений!"),
                    ephemeral=True
                )
                return
            
            # Get channel data from database
            channel_data = await db.get_voice_channel(self.channel_id)
            if not channel_data:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Дані каналу не знайдені!"),
                    ephemeral=True
                )
                return
            
            # Check if user is owner or has moderation rights
            is_owner = interaction.user.id == channel_data['owner_id']
            is_moderator = any(role.id in MODERATION_ROLES for role in interaction.user.roles)
            
            if not (is_owner or is_moderator):
                await interaction.response.send_message(
                    embed=error_embed("Помилка доступу", "Тільки власник каналу або модератор може керувати цим каналом!"),
                    ephemeral=True
                )
                return
            
            if action == "lock":
                # Lock channel
                overwrites = voice_channel.overwrites
                overwrites[interaction.guild.default_role] = nextcord.PermissionOverwrite(connect=False)
                await voice_channel.edit(overwrites=overwrites)
                await db.update_voice_channel(self.channel_id, {"is_locked": True})
                
                await interaction.response.send_message(
                    embed=success_embed("Канал заблоковано", "Тепер тільки учасники каналу можуть приєднатися."),
                    ephemeral=True
                )
            
            elif action == "unlock":
                # Unlock channel
                overwrites = voice_channel.overwrites
                if interaction.guild.default_role in overwrites:
                    overwrites[interaction.guild.default_role] = nextcord.PermissionOverwrite(connect=None)
                await voice_channel.edit(overwrites=overwrites)
                await db.update_voice_channel(self.channel_id, {"is_locked": False})
                
                await interaction.response.send_message(
                    embed=success_embed("Канал розблоковано", "Тепер усі можуть приєднатися до каналу."),
                    ephemeral=True
                )
            
            elif action == "limit":
                # Show modal for user limit
                modal = UserLimitModal(self.channel_id)
                await interaction.response.send_modal(modal)
            
            elif action == "rename":
                # Show modal for rename
                modal = RenameChannelModal(self.channel_id)
                await interaction.response.send_modal(modal)
            
            elif action == "transfer":
                # Show modal for ownership transfer
                modal = TransferOwnershipModal(self.channel_id)
                await interaction.response.send_modal(modal)
            
            elif action == "delete":
                # Confirm deletion
                view = ConfirmDeleteView(self.channel_id)
                embed = warning_embed(
                    "Підтвердження видалення",
                    "Ви впевнені, що хочете видалити цей голосовий канал?\n"
                    "Ця дія незворотна!"
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        except Exception as e:
            print(f"❌ Error in voice action {action}: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Сталася помилка при виконанні дії."),
                ephemeral=True
            )

class UserLimitModal(nextcord.ui.Modal):
    """Modal for setting user limit"""
    
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        super().__init__(title="Встановити ліміт користувачів")
        
        self.limit_input = nextcord.ui.TextInput(
            label="Ліміт користувачів (0 = без ліміту)",
            placeholder="Введіть число від 0 до 99",
            min_length=1,
            max_length=2,
            required=True
        )
        self.add_item(self.limit_input)
    
    async def callback(self, interaction: nextcord.Interaction):
        try:
            limit = int(self.limit_input.value)
            if limit < 0 or limit > 99:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Ліміт має бути від 0 до 99!"),
                    ephemeral=True
                )
                return
            
            voice_channel = interaction.guild.get_channel(self.channel_id)
            await voice_channel.edit(user_limit=limit)
            
            limit_text = "без ліміту" if limit == 0 else f"{limit} користувачів"
            await interaction.response.send_message(
                embed=success_embed("Ліміт встановлено", f"Ліміт каналу: {limit_text}"),
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Будь ласка, введіть коректне число!"),
                ephemeral=True
            )
        except Exception as e:
            print(f"❌ Error setting user limit: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Не вдалося встановити ліміт."),
                ephemeral=True
            )

class RenameChannelModal(nextcord.ui.Modal):
    """Modal for renaming channel"""
    
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        super().__init__(title="Перейменувати канал")
        
        self.name_input = nextcord.ui.TextInput(
            label="Нова назва каналу",
            placeholder="Введіть нову назву каналу",
            min_length=1,
            max_length=100,
            required=True
        )
        self.add_item(self.name_input)
    
    async def callback(self, interaction: nextcord.Interaction):
        try:
            new_name = self.name_input.value.strip()
            voice_channel = interaction.guild.get_channel(self.channel_id)
            
            await voice_channel.edit(name=new_name)
            await db.update_voice_channel(self.channel_id, {"channel_name": new_name})
            
            await interaction.response.send_message(
                embed=success_embed("Канал перейменовано", f"Нова назва: **{new_name}**"),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Error renaming channel: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Не вдалося перейменувати канал."),
                ephemeral=True
            )

class TransferOwnershipModal(nextcord.ui.Modal):
    """Modal for transferring ownership"""
    
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        super().__init__(title="Передати права власника")
        
        self.user_input = nextcord.ui.TextInput(
            label="Новий власник (ID або @mention)",
            placeholder="Введіть ID користувача або згадайте його",
            min_length=1,
            max_length=100,
            required=True
        )
        self.add_item(self.user_input)
    
    async def callback(self, interaction: nextcord.Interaction):
        try:
            user_input = self.user_input.value.strip()
            
            # Try to get user by ID or mention
            new_owner = None
            if user_input.startswith('<@') and user_input.endswith('>'):
                # Mention format
                user_id = int(user_input[2:-1].replace('!', ''))
                new_owner = interaction.guild.get_member(user_id)
            else:
                # Try as ID
                try:
                    user_id = int(user_input)
                    new_owner = interaction.guild.get_member(user_id)
                except ValueError:
                    pass
            
            if not new_owner:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Користувач не знайдений!"),
                    ephemeral=True
                )
                return
            
            # Check if new owner is in the voice channel
            voice_channel = interaction.guild.get_channel(self.channel_id)
            if new_owner not in voice_channel.members:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Новий власник має бути в голосовому каналі!"),
                    ephemeral=True
                )
                return
            
            # Transfer ownership
            await db.update_voice_channel(self.channel_id, {"owner_id": new_owner.id})
            
            await interaction.response.send_message(
                embed=success_embed(
                    "Права передано", 
                    f"Права власника передано користувачу {new_owner.mention}"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Error transferring ownership: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Не вдалося передати права."),
                ephemeral=True
            )

class ConfirmDeleteView(nextcord.ui.View):
    """Confirmation view for channel deletion"""
    
    def __init__(self, channel_id: int):
        super().__init__(timeout=60)
        self.channel_id = channel_id
    
    @nextcord.ui.button(
        label="Так, видалити",
        style=nextcord.ButtonStyle.danger,
        emoji="✅"
    )
    async def confirm_delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            voice_channel = interaction.guild.get_channel(self.channel_id)
            if voice_channel:
                await voice_channel.delete(reason=f"Видалено власником: {interaction.user.name}")
            
            await db.remove_voice_channel(self.channel_id)
            
            await interaction.response.send_message(
                embed=success_embed("Канал видалено", "Голосовий канал успішно видалено."),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Error deleting channel: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Не вдалося видалити канал."),
                ephemeral=True
            )
    
    @nextcord.ui.button(
        label="Скасувати",
        style=nextcord.ButtonStyle.secondary,
        emoji="❌"
    )
    async def cancel_delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            embed=info_embed("Скасовано", "Видалення каналу скасовано."),
            ephemeral=True
        )

class VoiceCog(commands.Cog):
    """Cog for temporary voice channels"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger(bot)
        self.temp_channels: Dict[int, Dict] = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Load existing voice channels from database"""
        print("🔄 Loading voice channels...")
        
        # Clean up any orphaned channels on startup
        voice_category = self.bot.get_channel(CATEGORIES['VOICE'])
        if voice_category:
            for channel in voice_category.voice_channels:
                if channel.id != CHANNELS['VOICE_CREATOR'] and len(channel.members) == 0:
                    try:
                        await channel.delete(reason="Cleanup on bot restart")
                        await db.remove_voice_channel(channel.id)
                    except:
                        pass
        
        print("✅ Voice system loaded")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes"""
        try:
            # User joined voice creator channel
            if after.channel and after.channel.id == CHANNELS['VOICE_CREATOR']:
                await self._create_temp_channel(member)
            
            # User left a temporary channel
            if before.channel and before.channel.id != CHANNELS['VOICE_CREATOR']:
                # Check if it's a temporary channel and is now empty
                channel_data = await db.get_voice_channel(before.channel.id)
                if channel_data and len(before.channel.members) == 0:
                    await self._delete_temp_channel(before.channel)
        
        except Exception as e:
            print(f"❌ Error in voice state update: {e}")
    
    async def _create_temp_channel(self, member: nextcord.Member):
        """Create temporary voice channel for user"""
        try:
            voice_category = self.bot.get_channel(CATEGORIES['VOICE'])
            if not voice_category:
                return
            
            # Create channel
            channel_name = f"🎙️ {member.display_name}"
            temp_channel = await voice_category.create_voice_channel(
                name=channel_name,
                reason=f"Temporary voice channel for {member.name}"
            )
            
            # Move user to new channel
            await member.move_to(temp_channel, reason="Moved to temporary channel")
            
            # Add to database
            await db.add_voice_channel(temp_channel.id, member.id, channel_name)
            
            # Send control panel
            embed = voice_control_embed(channel_name, member)
            view = VoiceControlView(temp_channel.id)
            
            control_message = await temp_channel.send(embed=embed, view=view)
            
            # Log creation
            await self.logger.log_voice_channel_create(temp_channel, member)
            
        except Exception as e:
            print(f"❌ Error creating temp channel: {e}")
    
    async def _delete_temp_channel(self, channel: nextcord.VoiceChannel):
        """Delete temporary voice channel"""
        try:
            # Get channel data
            channel_data = await db.get_voice_channel(channel.id)
            if not channel_data:
                return
            
            # Remove from database
            await db.remove_voice_channel(channel.id)
            
            # Log deletion
            await self.logger.log_voice_channel_delete(
                channel_data['channel_name'],
                channel_data['owner_id']
            )
            
            # Delete channel
            await channel.delete(reason="Temporary channel cleanup")
            
        except Exception as e:
            print(f"❌ Error deleting temp channel: {e}")
    
    @commands.command(name="voice")
    async def voice_info(self, ctx, member: nextcord.Member = None):
        """
        Get information about voice channels
        Usage: !voice [@user]
        """
        try:
            target = member or ctx.author
            
            # Check if user is in a voice channel
            if not target.voice or not target.voice.channel:
                await ctx.send(
                    embed=warning_embed(
                        "Не в голосовому каналі",
                        f"{target.mention} зараз не в голосовому каналі."
                    )
                )
                return
            
            voice_channel = target.voice.channel
            
            # Check if it's a temporary channel
            channel_data = await db.get_voice_channel(voice_channel.id)
            
            embed = create_embed(
                f"Інформація про голосовий канал",
                f"**Канал:** {voice_channel.name}\n"
                f"**Користувачів:** {len(voice_channel.members)}\n"
                f"**Ліміт:** {voice_channel.user_limit if voice_channel.user_limit > 0 else 'Немає'}"
            )
            
            if channel_data:
                owner = ctx.guild.get_member(channel_data['owner_id'])
                embed.add_field(
                    name="Власник",
                    value=owner.mention if owner else "Невідомий",
                    inline=True
                )
                embed.add_field(
                    name="Статус",
                    value="🔒 Заблоковано" if channel_data.get('is_locked') else "🔓 Відкрито",
                    inline=True
                )
            
            # List members
            members_list = "\n".join([f"• {m.mention}" for m in voice_channel.members[:10]])
            if len(voice_channel.members) > 10:
                members_list += f"\n... та ще {len(voice_channel.members) - 10}"
            
            embed.add_field(name="Учасники", value=members_list, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error in voice info: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося отримати інформацію про канал."))

def setup(bot):
    bot.add_cog(VoiceCog(bot))