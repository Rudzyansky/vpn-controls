from telethon.events import register, NewMessage

from bot_commands.categories import Categories
from domain import registration, commands
from domain.commands import access_list
from handlers.utils import extract
from localization import translate


@register(NewMessage(access_list(Categories.COMMON), blacklist_chats=True, pattern=r'^/start(?: ([a-z]{2}))?$'))
@translate()
async def handler(event: NewMessage.Event, _):
    if not registration.is_accept_invite(event.chat_id):
        return
    user = registration.register_user(event.chat_id, extract(event.pattern_match, 1, 'en'))
    if user is None:
        await event.client.send_message(event.chat_id, _('Something went wrong. Contact with developer'))
        return

    await commands.add_categories(user, Categories.NO_ACCOUNTS, Categories.COMMON)
    # todo say hello
