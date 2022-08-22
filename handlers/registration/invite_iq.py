from telethon import Button
from telethon.events import register, InlineQuery
from telethon.tl.types import InputWebDocument, DocumentAttributeImageSize
from telethon.utils import get_display_name

from domain import registration, common
from entities.token import Token
from localization import translate, languages


@register(InlineQuery(common.admins, pattern=r'^invite$'))
@translate(text=False, translations=True)
async def handler(event: InlineQuery.Event, translations):
    current_tokens = registration.get_current_tokens(event.chat_id)
    articles = []
    lang = registration.language(event.chat_id)
    articles += [await invite_article(event, token, lang, translations[lang].gettext) for token in current_tokens]
    await event.answer(articles)


@register(InlineQuery(common.admins, pattern=r'^invite/$'))
@translate(text=False, translations=True)
async def handler_space(event: InlineQuery.Event, translations):
    current_tokens = registration.get_current_tokens(event.chat_id)
    articles = []
    for lang in languages:
        _ = translations[lang].gettext
        articles += [await invite_article(event, token, lang, _) for token in current_tokens]
    await event.answer(articles)


@register(InlineQuery(common.admins, pattern=r'^invite/([a-z]{2})$'))
@translate(text=False, translations=True)
async def handler_lang(event: InlineQuery.Event, translations):
    lang = event.pattern_match[1]
    if lang not in languages:
        await event.answer()
        return
    current_tokens = registration.get_current_tokens(event.chat_id)
    articles = [await invite_article(event, token, lang, translations[lang].gettext) for token in current_tokens]
    await event.answer(articles)


@register(InlineQuery(common.admins, pattern=r'^invite/([0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})$'))
@translate(text=False, translations=True)
async def handler_token(event: InlineQuery.Event, translations):
    token = registration.fetch_token(Token(event.pattern_match[1], owner_id=event.chat_id))
    if token is None:
        await event.answer()
    else:
        lang = registration.language(event.chat_id)
        await event.answer([await invite_article(event, token, lang, translations[lang].gettext)])


@register(InlineQuery(common.admins, pattern=r'^invite/([0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})/$'))
@translate(text=False, translations=True)
async def handler_token_space(event: InlineQuery.Event, translations):
    token = registration.fetch_token(Token(event.pattern_match[1], owner_id=event.chat_id))
    if token is None:
        await event.answer()
    else:
        await event.answer([await invite_article(event, token, lang, translations[lang].gettext) for lang in languages])


@register(InlineQuery(common.admins, pattern=r'^invite/([0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})/([a-z]{2})$'))
@translate(text=False, translations=True)
async def handler_token_lang(event: InlineQuery.Event, translations):
    token = registration.fetch_token(Token(event.pattern_match[1], owner_id=event.chat_id))
    if token is None:
        await event.answer()
    else:
        lang = event.pattern_match[2]
        if lang in languages:
            await event.answer([await invite_article(event, token, lang, translations[lang].gettext)])
        else:
            await event.answer()


invite_thumb = InputWebDocument('https://false.team/invite128.png', 6105, 'image/png',
                                [DocumentAttributeImageSize(128, 128)])


async def invite_article(event, token, lang, _):
    if token.used_by is None:
        description = ''
    else:
        display_name = get_display_name(await event.client.get_entity(token.used_by))
        description = (_('Bound to %s') % display_name) + ', '
    description += (_('Expires in %s') % token.expire) + '\n' + token.string

    return event.builder.article(_('Invite'), description, thumb=invite_thumb,
                                 text=_('You have been invited to use FalseЪ VPN'), buttons=[
            Button.inline(_('Accept'), b'accept ' + token.bytes + b' ' + lang.encode()),
            Button.inline(_('Decline'), b'decline ' + token.bytes)])
