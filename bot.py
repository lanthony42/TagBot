import dotenv
from utils import *
from database import Database
from discord.ext import commands
from scripting import Parser
import discord
import os


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, allowed_mentions=discord.AllowedMentions(everyone=False))

        key = os.getenv('SHEET_KEY')
        self.database = Database(key)
        self.parser = Parser()

    async def on_ready(self):
        cogs = ('cogs.tags', 'cogs.admin')
        for cog in cogs:
            try:
                self.load_extension(cog)
            except commands.ExtensionAlreadyLoaded:
                debug(f'{cog} has already been loaded!')

        await self.change_presence(status=discord.Status.do_not_disturb if IS_DEV else discord.Status.online,
                                   activity=discord.Game(name='with your code' if IS_DEV else 'with your tags'))
        print('Ready for tagging!')

    async def on_message(self, message: discord.Message):
        if not message.content:
            return

        ctx = await self.get_context(message, cls=BotContext)
        if not ctx.command and message.content[0] == PREFIX:
            message.content = f'{PREFIX}{GET} {message.content[1:]}'
            ctx = await self.get_context(message, cls=BotContext)

        if IS_DEV and not await ctx.bot.is_owner(ctx.author):
            return
        else:
            await self.invoke(ctx)

    async def on_command_error(self, ctx: BotContext, exception: discord.DiscordException):
        if isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send('Missing arguments!')
        else:
            debug(f'Command Error: {exception}')


dotenv.load_dotenv()
discord_token = os.getenv('DEV_TOKEN' if IS_DEV else 'DISCORD_TOKEN')

bot = Bot()
bot.run(discord_token)
