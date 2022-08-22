from telethon.events import register, CallbackQuery

from domain import registration, common
from entities.token import Token
from localization import translate


@register(CallbackQuery(pattern=rb'^decline (.{16})$'))
@translate()
async def handler(event: CallbackQuery.Event, _):
    if event.sender_id in common.registered:
        await event.answer(_('Access denied'))
        return

    if registration.revoke_token(Token(event.pattern_match[1], owner_id=event.chat_id)):
        await event.edit(_('Invitation turned into a pumpkin'))
    else:
        await event.edit(_('Invitation is invalid'))
