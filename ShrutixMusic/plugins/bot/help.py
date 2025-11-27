import random
from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message
from ShrutixMusic import nand
from ShrutixMusic.utils import help_pannel
from ShrutixMusic.utils.database import get_lang
from ShrutixMusic.utils.decorators.language import LanguageStart, languageCB
from ShrutixMusic.utils.inline.help import help_back_markup, private_help_panel
from config import BANNED_USERS, START_IMAGE_URLS, SUPPORT_CHAT
from strings import get_string, helpers

SUCCESS_EFFECT_IDS = [
    5104841245755180586,
    5107584321108051014,
    5159385139981059251,
    5046509860389126442,
]

@nand.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@nand.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client: nand, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, True)
        await update.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT), reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = help_pannel(_)
        random_img = random.choice(START_IMAGE_URLS)
        
        try:
            await update.reply_photo(
                photo=random_img,
                caption=_["help_1"].format(SUPPORT_CHAT),
                reply_markup=keyboard,
                has_spoiler=True,
                message_effect_id=random.choice(SUCCESS_EFFECT_IDS),
            )
        except:
            await update.reply_photo(
                photo=random_img,
                caption=_["help_1"].format(SUPPORT_CHAT),
                reply_markup=keyboard,
                has_spoiler=True,
            )

@nand.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    await message.reply_text(_["help_2"], reply_markup=InlineKeyboardMarkup(keyboard))

@nand.on_callback_query(filters.regex("help_page_2") & ~BANNED_USERS)
async def help_page_2_callback(client, CallbackQuery):
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    chat_id = CallbackQuery.message.chat.id
    language = await get_lang(chat_id)
    _ = get_string(language)
    
    keyboard = help_pannel(_, True, page=2)
    
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)
    except Exception as e:
        print(f"Error in page 2 navigation: {e}")

@nand.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    
    page = 2 if cb in ["hb10", "hb11", "hb12", "hb13", "hb14", "hb15"] else 1
    keyboard = help_back_markup(_, page)
    
    if cb == "hb1":
        await CallbackQuery.edit_message_text(helpers.HELP_1, reply_markup=keyboard)
    elif cb == "hb2":
        await CallbackQuery.edit_message_text(helpers.HELP_2, reply_markup=keyboard)
    elif cb == "hb3":
        await CallbackQuery.edit_message_text(helpers.HELP_3, reply_markup=keyboard)
    elif cb == "hb4":
        await CallbackQuery.edit_message_text(helpers.HELP_4, reply_markup=keyboard)
    elif cb == "hb5":
        await CallbackQuery.edit_message_text(helpers.HELP_5, reply_markup=keyboard)
    elif cb == "hb6":
        await CallbackQuery.edit_message_text(helpers.HELP_6, reply_markup=keyboard)
    elif cb == "hb7":
        await CallbackQuery.edit_message_text(helpers.HELP_7, reply_markup=keyboard)
    elif cb == "hb8":
        await CallbackQuery.edit_message_text(helpers.HELP_8, reply_markup=keyboard)
    elif cb == "hb9":
        await CallbackQuery.edit_message_text(helpers.HELP_9, reply_markup=keyboard)
    elif cb == "hb10":
        await CallbackQuery.edit_message_text(helpers.HELP_10, reply_markup=keyboard)
    elif cb == "hb11":
        await CallbackQuery.edit_message_text(helpers.HELP_11, reply_markup=keyboard)
    elif cb == "hb12":
        await CallbackQuery.edit_message_text(helpers.HELP_12, reply_markup=keyboard)
    elif cb == "hb13":
        await CallbackQuery.edit_message_text(helpers.HELP_13, reply_markup=keyboard)
    elif cb == "hb14":
        await CallbackQuery.edit_message_text(helpers.HELP_14, reply_markup=keyboard)
    elif cb == "hb15":
        await CallbackQuery.edit_message_text(helpers.HELP_15, reply_markup=keyboard)
