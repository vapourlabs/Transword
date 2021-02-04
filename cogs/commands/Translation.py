# 3rd party libraries
from discord import Embed
from discord.utils import get
from discord.ext.commands import Cog
from discord_slash import SlashCommand, SlashContext
from discord_slash.cog_ext import cog_slash
from asyncio import get_event_loop

# Local libraries
from ..api.SlashAPI import SlashAPI as SAPI
from ..api.DeepLAPI import DeepLAPI as DAPI

class Translation(Cog):
    """ A cog handling all translation commands for the Bot. """

    def __init__(self, bot):
        # Makes slash commands existent if not set.
        if not hasattr(bot, "slash"):
            bot.slash = SlashCommand(
                bot,
                override_type = True,
                auto_register = True,
                auto_delete = True
            )

        # Define the DeepL API access.
        self.key = open(".AUTHKEY", "r").read()

        self.bot = bot
        self.bot.slash.get_cog_commands(self)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_slash(**SAPI.read("translate")["decorator"])
    async def _translate(self,
                         ctx: SlashContext,
                         target: str,
                         text: str,
                         formality: str = "",
                         format: str = ""):
        """ Translates text from a foreign language into another one specified. """

        # Check if any optional arguments were passed.
        options = [["preserve_formatting", "0"]]

        if formality != "":
            if target in ["EN", "EN-GB", "EN-US",
                          "ES", "JA", "ZH"]:
                await ctx.send(
                    content = f"Sorry {ctx.author.mention}, but `{target}` is not a supported language for formal formatting!\n(Formality argument has been ignored.)",
                    complete_hidden = True
                )
            else:
                options.append(["formality", formality])
        if format != "":
            options.append(["split_sentences", format])

        # Run the DeepL API to translate for us as long as within character limits.
        translation = None
        chars = len(text)

        if chars <= 200:
            translation = DAPI(self.key).translate(
                text = text,
                target = target,
                types = options
            )["translations"][0]
        else:
            await ctx.send(
                content = f"Sorry {ctx.author.mention}, but your message exceeds the `200` character limit with a total of `{chars}` characters!\nIn order to receive more character usage, please consider checking out our [Patreon tiers](https://www.patreon.com/transword) here.",
                complete_hidden = True
            )
            translation = False

        if translation:
            # Pull the embed and make some modifications.
            embed = Embed.from_dict(SAPI.read("translate")["embeds"][0])
            embed.set_field_at(0, name = f"`{translation['detected_source_language']}`",    value = text,                   inline = True)
            embed.set_field_at(1, name = f"`{target}`",                                     value = translation["text"],    inline = True)
            embed.set_author(name = ctx.author, url = f"https://discord.com/users/{ctx.author.id}", icon_url = ctx.author.avatar_url)

            await ctx.send(3, embeds = [embed])

    @cog_slash(**SAPI.read("transauto")["decorator"])
    async def _transauto(self,
                         ctx: SlashContext,
                         target: str):
        """ Automatically translates foreign language text into another one specified. """

        _role = f"auto{target}"

        async def check(role):
            roles = await ctx.guild.fetch_roles()

            for target in roles:
                if target.name == _role:
                    return True
                else:
                    await ctx.guild.create_role(name = _role)
                    return True

        if await check(_role):
            give_role = False
            _object = get(ctx.guild.roles, name = _role)

            for role in ctx.author.roles:
                if _object.name != role.name:
                    give_role = True
                else:
                    give_role = False

            if give_role == True:
                await ctx.author.add_roles(role)
                await ctx.send(
                    content = f"Automatic translation for `{target}` is now on!\nAll messages you send will now be automatically converted until this command is passed again.",
                    complete_hidden = True
                )
            else:
                await ctx.author.remove_roles(role)
                await ctx.send(
                    content = f"Automatic translation for `{target}` is now off.\nAll messages you send will no longer be automatically converted.",
                    complete_hidden = True
                )

        # await ctx.send(content = "Sorry, but this feature is not implemented yet!")

def setup(bot):
    bot.add_cog(Translation(bot))