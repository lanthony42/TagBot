from utils import *
from discord.ext import commands
from discord import Member
from typing import Optional


class Tags(commands.Cog):
    @commands.command(name=GET, aliases=['tag', 'g', 't'], help='Retrieves an existing tag.')
    async def get(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        content = ctx.database.get_item(GLOBAL, TAG, tag, CONTENT)

        if content:
            if CMD_LPAR in content[0] and CMD_RPAR in content[0]:
                result = await ctx.parser.parse_content(ctx, content[0])
                result = await CLEANER.convert(ctx, result)

                if result:
                    await ctx.send(result if len(result) < MAX_MSG else 'Output was too long!')
                else:
                    await ctx.send('Tag had no output!')
            else:
                await ctx.send(content[0])
        else:
            await ctx.send('Tag not found!')

    @commands.command(name='add', aliases=['set', 'a'], help='Adds a new tag.')
    async def add(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        current = ctx.database.get_item(GLOBAL, TAG, tag, CONTENT)

        if current:
            await ctx.send('Tag already exists!')
        elif tag in ctx.bot.all_commands.keys():
            await ctx.send('Can\'t use command name as tag!')
        else:
            content = await get_input(ctx, 'Set tag contents:')
            if not content:
                return

            ctx.database.add_record(GLOBAL, {TAG: tag, AUTHOR: ctx.author.id, CONTENT: content})
            if ctx.database.push():
                await ctx.send('Tag added.')
            else:
                await ctx.send('Tag failed to add!')

    @commands.command(name='edit', aliases=['e'], help='Edits an existing tag.')
    async def edit(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        record = ctx.database.get_record(GLOBAL, TAG, tag)

        if record:
            if record[0][AUTHOR] == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                record[0][CONTENT] = await get_input(ctx, 'Set tag contents:')
                if not record[0][CONTENT]:
                    return

                ctx.database.update_record(GLOBAL, TAG, tag, record[0])
                if ctx.database.push():
                    await ctx.send('Tag edited.')
                else:
                    await ctx.send('Tag failed to edit!')
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')

    @commands.command(name='rename', aliases=['change_name'], help='Renames an existing tag.')
    async def rename(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        record = ctx.database.get_record(GLOBAL, TAG, tag)

        if record:
            if record[0][AUTHOR] == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                name = await get_input(ctx, 'Enter new tag name:')
                if name:
                    if not ctx.database.get_record(GLOBAL, TAG, name):
                        record[0][TAG] = name
                        ctx.database.update_record(GLOBAL, TAG, tag, record[0])

                        if ctx.database.push():
                            await ctx.send('Tag renamed.')
                        else:
                            await ctx.send('Tag failed to edit!')
                    else:
                        await ctx.send('Tag already exists!')
                return
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')

    @commands.command(name='delete', aliases=['remove', 'del', 'rem', 'd'], help='Deletes an existing tag.')
    async def delete(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        author = ctx.database.get_item(GLOBAL, TAG, tag, AUTHOR)

        if author:
            if author[0] == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                ctx.database.del_record(GLOBAL, TAG, tag)

                if ctx.database.push():
                    await ctx.send('Tag deleted.')
                else:
                    await ctx.send('Tag failed to delete!')
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')

    @commands.command(name='owner', aliases=['owns', 'own', 'o'], help='Shows owner of existing tag.')
    async def owner(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        user_id = ctx.database.get_item(GLOBAL, TAG, tag, AUTHOR)

        if user_id:
            author = ctx.bot.get_user(int(user_id[0]))
            await ctx.send(f'@{author.name}#{author.discriminator}' if author else 'Owner not found!')
        else:
            await ctx.send('Tag not found!')

    @commands.command(name='gift', aliases=['transfer', 'trans'], help='Transfers ownership of an existing tag.')
    async def gift(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        record = ctx.database.get_record(GLOBAL, TAG, tag)

        if record:
            if record[0][AUTHOR] == str(ctx.author.id) or await ctx.bot.is_owner(ctx.author):
                author = await get_input(ctx, 'Which member should tag be gifted to?')
                if author:
                    try:
                        member = await MEMBER_CONVERT.convert(ctx, author)
                        record[0][AUTHOR] = member.id
                        ctx.database.update_record(GLOBAL, TAG, tag, record[0])

                        if ctx.database.push():
                            await ctx.send('Tag gifted.')
                        else:
                            await ctx.send('Tag failed to edit!')
                    except commands.BadArgument:
                        await ctx.send('No such member found!')
                return
            else:
                await ctx.send('You are not the creator of this tag!')
        else:
            await ctx.send('Tag doesn\'t exist!')

    @commands.command(name='list', aliases=['list_commands', 'listcommands', 'ls', 'l'], help='List user\'s tags.')
    async def list(self, ctx: BotContext, *, member: Optional[Member]):
        if member:
            ctx.message.author = member
        ctx.database.fetch()
        records = ctx.database.get_record(GLOBAL, AUTHOR, ctx.author.id)

        if records:
            pages = []
            output = 'User\'s Tags:\n```\n'
            for i, record in enumerate(records, 1):
                output += f'{record[TAG]}\n'
                if i % MAX_LIST == 0:
                    output += '```'
                    pages.append(output)
                    output = 'User\'s Tags:\n```\n'

            if len(output) > len('User\'s Tags:\n```\n'):
                output += '```'
                pages.append(output)
            await paginate(ctx, pages)
        else:
            await ctx.send('No tags found!')

    @commands.command(name='raw', aliases=['get_raw', 'tag_raw', 'gr', 'tr'], help='Retrieves an existing tag as raw.')
    async def raw(self, ctx: BotContext, *, tag: str):
        ctx.database.fetch()
        content = ctx.database.get_item(GLOBAL, TAG, tag, CONTENT)

        if content:
            await ctx.send(f'```\n{content[0]}\n```')
        else:
            await ctx.send('Tag not found!')

    @commands.command(name='script', aliases=['test', 'scr'], help='Test the output of a tag script.')
    async def script(self, ctx: BotContext, *, text: str):
        if text in ['help', '-h', 'h']:
            cmd = ctx.bot.get_command('script_help')
            await ctx.invoke(cmd)
        else:
            await ctx.send(await ctx.parser.parse_content(ctx, text))

    @commands.command(name='script_help', aliases=['scripthelp'], help='Lists script commands')
    async def script_help(self, ctx: BotContext):
        pages = []
        output = []
        count = 1
        for name, info in ctx.parser.cmd_helper.help.items():
            params = f": {', '.join(info[ARG])}"
            output.append(f"{name}{params if info[IS_ARGS] else ''}")

            if count % MAX_LIST == 0:
                output = '\n'.join(output)
                pages.append(f"Script Commands:\n```\n{output}\n```")
                output = []
            count += 1

        if len(output) > 0:
            output = '\n'.join(output)
            pages.append(f"Script Commands:\n```\n{output}\n```")
        await paginate(ctx, pages)

    @commands.command(name='cancel', aliases=['c'], help='Cancels input.')
    async def cancel(self, ctx: BotContext):
        pass


def setup(bot):
    bot.add_cog(Tags())
