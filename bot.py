import dotenv
from constants import *
from database import Database
from discord.ext import commands
import discord
import os


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX)

        key = os.getenv('SHEET_KEY')
        self.database = Database(key)

    async def on_ready(self):
        cogs = ('cogs.tags', 'cogs.admin')
        for cog in cogs:
            self.load_extension(cog)

        await self.change_presence(status=discord.Status.online, activity=discord.Game(name='with your tags'))
        print('Ready for tagging!')

    async def on_message(self, message: discord.Message):
        if not message.content:
            return
        
        message.content = message.clean_content
        for attach in message.attachments:
            message.content += f' {attach.proxy_url}'

        ctx = await self.get_context(message, cls=BotContext)
        if not ctx.command and message.content[0] == PREFIX:
            message.content = f'{PREFIX}{GET} {message.content[1:]}'
            ctx = await self.get_context(message, cls=BotContext)

        await self.invoke(ctx)

    async def on_command_error(self, ctx: BotContext, exception: discord.DiscordException):
        if isinstance(exception, commands.errors.MissingRequiredArgument):
            await ctx.send('Missing arguments!')
        else:
            print(f'Error: {exception}')


dotenv.load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

bot = Bot()
bot.run(discord_token)
