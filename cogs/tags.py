from constants import *
from discord.ext import commands


class Tags(commands.Cog):
    @commands.command(name=GET, aliases=['tag', 'g', 't'], help='Retrieves an existing tag.')
    async def get(self, ctx: BotContext, tag: str):
        ctx.database.fetch()
        content = ctx.database.get_item(GLOBAL, TAG, tag, CONTENT)

        if content:
            await ctx.send(content)
        else:
            await ctx.send('Tag not found!')

    @commands.command(name='add', aliases=['set', 'a', 's'], help='Adds a new tag.')
    async def add(self, ctx: BotContext, tag: str, *, content: str):
        ctx.database.fetch()
        current = ctx.database.get_item(GLOBAL, TAG, tag, CONTENT)

        if current:
            await ctx.send('Tag already exists!')
        elif tag in ctx.bot.all_commands.keys():
            await ctx.send('Can\'t use command name as tag!')
        else:
            content = ctx.bot.help_command.remove_mentions(content)
            ctx.database.add_record(GLOBAL, {TAG: tag, AUTHOR: ctx.author.id, CONTENT: content})

            if ctx.database.push():
                await ctx.send('Tag added.')
            else:
                await ctx.send('Tag failed to add!')

    @commands.command(name='edit', aliases=['e'], help='Edits an existing tag.')
    async def edit(self, ctx: BotContext, tag: str, *, content: str):
        ctx.database.fetch()
        record = ctx.database.get_record(GLOBAL, TAG, tag)

        if record:
            if record[AUTHOR] == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                record[CONTENT] = content
                ctx.database.update_record(GLOBAL, TAG, tag, record)

                if ctx.database.push():
                    await ctx.send('Tag edited.')
                else:
                    await ctx.send('Tag failed to edit!')
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')

    @commands.command(name='delete', aliases=['del', 'd'], help='Deletes an existing tag.')
    async def delete(self, ctx: BotContext, tag: str):
        ctx.database.fetch()
        author = ctx.database.get_item(GLOBAL, TAG, tag, AUTHOR)

        if author:
            if author == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                ctx.database.del_record(GLOBAL, TAG, tag)

                if ctx.database.push():
                    await ctx.send('Tag deleted.')
                else:
                    await ctx.send('Tag failed to delete!')
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')


def setup(bot):
    bot.add_cog(Tags())
