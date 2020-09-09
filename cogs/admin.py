from constants import *
from discord.ext import commands


class Admin(commands.Cog):
    @commands.command(name='clear', aliases=['clear_data', 'cleardata'], help='Clears all tags from database.')
    @commands.is_owner()
    async def clear(self, ctx: BotContext):
        ctx.database.fetch()
        ctx.database.clear()

        if ctx.database.push():
            await ctx.send('All tags cleared.')
        else:
            await ctx.send('Failed to clear tags!')


def setup(bot):
    bot.add_cog(Admin())
