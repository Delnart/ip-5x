# Discord Bot Configuration for IP-5x Stream

# Bot Settings
COMMAND_PREFIX = "!"
BOT_COLOR = 0xFF69B4  # Pink-Purple color
AXOLOTL_EMOJI = "🦎"  # Can be replaced with custom axolotl emoji

# Role IDs
ROLES = {
    'IP_51': 1422209528627335208,
    'IP_52': 1422209554330157086,
    'IP_53': 1422209565016981657,
    'IP_54': 1422209574362157056,
    'IP_55': 1422209584134619207,
    'IP_56': 1422209598047391794,
    'IP_O51': 1422209628522942515,
    'STAROSTA': 1422209653684568145,
    'ZASTUPNYK': 1422209674043981895,
    'GUEST': 1422225294521012305
}

# Channel IDs
CHANNELS = {
    'LOG': 1422210022884114534,
    'RULES': 1422210151540330566,
    'GET_ROLE': 1422210275922280598,
    'GROUP_APPLICATIONS': 1422210351604433018,
    'VOICE_CREATOR': 1422210837933723731
}

# Category IDs
CATEGORIES = {
    'VOICE': 1422209118264885370
}

# Group mappings for easier access
GROUP_ROLES = {
    'ІП-51': ROLES['IP_51'],
    'ІП-52': ROLES['IP_52'],
    'ІП-53': ROLES['IP_53'],
    'ІП-54': ROLES['IP_54'],
    'ІП-55': ROLES['IP_55'],
    'ІП-56': ROLES['IP_56'],
    'ІП-о51': ROLES['IP_O51']
}

# Moderation roles (who can use moderation commands)
MODERATION_ROLES = [ROLES['STAROSTA'], ROLES['ZASTUPNYK']]

# Welcome message for rules channel
RULES_MESSAGE = f"""
{AXOLOTL_EMOJI} **Ласкаво просимо на сервер потоку ІП-5x!** {AXOLOTL_EMOJI}

📋 **Правила сервера:**
• Поважайте один одного
• Не спамте і не флудьте
• Використовуйте відповідні канали
• Слідуйте інструкціям старост

Щоб продовжити, натисніть кнопку нижче і погодьтеся з правилами.
"""

# Group selection message
GROUP_SELECTION_MESSAGE = f"""
{AXOLOTL_EMOJI} **Оберіть свою групу** {AXOLOTL_EMOJI}

Натисніть на кнопку відповідної групи нижче.
Після натискання заповніть форму з вашими даними.

**Доступні групи:**
• ІП-51 • ІП-52 • ІП-53
• ІП-54 • ІП-55 • ІП-56 • ІП-о51
"""