from utils import *
from pyparsing import *
from collections import OrderedDict
from discord.ext.commands import BadArgument
import discord
import inspect
import random


class Parser:
    def __init__(self):
        self.commands = Commands()
        self.cmd_helper = CommandHelper(self.commands)

    async def parse_content(self, ctx: BotContext, content: str):
        func = Forward()
        left, right, deliminator = map(lambda x: Suppress(Regex(fr'(?<!\\)(\{x})')), CMD_CHAR)

        text = Regex(fr'((?:\\[{CMD_CHAR}]|[^{CMD_CHAR}])*)')
        nested = Group((text(BEFORE) + Group(func)(CALL) + text(AFTER)))
        other = Regex(r'(.+)')(AFTER)
        arg = nested | text

        args = ZeroOrMore(arg + deliminator) + arg
        func <<= (left + Word(alphas)(CMD) + Optional(CMD_SEPARATOR + args)(ARG) + right).leaveWhitespace()
        search = (nested | Group(other)).leaveWhitespace()
        debug(nested.runTests(content))
        output = ''
        for match in search.searchString(content):
            debug(match[0].asDict())
            output += await self.parse_matches(ctx, match[0].asDict())
        return output

    async def parse_matches(self, ctx: BotContext, match: dict):
        if CALL in match.keys():
            result = await self.parse_command(ctx, match[CALL].get(CMD), match[CALL].get(ARG, []))
            return f"{match.get(BEFORE, '')}{result}{match.get(AFTER, '')}"
        elif AFTER in match.keys():
            return match[AFTER]
        else:
            return ''

    async def parse_command(self, ctx: BotContext, command: str, args: list):
        clean_args = args[1:]
        for i in range(len(clean_args)):
            if type(clean_args[i]) is dict:
                clean_args[i] = await self.parse_matches(ctx, clean_args[i])

        func = self.cmd_helper.help.get(strip(command))
        if func:
            try:
                if func[IS_CTX]:
                    clean_args.insert(0, ctx)
                elif func[IS_POSITIONAL]:
                    clean_args = clean_args[:len(func[ARG])]

                return await func[CMD](*clean_args)
            except (TypeError, ValueError, BadArgument) as error:
                debug(f'Script Error: {error}')
        return f"{CMD_LPAR}{command}{CMD_SEPARATOR if args else ''}{CMD_DELIMITER.join(args[1:])}{CMD_RPAR}"


class Commands:
    # User Commands
    @staticmethod
    async def name(ctx: BotContext):
        return ctx.author.name

    @staticmethod
    async def getname(ctx: BotContext, name: str):
        member = await MEMBER_CONVERT.convert(ctx, name.strip())
        return member.name

    @staticmethod
    async def nick(ctx: BotContext):
        return ctx.author.display_name

    @staticmethod
    async def getnick(ctx: BotContext, name: str):
        member = await MEMBER_CONVERT.convert(ctx, name.strip())
        return member.display_name

    @staticmethod
    async def discrim(ctx: BotContext):
        return ctx.author.discriminator

    @staticmethod
    async def getdiscrim(ctx: BotContext, name: str):
        member = await MEMBER_CONVERT.convert(ctx, name.strip())
        return member.discriminator

    @staticmethod
    async def id(ctx: BotContext):
        return ctx.author.id

    @staticmethod
    async def getid(ctx: BotContext, name: str):
        member = await MEMBER_CONVERT.convert(ctx, name.strip())
        return member.id

    @staticmethod
    async def avatar(ctx: BotContext):
        return ctx.author.avatar_url

    @staticmethod
    async def getavatar(ctx: BotContext, name: str):
        member = await MEMBER_CONVERT.convert(ctx, name.strip())
        return member.avatar_url

    # Guild Commands
    @staticmethod
    async def server(ctx: BotContext):
        if ctx.guild:
            return ctx.guild.name
        elif isinstance(ctx.channel, discord.DMChannel):
            return f'{ctx.author.name}\'s DM Channel'
        elif isinstance(ctx.channel, discord.GroupChannel):
            return f'{ctx.channel.owner.name}\'s Group Channel'

    @staticmethod
    async def channel(ctx: BotContext):
        if isinstance(ctx.channel, discord.TextChannel):
            return ctx.channel.name
        elif isinstance(ctx.channel, discord.DMChannel):
            return f'{ctx.author.name}\'s DM Channel'
        elif isinstance(ctx.channel, discord.GroupChannel):
            return f'{ctx.channel.owner.name}\'s Group Channel'

    @staticmethod
    async def randuser(ctx: BotContext):
        if ctx.guild:
            return random.choice(ctx.channel.members).name
        elif isinstance(ctx.channel, discord.GroupChannel):
            return random.choice(ctx.channel.recipients).name
        elif isinstance(ctx.channel, discord.DMChannel):
            return random.choice((ctx.author, ctx.bot.user)).name

    @staticmethod
    async def randonline(ctx: BotContext):
        if ctx.guild:
            online = [member for member in ctx.channel.members if member.status == discord.Status.online]
            if online:
                return random.choice(online).name
        return ctx.bot.user.name

    @staticmethod
    async def randnotoff(ctx: BotContext):
        if ctx.guild:
            online = [member for member in ctx.channel.members if member.status != discord.Status.offline]
            if online:
                return random.choice(online).name
        return ctx.bot.user.name

    # String Commands
    @staticmethod
    async def strip(text: str):
        return text.strip()

    @staticmethod
    async def lower(text: str):
        return text.lower()

    @staticmethod
    async def upper(text: str):
        return text.upper()

    @staticmethod
    async def code(text: str):
        return f'``{text}``'

    @staticmethod
    async def codeblock(text: str, lang: str = ''):
        return f"```{lang.strip() if lang else ''}\n{text}\n```"

    @staticmethod
    async def replace(text: str, old: str, new: str, keep_whitespace: str = 'false'):
        if strip(keep_whitespace) != 'false':
            return text.replace(old, new)
        else:
            return text.replace(old.strip(), new.strip())

    # Logical and Arithmetic Commands
    @staticmethod
    async def conditional(condition: str, if_true: str, if_false: str):
        return if_false if strip(condition) == 'false' or not strip(condition) else if_true

    # TODO: Boolean Parsing and Arithmetic Parsing
    @staticmethod
    async def bool(expression: str):
        text = Regex(fr'((?:\\[{CMD_CHAR}]|[^{CMD_CHAR}])*)')
        boolean = infixNotation(text, [(oneOf([EQ, GT, LT, GE, LE]), 2, opAssoc.LEFT), (NOT, 1, opAssoc.RIGHT),
                                       (AND, 2, opAssoc.LEFT), (OR, 2, opAssoc.LEFT)])
        debug(boolean.searchString(expression))
        return CommandHelper.parse_bool(boolean.searchString(expression)[0])

    @staticmethod
    async def math(expression: str):
        floats = pyparsing_common.real
        integer = pyparsing_common.signed_integer
        ops = [(NEG, 1, opAssoc.RIGHT)]
        ops.extend([(op, 2, opAssoc.LEFT) for op in (EXP, MUL, DIV, ADD, SUB)])

        math = infixNotation(floats | integer, ops)
        debug(math.searchString(expression)[0])
        result = float(CommandHelper.parse_math(math.searchString(expression)[0]))
        return int(result) if result.is_integer() else result

    # Misc Commands
    @staticmethod
    async def input(ctx: BotContext, message_text: str):
        return await get_input(ctx, message_text)

    @staticmethod
    async def choose(*args):
        choices = [arg for arg in args if arg]

        if choices:
            return random.choice(choices)
        else:
            raise BadArgument

    @staticmethod
    async def range(start: str, stop: str):
        return random.randint(int(start), int(stop))


class CommandHelper:
    def __init__(self, commands: Commands):
        self.commands = commands
        self.functions = {'if': commands.conditional}
        self.help = self.generate_help()

    def generate_help(self):
        def arg(name: str, param: inspect.Parameter):
            name = name.replace('_', ' ')
            if param.default != param.empty:
                return f'({name})'
            elif param.kind == param.VAR_POSITIONAL:
                return 'list'
            else:
                return name

        output = {}
        for f in dir(Commands):
            func = getattr(Commands, f)
            if callable(func) and not f.startswith('__'):
                params = inspect.signature(func).parameters
                param_names = list(params)
                try:
                    i = list(self.functions.values()).index(func)
                    command = {CALL: list(self.functions.keys())[i]}
                except ValueError:
                    command = {CALL: f}

                command[CMD] = func
                command[IS_CTX] = param_names[0] == CTX if param_names else False
                command[IS_POSITIONAL] = list(params.values())[len(params) - 1].kind == inspect.Parameter.VAR_POSITIONAL
                command[ARG] = [arg(name, param) for name, param in params.items()
                                if name != CTX]
                command[IS_ARGS] = bool(command[ARG])

                output[command[CALL]] = command
        return OrderedDict(sorted(output.items()))

    @classmethod
    def parse_bool(cls, match: list):
        pass

    @classmethod
    def parse_math(cls, item):
        if type(item) is ParseResults:
            return cls.parse_operation(item)
        else:
            return float(item)

    @classmethod
    def parse_operation(cls, match: ParseResults):
        if len(match) == 1:
            return cls.parse_math(match[0])
        elif len(match) == 2:
            if match[0] == NEG:
                return -cls.parse_math(match[1])
        elif len(match) == 3:
            if match[1] == ADD:
                return cls.parse_math(match[0]) + cls.parse_math(match[2])
            elif match[1] == SUB:
                return cls.parse_math(match[0]) - cls.parse_math(match[2])
            elif match[1] == MUL:
                return cls.parse_math(match[0]) * cls.parse_math(match[2])
            elif match[1] == DIV:
                return cls.parse_math(match[0]) / cls.parse_math(match[2])
            elif match[1] == EXP:
                return cls.parse_math(match[0]) ** cls.parse_math(match[2])
        return ''
