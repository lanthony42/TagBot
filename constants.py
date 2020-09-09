from discord.ext.commands import Context

PREFIX = ','
GET = 'get'

GLOBAL = 'Main'
TAG = 'Tag'
AUTHOR = 'Author'
CONTENT = 'Content'
FIELDS = [TAG, AUTHOR, CONTENT]


class BotContext(Context):
    @property
    def database(self):
        return self.bot.database
