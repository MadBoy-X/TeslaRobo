from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from TeslaRobot import (
    DEL_CMDS,
    DEV_USERS,
    DRAGONS,
    SUPPORT_CHAT,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)

from telegram import Chat, ChatMember, ParseMode, Update
from telegram.ext import CallbackContext

# stores admemes in memory for 10 min.
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)
THREAD_LOCK = RLock()


def is_whitelist_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return any(user_id in user for user in [WOLVES, TIGERS, DEMONS, DRAGONS, DEV_USERS])


def is_support_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DEMONS or user_id in DRAGONS or user_id in DEV_USERS


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DRAGONS or user_id in DEV_USERS


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in DRAGONS
        or user_id in DEV_USERS
        or chat.all_members_are_administrators
        or user_id in [777000, 1837687523]
    ):  # Count telegram and Group Anonymous as admin
        return True
    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future useage...
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list
    else:
        return member.status in ("administrator", "creator")


def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == "private" or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)

    return bot_member.status in ("administrator", "creator")


def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in DRAGONS
        or user_id in DEV_USERS
        or user_id in WOLVES
        or user_id in TIGERS
        or chat.all_members_are_administrators
        or user_id in [777000, 1099219137]
    ):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        member = chat.get_member(user_id)

    return member.status in ("administrator", "creator")


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ("left", "kicked")


def dev_plus(func):
    @wraps(func)
    def is_dev_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user

        if user.id in DEV_USERS:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass
        else:
            update.effective_message.reply_text(
               "𝑻𝒉𝒂𝒕❜𝒔 𝒂 𝑫𝒆𝒗𝒆𝒍𝒐𝒑𝒆𝒓 𝑹𝒆𝒔𝒕𝒓𝒊𝒄𝒕𝒆𝒅 𝑪𝒐𝒎𝒎𝒂𝒏𝒅. "
               "\n𝒀𝒐𝒖 𝒄𝒂𝒏❜𝒕 𝒂𝒄𝒄𝒆𝒔𝒔 𝒊𝒕. 𝑻𝒉𝒂𝒏𝒌𝒔𝒔."
            )

    return is_dev_plus_func


def sudo_plus(func):
    @wraps(func)
    def is_sudo_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_sudo_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass
        else:
            update.effective_message.reply_text(
                "𝑾𝒉𝒐 𝒅𝒊𝒔 𝑵𝒐𝒏-𝑨𝒅𝒎𝒆𝒎𝒆 𝑲𝒊𝒊𝒅𝒅𝒐, 𝑰𝒏𝒔𝒕𝒓𝒖𝒄𝒕𝒊𝒏𝒈 𝒎𝒆, 𝑾𝒉𝒂𝒕 𝒕𝒐 𝒅𝒐❓\n𝒀𝒐𝒖 𝒘𝒂𝒏𝒕 𝒂 𝑩𝒂𝒏❓"
            )

    return is_sudo_plus_func


def support_plus(func):
    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass

    return is_support_plus_func


def whitelist_plus(func):
    @wraps(func)
    def is_whitelist_plus_func(
        update: Update, context: CallbackContext, *args, **kwargs
    ):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                f"𝒀𝒐𝒖❜𝒓𝒆 𝒏𝒐𝒕 𝒂𝒍𝒍𝒐𝒘𝒆𝒅 𝒕𝒐 𝒂𝒄𝒄𝒆𝒔𝒔 𝒕𝒉𝒊𝒔 𝒄𝒐𝒎𝒎𝒂𝒏𝒅.\n𝑽𝒊𝒔𝒊𝒕 @{SUPPORT_CHAT}"
            )

    return is_whitelist_plus_func


def user_admin(func):
    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass
        else:
            update.effective_message.reply_text(
                "𝑾𝒉𝒐 𝒅𝒊𝒔 𝑵𝒐𝒏-𝑨𝒅𝒎𝒆𝒎𝒆 𝑲𝒊𝒊𝒅𝒅𝒐, 𝑰𝒏𝒔𝒕𝒓𝒖𝒄𝒕𝒊𝒏𝒈 𝒎𝒆, 𝑾𝒉𝒂𝒕 𝒕𝒐 𝒅𝒐❓\n𝒀𝒐𝒖 𝒘𝒂𝒏𝒕 𝒂 𝑩𝒂𝒏❓"
            )

    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    def is_not_admin_no_reply(
        update: Update, context: CallbackContext, *args, **kwargs
    ):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except:
                pass

    return is_not_admin_no_reply


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and not is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass

    return is_not_admin


def bot_admin(func):
    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            not_admin = "𝑯𝒆𝒚 𝒀𝒐𝒖!!!! 𝒀𝒂 𝒀𝒐𝒖!!!\n𝑰❜𝒎 𝑵𝒐𝒕 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆!!\n\n𝑭𝑭𝑭𝑭\n𝑴𝒂𝒌𝒆 𝒎𝒆 𝑨𝒅𝒎𝒊𝒏 𝒘𝒊𝒕𝒉 𝒂𝒍𝒍 𝒓𝒊𝒈𝒉𝒕𝒔 (𝒆𝒙𝒄𝒆𝒑𝒕 𝑹𝒆𝒎𝒂𝒊𝒏 𝑨𝒏𝒐𝒏𝒚𝒎𝒐𝒖𝒔) 𝑷𝒉𝒂𝒔𝒕."
        else:
            not_admin = f"𝑯𝒆𝒚 𝒀𝒐𝒖!!!! 𝒀𝒂 𝒀𝒐𝒖!!!\n𝑰❜𝒎 𝑵𝒐𝒕 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒊𝒏 <b>{update_chat_title}</b>!!\n\n𝑭𝑭𝑭𝑭\n𝑴𝒂𝒌𝒆 𝒎𝒆 𝑨𝒅𝒎𝒊𝒏 𝒘𝒊𝒕𝒉 𝒂𝒍𝒍 𝒓𝒊𝒈𝒉𝒕𝒔 (𝒆𝒙𝒄𝒆𝒑𝒕 𝑹𝒆𝒎𝒂𝒊𝒏 𝑨𝒏𝒐𝒏𝒚𝒎𝒐𝒖𝒔) 𝑷𝒉𝒂𝒔𝒕."

        if is_bot_admin(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(not_admin, parse_mode=ParseMode.HTML)

    return is_admin


def bot_can_delete(func):
    @wraps(func)
    def delete_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒅𝒆𝒍𝒆𝒕𝒆 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔 𝒉𝒆𝒓𝒆!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒅𝒆𝒍𝒆𝒕𝒆 𝒐𝒕𝒉𝒆𝒓 𝒖𝒔𝒆𝒓𝒔❜ 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔."
        else:
            cant_delete = f"𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒅𝒆𝒍𝒆𝒕𝒆 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔 𝒊𝒏 <b>{update_chat_title}</b>!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒅𝒆𝒍𝒆𝒕𝒆 𝒐𝒕𝒉𝒆𝒓 𝒖𝒔𝒆𝒓𝒔❜ 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔."

        if can_delete(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(cant_delete, parse_mode=ParseMode.HTML)

    return delete_rights


def can_pin(func):

    @wraps(func)
    def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = "𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒊𝒏 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔 𝒉𝒆𝒓𝒆!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒊𝒏 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔."
        else:
            cant_pin = f"𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒊𝒏 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔 𝒊𝒏 <b>{update_chat_title}</b>!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒊𝒏 𝒎𝒆𝒔𝒔𝒂𝒈𝒆𝒔."

        if chat.get_member(bot.id).can_pin_messages:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_pin, parse_mode=ParseMode.HTML)

    return pin_rights
    
def can_promote(func):
    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_promote = "𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒓𝒐𝒎𝒐𝒕𝒆/𝒅𝒆𝒎𝒐𝒕𝒆 𝒖𝒔𝒆𝒓𝒔 𝒉𝒆𝒓𝒆!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒂𝒑𝒑𝒐𝒊𝒏𝒕 𝒏𝒆𝒘 𝒂𝒅𝒎𝒊𝒏𝒔 𝒐𝒓 𝒅𝒆𝒎𝒐𝒕𝒆 𝒂𝒅𝒎𝒊𝒏𝒔 𝒂𝒑𝒑𝒐𝒊𝒏𝒕𝒆𝒅 𝒃𝒚 𝒎𝒆."
        else:
            cant_promote = (
                f"𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒑𝒓𝒐𝒎𝒐𝒕𝒆/𝒅𝒆𝒎𝒐𝒕𝒆 𝒖𝒔𝒆𝒓𝒔 𝒊𝒏 <b>{update_chat_title}</b>!!\n"
                f"𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒂𝒑𝒑𝒐𝒊𝒏𝒕 𝒏𝒆𝒘 𝒂𝒅𝒎𝒊𝒏𝒔 𝒐𝒓 𝒅𝒆𝒎𝒐𝒕𝒆 𝒂𝒅𝒎𝒊𝒏𝒔 𝒂𝒑𝒑𝒐𝒊𝒏𝒕𝒆𝒅 𝒃𝒚 𝒎𝒆."
            )

        if chat.get_member(bot.id).can_promote_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(cant_promote, parse_mode=ParseMode.HTML)

    return promote_rights


def can_restrict(func):
    @wraps(func)
    def restrict_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_restrict = "𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒓𝒆𝒔𝒕𝒓𝒊𝒄𝒕 𝒖𝒔𝒆𝒓𝒔 𝒉𝒆𝒓𝒆!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒓𝒆𝒔𝒕𝒓𝒊𝒄𝒕 𝒖𝒔𝒆𝒓𝒔."
        else:
            cant_restrict = f"𝑰 𝒇𝒆𝒆𝒍 𝒍𝒊𝒌𝒆 𝑰❜𝒎 𝒖𝒏𝒂𝒃𝒍𝒆 𝒕𝒐 𝒓𝒆𝒔𝒕𝒓𝒊𝒄𝒕 𝒖𝒔𝒆𝒓𝒔 𝒊𝒏 <b>{update_chat_title}</b>!!\n𝑴𝒂𝒌𝒆 𝒔𝒖𝒓𝒆 𝒕𝒉𝒂𝒕 𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒎𝒆𝒎𝒆 𝒂𝒏𝒅 𝒎𝒖𝒔𝒕 𝒃𝒆 𝒂𝒃𝒍𝒆 𝒕𝒐 𝒓𝒆𝒔𝒕𝒓𝒊𝒄𝒕 𝒖𝒔𝒆𝒓𝒔."

        if chat.get_member(bot.id).can_restrict_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_restrict, parse_mode=ParseMode.HTML
            )

    return restrict_rights


def user_can_ban(func):
    @wraps(func)
    def user_is_banhammer(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if (
            not (member.can_restrict_members or member.status == "creator")
            and user not in DRAGONS
            and user not in [777000, 1837687523]
        ):
            update.effective_message.reply_text(
                "😂 𝑶𝒉 𝑳𝒐𝑳, 𝑺𝒐𝒓𝒓𝒚, 𝒃𝒖𝒕 𝒚𝒐𝒖 𝒄𝒂𝒏❜𝒕 𝒅𝒐 𝒕𝒉𝒂𝒕."
            )
            return ""
        return func(update, context, *args, **kwargs)

    return user_is_banhammer


def connection_status(func):
    @wraps(func)
    def connected_status(update: Update, context: CallbackContext, *args, **kwargs):
        conn = connected(
            context.bot,
            update,
            update.effective_chat,
            update.effective_user.id,
            need_admin=False,
        )

        if conn:
            chat = dispatcher.bot.getChat(conn)
            update.__setattr__("_effective_chat", chat)
            return func(update, context, *args, **kwargs)
        else:
            if update.effective_message.chat.type == "private":
                update.effective_message.reply_text(
                    "𝑺𝒆𝒏𝒅 `/connect` 𝒊𝒏 𝒂 𝒈𝒓𝒐𝒖𝒑 𝒕𝒉𝒂𝒕 𝒚𝒐𝒖 𝒂𝒏𝒅 𝒎𝒆 𝒉𝒂𝒗𝒆 𝒊𝒏 𝒄𝒐𝒎𝒎𝒐𝒏 𝒇𝒊𝒓𝒔𝒕𝒍𝒚."
                )
                return connected_status

            return func(update, context, *args, **kwargs)

    return connected_status


# Workaround for circular import with connection.py
from TeslaRobot.modules import connection

connected = connection.connected
