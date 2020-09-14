from asyncio import TimeoutError
from discord.ext.commands import Context, MemberConverter, clean_content
from discord import Message
from os import environ

IS_DEV = 'PYCHARM_HOSTED' in environ
PREFIX = '.' if IS_DEV else ','
GET = 'get'
CTX = 'ctx'
MAX_MSG = 2000
MAX_LIST = 8

GLOBAL = 'Main'
TAG = 'Tag'
AUTHOR = 'Author'
CONTENT = 'Content'
FIELDS = [TAG, AUTHOR, CONTENT]

CMD_LPAR = '<'
CMD_RPAR = '>'
CMD_SEPARATOR = ':'
CMD_DELIMITER = '/'
CMD_CHAR = CMD_LPAR + CMD_RPAR + CMD_DELIMITER

EQ = '='
LOGIC_EQ = '=='
NE = '~='
GT = '>'
LT = '<'
GE = '>='
LE = '<='

BIT_AND = '&'
AND = '&&'
BIT_OR = '|'
OR = '||'
BOOL_CHAR = NE + GT + LT + BIT_AND + BIT_OR

NEG = '-'
ADD = '+'
SUB = '-'
MUL = '*'
MUL_ALPHA = 'x'
DIV = '//'
DIV_ESC = '\\/'
EXP = '^'
MATH_CHAR = ADD + SUB + MUL + MUL_ALPHA + DIV + EXP

CMD = 'command'
CALL = 'call'
ARG = 'args'
BEFORE = 'before'
AFTER = 'after'
IS_CTX = 'contextual'
IS_ARGS = 'useUserArgs'
IS_POSITIONAL = 'positional'

MEMBER_CONVERT = MemberConverter()
CLEANER = clean_content(use_nicknames=False)


class BotContext(Context):
    @property
    def database(self):
        return self.bot.database

    @property
    def parser(self):
        return self.bot.parser


def strip(text: str):
    return text.lower().strip()


def test_bool(text: str):
    return strip(text) and strip(text) != 'false'


def debug(out):
    if IS_DEV:
        print(out)


async def get_input(ctx: BotContext, text: str = '', timeout: float = 30.0):
    def check(msg: Message):
        if strip(msg.content) in [f'{PREFIX}cancel', f'{PREFIX}c']:
            msg.content = ''
        return msg.author == ctx.author and msg.channel == ctx.channel

    message = await ctx.send(text if text else 'Input:')
    try:
        response = await ctx.bot.wait_for('message', check=check, timeout=timeout)
        content = response.content

        for attach in response.attachments:
            content += f' {attach.proxy_url}'

        if not content:
            await message.edit(content='Canceled!')
        return content
    except TimeoutError:
        await message.edit(content='Timed out!')
        return ''


async def paginate(ctx: BotContext, pages: list, timeout: float = 30.0):
    reactions = ['⬅', '➡']
    index = 0

    def check(reaction, user):
        return not user.bot and reaction.message.id == message.id and str(reaction.emoji) in reactions

    message = await ctx.send(pages[index])
    if len(pages) < 2:
        return
    for react in reactions:
        await message.add_reaction(react)

    while True:
        try:
            react, author = await ctx.bot.wait_for('reaction_add', check=check, timeout=timeout)
            await message.remove_reaction(react, author)
        except TimeoutError:
            await message.clear_reactions()
            break
        else:
            if react.emoji == '⬅':
                index = len(pages) - 1 if index - 1 < 0 else index - 1
            elif react.emoji == '➡':
                index = 0 if index + 1 >= len(pages) else index + 1
            await message.edit(content=pages[index])
