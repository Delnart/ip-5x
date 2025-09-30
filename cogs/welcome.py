import nextcord
from nextcord.ext import commands
from typing import Optional

from config import *
from utils.embeds import *
from utils.logs import Logger
from database.db import db

class RulesView(nextcord.ui.View):
    """Persistent view for rules acceptance"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @nextcord.ui.button(
        label="Я погоджуюся з правилами",
        style=nextcord.ButtonStyle.green,
        emoji="✅",
        custom_id="accept_rules"
    )
    async def accept_rules(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Handle rules acceptance"""
        try:
            # Get guest role
            guest_role = interaction.guild.get_role(ROLES['GUEST'])
            if not guest_role:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Роль гостя не знайдена!"),
                    ephemeral=True
                )
                return
            
            # Check if user already has guest role
            if guest_role in interaction.user.roles:
                await interaction.response.send_message(
                    embed=warning_embed("Увага", "Ви вже маєте роль гостя!"),
                    ephemeral=True
                )
                return
            
            # Add guest role
            await interaction.user.add_roles(guest_role, reason="Погодився з правилами")
            
            # Add user to database
            await db.add_user(interaction.user.id, interaction.user.name)
            
            # Send success message
            embed = success_embed(
                "Вітаємо!",
                f"Ви успішно погодились з правилами та отримали роль гостя!\n\n"
                f"Тепер ви можете перейти до <#{CHANNELS['GET_ROLE']}> щоб обрати свою групу."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Error in rules acceptance: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Сталася помилка при обробці запиту."),
                ephemeral=True
            )

class GroupSelectionView(nextcord.ui.View):
    """Persistent view for group selection"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        # Create buttons for each group
        groups = [
            ("ІП-51", "ip_51"),
            ("ІП-52", "ip_52"), 
            ("ІП-53", "ip_53"),
            ("ІП-54", "ip_54"),
            ("ІП-55", "ip_55"),
            ("ІП-56", "ip_56"),
            ("ІП-о51", "ip_o51")
        ]
        
        for group_name, custom_id in groups:
            button = nextcord.ui.Button(
                label=group_name,
                style=nextcord.ButtonStyle.primary,
                custom_id=f"select_group_{custom_id}"
            )
            button.callback = self.create_group_callback(group_name)
            self.add_item(button)
    
    def create_group_callback(self, group_name: str):
        """Create callback function for group selection"""
        async def group_callback(interaction: nextcord.Interaction):
            # Check if user has guest role
            guest_role = interaction.guild.get_role(ROLES['GUEST'])
            if guest_role not in interaction.user.roles:
                await interaction.response.send_message(
                    embed=error_embed(
                        "Помилка доступу", 
                        "Спочатку потрібно погодитися з правилами!"
                    ),
                    ephemeral=True
                )
                return
            
            # Check if user already has a group role
            user_group_roles = [role for role in interaction.user.roles 
                              if role.id in GROUP_ROLES.values()]
            
            if user_group_roles:
                current_group = next(name for name, role_id in GROUP_ROLES.items() 
                                   if role_id == user_group_roles[0].id)
                await interaction.response.send_message(
                    embed=warning_embed(
                        "Увага", 
                        f"Ви вже маєте роль групи {current_group}!\n"
                        f"Для зміни групи звертайтеся до адміністрації."
                    ),
                    ephemeral=True
                )
                return
            
            # Show modal for full name input
            modal = GroupApplicationModal(group_name)
            await interaction.response.send_modal(modal)
        
        return group_callback

class GroupApplicationModal(nextcord.ui.Modal):
    """Modal for group application with full name"""
    
    def __init__(self, group_name: str):
        self.group_name = group_name
        super().__init__(title=f"Заявка до групи {group_name}")
        
        self.full_name = nextcord.ui.TextInput(
            label="Повне ім'я (ПІБ)",
            placeholder="Введіть ваше повне ім'я (Прізвище Ім'я По батькові)",
            min_length=5,
            max_length=100,
            required=True
        )
        self.add_item(self.full_name)
    
    async def callback(self, interaction: nextcord.Interaction):
        """Handle application submission"""
        try:
            # Validate full name
            full_name = self.full_name.value.strip()
            if len(full_name.split()) < 2:
                await interaction.response.send_message(
                    embed=error_embed(
                        "Помилка", 
                        "Будь ласка, введіть повне ім'я (мінімум ім'я та прізвище)."
                    ),
                    ephemeral=True
                )
                return
            
            # Add application to database
            success = await db.add_application(
                interaction.user.id,
                interaction.user.name,
                self.group_name,
                full_name
            )
            
            if not success:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "У вас вже є активна заявка. Зачекайте розгляду."),
                    ephemeral=True
                )
                return
            
            # Send application to review channel
            review_channel = interaction.guild.get_channel(CHANNELS['GROUP_APPLICATIONS'])
            if review_channel:
                embed = group_application_embed(interaction.user, self.group_name, full_name)
                
                # Create review buttons
                view = ApplicationReviewView(interaction.user.id, self.group_name)
                
                # Ping appropriate moderators
                ping_roles = []
                starosta_role = interaction.guild.get_role(ROLES['STAROSTA'])
                zastupnyk_role = interaction.guild.get_role(ROLES['ZASTUPNYK'])
                
                if starosta_role:
                    ping_roles.append(starosta_role.mention)
                if zastupnyk_role:
                    ping_roles.append(zastupnyk_role.mention)
                
                ping_text = " ".join(ping_roles) if ping_roles else ""
                
                await review_channel.send(
                    content=ping_text,
                    embed=embed,
                    view=view
                )
            
            # Confirm to user
            await interaction.response.send_message(
                embed=success_embed(
                    "Заявка подана!",
                    f"Ваша заявка до групи **{self.group_name}** успішно подана!\n"
                    f"Очікуйте розгляду від старост або заступників."
                ),
                ephemeral=True
            )
            
            # Log application
            logger = Logger(interaction.client)
            await logger.log_application_submitted(interaction.user, self.group_name, full_name)
            
        except Exception as e:
            print(f"❌ Error in application submission: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Сталася помилка при подачі заявки."),
                ephemeral=True
            )

class ApplicationReviewView(nextcord.ui.View):
    """View for reviewing group applications"""
    
    def __init__(self, user_id: int, group: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.group = group
    
    @nextcord.ui.button(
        label="Схвалити",
        style=nextcord.ButtonStyle.green,
        emoji="✅"
    )
    async def approve_application(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Approve group application"""
        await self._handle_review(interaction, "approved")
    
    @nextcord.ui.button(
        label="Відхилити",
        style=nextcord.ButtonStyle.red,
        emoji="❌"
    )
    async def reject_application(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Reject group application"""
        await self._handle_review(interaction, "rejected")
    
    async def _handle_review(self, interaction: nextcord.Interaction, status: str):
        """Handle application review"""
        try:
            # Check if user has moderation permissions
            user_roles = [role.id for role in interaction.user.roles]
            if not any(role in MODERATION_ROLES for role in user_roles):
                await interaction.response.send_message(
                    embed=error_embed("Помилка доступу", "У вас немає прав для розгляду заявок."),
                    ephemeral=True
                )
                return
            
            # Get the applicant
            applicant = interaction.guild.get_member(self.user_id)
            if not applicant:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Користувач не знайдений на сервері."),
                    ephemeral=True
                )
                return
            
            # Update application status in database
            success = await db.update_application_status(
                self.user_id, 
                self.group, 
                status, 
                interaction.user.id
            )
            
            if not success:
                await interaction.response.send_message(
                    embed=error_embed("Помилка", "Не вдалося оновити статус заявки."),
                    ephemeral=True
                )
                return
            
            if status == "approved":
                # Add group role
                group_role = interaction.guild.get_role(GROUP_ROLES[self.group])
                if group_role:
                    await applicant.add_roles(group_role, reason=f"Заявка схвалена {interaction.user.name}")
                    
                    # Update user group in database
                    await db.update_user_group(self.user_id, self.group)
                
                # Remove guest role
                guest_role = interaction.guild.get_role(ROLES['GUEST'])
                if guest_role in applicant.roles:
                    await applicant.remove_roles(guest_role, reason="Додано до групи")
                
                # Send DM to user
                try:
                    embed = success_embed(
                        "Заявка схвалена!",
                        f"Вітаємо! Ваша заявка до групи **{self.group}** була схвалена.\n"
                        f"Тепер ви маєте доступ до всіх каналів групи."
                    )
                    await applicant.send(embed=embed)
                except:
                    pass  # Can't send DM
            
            else:  # rejected
                # Send DM to user
                try:
                    embed = error_embed(
                        "Заявка відхилена",
                        f"На жаль, ваша заявка до групи **{self.group}** була відхилена.\n"
                        f"Для отримання додаткової інформації звертайтеся до адміністрації."
                    )
                    await applicant.send(embed=embed)
                except:
                    pass  # Can't send DM
            
            # Update embed and disable buttons
            status_text = "схвалена" if status == "approved" else "відхилена"
            status_emoji = "✅" if status == "approved" else "❌"
            
            embed = interaction.message.embeds[0]
            embed.add_field(
                name="Статус",
                value=f"{status_emoji} Заявка {status_text}\n"
                      f"Розглянув: {interaction.user.mention}",
                inline=False
            )
            embed.color = 0x00FF00 if status == "approved" else 0xFF0000
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Log the review
            logger = Logger(interaction.client)
            await logger.log_application_reviewed(
                self.user_id, self.group, status, interaction.user
            )
            
        except Exception as e:
            print(f"❌ Error in application review: {e}")
            await interaction.response.send_message(
                embed=error_embed("Помилка", "Сталася помилка при розгляді заявки."),
                ephemeral=True
            )

class WelcomeCog(commands.Cog):
    """Cog for welcome system and authorization"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger(bot)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Setup persistent views when bot is ready"""
        print("🔄 Setting up persistent views...")
        
        # Add persistent views
        self.bot.add_view(RulesView())
        self.bot.add_view(GroupSelectionView())
        
        print("✅ Welcome system loaded")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member join"""
        try:
            # Add to database
            await db.add_user(member.id, member.name)
            
            # Log join
            await self.logger.log_user_join(member)
            
        except Exception as e:
            print(f"❌ Error handling member join: {e}")
    
    @commands.Cog.listener() 
    async def on_member_remove(self, member):
        """Handle member leave"""
        try:
            await self.logger.log_user_leave(member)
        except Exception as e:
            print(f"❌ Error handling member leave: {e}")
    
    @commands.command(name="setup_rules")
    @commands.has_any_role(*MODERATION_ROLES)
    async def setup_rules_message(self, ctx):
        """Setup rules message with button (Admin only)"""
        try:
            rules_channel = ctx.guild.get_channel(CHANNELS['RULES'])
            if not rules_channel:
                await ctx.send(embed=error_embed("Помилка", "Канал правил не знайдений!"))
                return
            
            embed = create_embed("Правила сервера", RULES_MESSAGE)
            view = RulesView()
            
            await rules_channel.send(embed=embed, view=view)
            await ctx.send(embed=success_embed("Готово", "Повідомлення з правилами створено!"))
            
        except Exception as e:
            print(f"❌ Error setting up rules: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося створити повідомлення з правилами."))
    
    @commands.command(name="setup_groups") 
    @commands.has_any_role(*MODERATION_ROLES)
    async def setup_group_selection(self, ctx):
        """Setup group selection message (Admin only)"""
        try:
            group_channel = ctx.guild.get_channel(CHANNELS['GET_ROLE'])
            if not group_channel:
                await ctx.send(embed=error_embed("Помилка", "Канал вибору ролі не знайдений!"))
                return
            
            embed = create_embed("Вибір групи", GROUP_SELECTION_MESSAGE)
            view = GroupSelectionView()
            
            await group_channel.send(embed=embed, view=view)
            await ctx.send(embed=success_embed("Готово", "Повідомлення з вибором груп створено!"))
            
        except Exception as e:
            print(f"❌ Error setting up group selection: {e}")
            await ctx.send(embed=error_embed("Помилка", "Не вдалося створити повідомлення з вибором груп."))

def setup(bot):
    bot.add_cog(WelcomeCog(bot))