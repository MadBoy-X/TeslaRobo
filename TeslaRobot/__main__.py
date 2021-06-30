import importlib
import time
import re
from sys import argv
from typing import Optional

from TeslaRobot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from TeslaRobot.modules import ALL_MODULES
from TeslaRobot.modules.helper_funcs.chat_status import is_user_admin
from TeslaRobot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
**𝑯𝒆𝒚 𝑻𝒉𝒆𝒓𝒆** [🙂](https://telegra.ph/file/76567abc61b076d3166ab.mp4) **!!**.\n**𝑴𝒐𝒊 𝑵𝒂𝒎𝒆 𝒊𝒛 𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐.**\n**𝑰❜𝒎 𝒂𝒏 𝑨𝒅𝒗𝒂𝒏𝒄𝒆𝒅 𝒂𝒏𝒅 𝑴𝒐𝒅𝒊𝒇𝒊𝒆𝒅 𝑮𝒓𝒐𝒖𝒑 𝑴𝒂𝒏𝒂𝒈𝒆𝒓 𝒘𝒊𝒕𝒉 𝒎𝒂𝒏𝒚 𝒊𝒏𝒕𝒆𝒓𝒆𝒔𝒕𝒊𝒏𝒈 𝒇𝒆𝒂𝒕𝒖𝒓𝒆𝒔, 𝒃𝒂𝒔𝒆𝒅 𝒐𝒏 𝑳𝒂𝒕𝒆𝒔𝒕 𝑷𝒚𝒕𝒉𝒐𝒏 𝑴𝒐𝒅𝒖𝒍𝒆𝒔 𝒂𝒏𝒅 𝑻𝒆𝒍𝒆𝒕𝒉𝒐𝒏.**\n\n**𝑰 𝒄𝒂𝒏 𝑯𝒆𝒍𝒑 𝒚𝒐𝒖 𝑴𝒂𝒏𝒂𝒈𝒆 𝒚𝒐𝒖𝒓 𝑮𝒓𝒐𝒖𝒑𝒔 𝑬𝒂𝒔𝒊𝒍𝒚 𝒂𝒏𝒅 𝑷𝒓𝒐𝒕𝒆𝒄𝒕 𝒕𝒉𝒆𝒎 𝒇𝒓𝒐𝒎 𝑺𝒑𝒂𝒎𝒎𝒆𝒓𝒔/𝑵𝑺𝑭𝑾 𝑪𝒐𝒏𝒕𝒆𝒏𝒕. 𝑻𝒓𝒚 𝑶𝒖𝒕** `/help`.  
"""

buttons = [
    [
        InlineKeyboardButton(
            text="𝙄𝙣𝙫𝙞𝙩𝙚 𝙏𝙚𝙨𝙡𝙖𝙍𝙤𝙗𝙤 𝙩𝙤 𝙮𝙤𝙪𝙧 𝙂𝙧𝙤𝙪𝙥 🤴", url="https://t.me/TeslaRobo_Bot?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="💞 𝘼𝙗𝙤𝙪𝙩 💞", callback_data="tesla_"),
        InlineKeyboardButton(
            text="𝙎𝙪𝙥𝙥𝙤𝙧𝙩 🆘", url=f"https://t.me/{SUPPORT_CHAT}"
        ),
    ],
    [
        InlineKeyboardButton(text="💝𝕳𝖊𝖑𝖕 & 𝕮𝖔𝖒𝖒𝖆𝖓𝖉𝖘💝", callback_data="help_back"),
    ],
]


HELP_STRINGS = """
**𝑯𝒐𝒊𝒊 👋 !! 𝑴𝒆 𝒊𝒛 [𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐](https://telegra.ph/file/c5aa4d6884a37be999ab7.mp4).\n𝑪𝒍𝒊𝒄𝒌 𝒐𝒏 𝒕𝒉𝒆 𝑩𝒖𝒕𝒕𝒐𝒏𝒔 𝒃𝒆𝒍𝒐𝒘, 𝒕𝒐 𝒈𝒆𝒕 𝒕𝒉𝒆 𝒅𝒐𝒄𝒖𝒎𝒆𝒏𝒕𝒂𝒕𝒊𝒐𝒏 𝒂𝒃𝒐𝒖𝒕 𝒔𝒑𝒆𝒄𝒊𝒇𝒊𝒄 𝑴𝒐𝒅𝒖𝒍𝒆𝒔.**
"""


tesla_IMG = "https://telegra.ph/file/5e7b85fdf7ebf15a4f617.png"

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("TeslaRobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one.")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="«« 𝘽𝙖𝙘𝙠", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_text(
            "𝑯𝒎 𝑯𝒎, 𝑰❜𝒎 𝑨𝒘𝒂𝒌𝒆 🥱, 𝒂𝒏𝒅 𝒅𝒐𝒊𝒏𝒈 𝒎𝒚 𝒘𝒐𝒓𝒌 𝒆𝒇𝒇𝒊𝒄𝒊𝒆𝒏𝒕𝒍𝒚 𝒊𝒏 𝒂𝒍𝒍 𝒕𝒉𝒆 𝑪𝒉𝒂𝒕𝒔...\n<b>😴 𝑫𝒊𝒅𝒏❜𝒕 𝒔𝒍𝒆𝒆𝒑 𝒔𝒊𝒏𝒄𝒆 💤 :</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "𝐻𝑒𝑟𝑒 𝑖𝑠 𝑡ℎ𝑒 𝐻𝑒𝑙𝑝 𝑓𝑜𝑟 𝑡ℎ𝑒 *{}* 𝑀𝑜𝑑𝑢𝑙𝑒:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="«« 𝘽𝙖𝙘𝙠", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


@run_async
def tesla_about_callback(update, context):
    query = update.callback_query
    if query.data == "tesla_":
        query.message.edit_text(
            text="""ℹ️ **𝑴𝒚𝒔𝒆𝒍𝒇 𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐, 𝑨𝒏 𝒂𝒅𝒗𝒂𝒏𝒄𝒆𝒅 𝒂𝒏𝒅 𝒑𝒐𝒘𝒆𝒓𝒇𝒖𝒍 𝑮𝒓𝒐𝒖𝒑 𝑴𝒂𝒏𝒂𝒈𝒆𝒓 𝑩𝒐𝒕, 𝒃𝒖𝒊𝒍𝒕 𝒃𝒚 [😎🎮MสdBØy ✘😎](https://t.me/Warning_MadBoy_is_Back) 𝒕𝒐 𝒉𝒆𝒍𝒑 𝒚𝒐𝒖 𝒎𝒂𝒏𝒂𝒈𝒆 𝒚𝒐𝒖𝒓 𝒈𝒓𝒐𝒖𝒑 𝒆𝒂𝒔𝒊𝒍𝒚.**
                 \n**➥ 𝗜 𝗰𝗮𝗻 𝗿𝗲𝘀𝘁𝗿𝗶𝗰𝘁 𝘂𝘀𝗲𝗿𝘀.**
                 \n**➥ 𝗜 𝗰𝗮𝗻 𝗴𝗿𝗲𝗲𝘁 𝘂𝘀𝗲𝗿𝘀 𝘄𝗶𝘁𝗵 𝗰𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗮𝗯𝗹𝗲 𝘄𝗲𝗹𝗰𝗼𝗺𝗲 𝗺𝗲𝘀𝘀𝗮𝗴𝗲𝘀 𝗮𝗻𝗱 𝗲𝘃𝗲𝗻 𝘀𝗲𝘁 𝗮 𝗴𝗿𝗼𝘂𝗽❜𝘀 𝗿𝘂𝗹𝗲𝘀.**
                 \n**➥ 𝗜 𝗵𝗮𝘃𝗲 𝗮𝗻 𝗮𝗱𝘃𝗮𝗻𝗰𝗲𝗱 𝗮𝗻𝘁𝗶-𝗳𝗹𝗼𝗼𝗱 𝘀𝘆𝘀𝘁𝗲𝗺.**
                 \n**➥ 𝗜 𝗰𝗮𝗻 𝘄𝗮𝗿𝗻 𝘂𝘀𝗲𝗿𝘀 𝘂𝗻𝘁𝗶𝗹 𝘁𝗵𝗲𝘆 𝗿𝗲𝗮𝗰𝗵 𝗺𝗮𝘅 𝘄𝗮𝗿𝗻𝘀, 𝘄𝗶𝘁𝗵 𝗲𝗮𝗰𝗵 𝗽𝗿𝗲𝗱𝗲𝗳𝗶𝗻𝗲𝗱 𝗮𝗰𝘁𝗶𝗼𝗻𝘀 𝘀𝘂𝗰𝗵 𝗮𝘀 𝗯𝗮𝗻, 𝗺𝘂𝘁𝗲, 𝗸𝗶𝗰𝗸, 𝗲𝘁𝗰.**
                 \n**➥ 𝗜 𝗵𝗮𝘃𝗲 𝗮 𝗻𝗼𝘁𝗲 𝗸𝗲𝗲𝗽𝗶𝗻𝗴 𝘀𝘆𝘀𝘁𝗲𝗺, 𝗯𝗹𝗮𝗰𝗸𝗹𝗶𝘀𝘁𝘀, 𝗮𝗻𝗱 𝗲𝘃𝗲𝗻 𝗽𝗿𝗲𝗱𝗲𝘁𝗲𝗿𝗺𝗶𝗻𝗲𝗱 𝗿𝗲𝗽𝗹𝗶𝗲𝘀 𝗼𝗻 𝗰𝗲𝗿𝘁𝗮𝗶𝗻 𝗸𝗲𝘆𝘄𝗼𝗿𝗱𝘀.**
                 \n**➥ 𝗜 𝗰𝗵𝗲𝗰𝗸 𝗳𝗼𝗿 𝗮𝗱𝗺𝗶𝗻𝘀❜ 𝗽𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻𝘀 𝗯𝗲𝗳𝗼𝗿𝗲 𝗲𝘅𝗲𝗰𝘂𝘁𝗶𝗻𝗴 𝗮𝗻𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗮𝗻𝗱 𝗺𝗼𝗿𝗲 𝘀𝘁𝘂𝗳𝗳𝘀.**
                 \n\n𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐 𝒊𝒔 𝒍𝒊𝒄𝒆𝒏𝒔𝒆𝒅 𝒖𝒏𝒅𝒆𝒓 𝒕𝒉𝒆 𝑮𝑵𝑼 𝑮𝒆𝒏𝒆𝒓𝒂𝒍 𝑷𝒖𝒃𝒍𝒊𝒄 𝑳𝒊𝒄𝒆𝒏𝒔𝒆 𝒗3.0.
                 \n**𝑯𝒆𝒓𝒆❜𝒔 𝒕𝒉𝒆 [💾 𝑹𝒆𝒑𝒐𝒔𝒊𝒕𝒐𝒓𝒚](https://github.com/MadBoy-X/TeslaRobo) 𝒇𝒐𝒓 𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐.**
                 \n\n**𝑰𝒇 𝒚𝒐𝒖 𝒉𝒂𝒗𝒆 𝒂𝒏𝒚 𝒒𝒖𝒆𝒓𝒊𝒆𝒔, 𝒍𝒆𝒕 𝒖𝒔 𝒌𝒏𝒐𝒘 𝒂𝒕 𝒕𝒉𝒆 @TeslaRobo_Chat.**""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="«« 𝘽𝙖𝙘𝙠", callback_data="tesla_back")
                 ]
                ]
            ),
        )
    elif query.data == "tesla_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )


@run_async
def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text="""𝑯𝒐𝒊𝒊 👋 !! 𝑰❜𝒎 *𝑻𝒆𝒔𝒍𝒂𝑹𝒐𝒃𝒐*.
                 \n𝑯𝒆𝒓𝒆❜𝒔 𝒕𝒉𝒆 [𝑺𝒐𝒖𝒓𝒄𝒆 𝑪𝒐𝒅𝒆](https://github.com/MadBoy-X/TeslaRobo) .""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="«« 𝙂𝙤 𝘽𝙖𝙘𝙠", callback_data="source_back")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"𝐶𝑜𝑛𝑡𝑎𝑐𝑡 𝑚𝑒 𝑖𝑛 𝑃𝑀 𝑡𝑜 𝑔𝑒𝑡 ℎ𝑒𝑙𝑝 𝑜𝑓 {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="𝙃𝙚𝙡𝙥 🆘",
                                url="https://t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "𝐶𝑜𝑛𝑡𝑎𝑐𝑡 𝑚𝑒 𝑖𝑛 𝑃𝑀 𝑡𝑜 𝑔𝑒𝑡 𝑡ℎ𝑒 𝑙𝑖𝑠𝑡 𝑜𝑓 𝑝𝑜𝑠𝑠𝑖𝑏𝑙𝑒 𝑐𝑜𝑚𝑚𝑎𝑛𝑑𝑠.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="𝙃𝙚𝙡𝙥 🆘",
                            url="https://t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "𝐻𝑒𝑟𝑒 𝑖𝑠 𝑡ℎ𝑒 𝑎𝑣𝑎𝑖𝑙𝑎𝑏𝑙𝑒 ℎ𝑒𝑙𝑝 𝑓𝑜𝑟 𝑡ℎ𝑒 *{}* 𝑀𝑜𝑑𝑢𝑙𝑒:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="«« 𝘽𝙖𝙘𝙠", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "𝑇ℎ𝑒𝑠𝑒 𝑎𝑟𝑒 𝑦𝑜𝑢𝑟 𝑐𝑢𝑟𝑟𝑒𝑛𝑡 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "𝑆𝑒𝑒𝑚𝑠 𝑙𝑖𝑘𝑒 𝑡ℎ𝑒𝑟𝑒 𝑎𝑟𝑒𝑛'𝑡 𝑎𝑛𝑦 𝑢𝑠𝑒𝑟 𝑠𝑝𝑒𝑐𝑖𝑓𝑖𝑐 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑎𝑣𝑎𝑖𝑙𝑎𝑏𝑙𝑒 :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="𝑊ℎ𝑖𝑐ℎ 𝑚𝑜𝑑𝑢𝑙𝑒 𝑤𝑜𝑢𝑙𝑑 𝑦𝑜𝑢 𝑙𝑖𝑘𝑒 𝑡𝑜 𝑐ℎ𝑒𝑐𝑘 {}'𝑠 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑓𝑜𝑟?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "𝑆𝑒𝑒𝑚𝑠 𝑙𝑖𝑘𝑒 𝑡ℎ𝑒𝑟𝑒 𝑎𝑟𝑒𝑛'𝑡 𝑎𝑛𝑦 𝑐ℎ𝑎𝑡 𝑠𝑝𝑒𝑐𝑖𝑓𝑖𝑐 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑎𝑣𝑎𝑖𝑙𝑎𝑏𝑙𝑒 :'(\n𝑆𝑒𝑛𝑑 𝑡ℎ𝑖𝑠 "
                "𝑖𝑛 𝑎 𝑔𝑟𝑜𝑢𝑝 𝑐ℎ𝑎𝑡 𝑦𝑜𝑢'𝑟𝑒 𝑎𝑑𝑚𝑖𝑛 𝑖𝑛 𝑡𝑜 𝑓𝑖𝑛𝑑 𝑖𝑡𝑠 𝑐𝑢𝑟𝑟𝑒𝑛𝑡 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* ℎ𝑎𝑠 𝑡ℎ𝑒 𝑓𝑜𝑙𝑙𝑜𝑤𝑖𝑛𝑔 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑓𝑜𝑟 𝑡ℎ𝑒 *{}* 𝑀𝑜𝑑𝑢𝑙𝑒:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="«« 𝘽𝙖𝙘𝙠",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "𝐻𝑖 𝑡ℎ𝑒𝑟𝑒! 𝑇ℎ𝑒𝑟𝑒 𝑎𝑟𝑒 𝑞𝑢𝑖𝑡𝑒 𝑎 𝑓𝑒𝑤 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑓𝑜𝑟 {} - 𝑔𝑜 𝑎ℎ𝑒𝑎𝑑 𝑎𝑛𝑑 𝑝𝑖𝑐𝑘 𝑤ℎ𝑎𝑡 "
                "𝑦𝑜𝑢'𝑟𝑒 𝑖𝑛𝑡𝑒𝑟𝑒𝑠𝑡𝑒𝑑 𝑖𝑛.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "𝐻𝑖 𝑡ℎ𝑒𝑟𝑒! 𝑇ℎ𝑒𝑟𝑒 𝑎𝑟𝑒 𝑞𝑢𝑖𝑡𝑒 𝑎 𝑓𝑒𝑤 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑓𝑜𝑟 {} - 𝑔𝑜 𝑎ℎ𝑒𝑎𝑑 𝑎𝑛𝑑 𝑝𝑖𝑐𝑘 𝑤ℎ𝑎𝑡 "
                "𝑦𝑜𝑢'𝑟𝑒 𝑖𝑛𝑡𝑒𝑟𝑒𝑠𝑡𝑒𝑑 𝑖𝑛.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="𝐻𝑖 𝑡ℎ𝑒𝑟𝑒! 𝑇ℎ𝑒𝑟𝑒 𝑎𝑟𝑒 𝑞𝑢𝑖𝑡𝑒 𝑎 𝑓𝑒𝑤 𝑠𝑒𝑡𝑡𝑖𝑛𝑔𝑠 𝑓𝑜𝑟 {} - 𝑔𝑜 𝑎ℎ𝑒𝑎𝑑 𝑎𝑛𝑑 𝑝𝑖𝑐𝑘 𝑤ℎ𝑎𝑡 "
                "𝑦𝑜𝑢'𝑟𝑒 𝑖𝑛𝑡𝑒𝑟𝑒𝑠𝑡𝑒𝑑 𝑖𝑛.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "𝑪𝒍𝒊𝒄𝒌 𝒉𝒆𝒓𝒆 𝒕𝒐 𝒈𝒆𝒕 𝒕𝒉𝒊𝒔 𝒄𝒉𝒂𝒕❜𝒔 𝒔𝒆𝒕𝒕𝒊𝒏𝒈𝒔, 𝒂𝒔 𝒘𝒆𝒍𝒍 𝒂𝒔 𝒚𝒐𝒖𝒓𝒔. 👀"
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="⚙️ 𝙎𝙚𝙩𝙩𝙞𝙣𝙜𝙨",
                                url="https://t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "𝘾𝙡𝙞𝙘𝙠 𝙝𝙚𝙧𝙚 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙮𝙤𝙪𝙧 𝙨𝙚𝙩𝙩𝙞𝙣𝙜𝙨. 👀"

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "𝒀𝒐𝒐!! 𝑴𝒆 𝒊𝒛 𝑶𝒏𝒍𝒊𝒏𝒆 𝒐𝒏𝒄𝒆 𝑨𝒈𝒂𝒊𝒏...😀🤨😁")
        except Unauthorized:
            LOGGER.warning(
                "Bot isn't able to send message to SUPPORT_CHAT, Go and Check !!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(tesla_about_callback, pattern=r"tesla_")
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_")

    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
