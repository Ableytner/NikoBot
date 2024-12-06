"""A module containing the help command"""

import discord as discordpy
from discord.ext import commands

from .. import util

class Help(commands.Cog):
    """A ``discord.commands.Cog`` containing the help command"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @util.discord.hybrid_command(
        "help",
        "Show information about a command or module, or list all available commands"
    )
    async def help(self,
                   ctx: commands.context.Context | discordpy.interactions.Interaction,
                   command_name: str | None = None):
        """
        Discord command displaying all commands
        
        If a command_name is given, display help about the command or module
        """

        sent_by_owner = util.discord.is_sent_by_owner(ctx)

        if command_name is None:
            if util.discord.is_slash_command(ctx):
                answer = self._generate_help_general_slash(sent_by_owner)
            else:
                answer = self._generate_help_general_normal(sent_by_owner)
        else:
            if util.discord.is_slash_command(ctx):
                answer = self._generate_help_specific_slash(command_name)
            else:
                answer = self._generate_help_specific_normal(command_name)

        await util.discord.reply(ctx, embed=answer)

    def _generate_help_general_normal(self, sent_by_owner: bool = False) -> discordpy.Embed:
        cmds_grouped: dict[str, list[tuple[str, str]]] = {}
        cmds_grouped["General"] = []

        for cmd in self.bot.commands:
            if cmd.description.startswith("__hidden__") and not sent_by_owner:
                continue

            if "." in cmd.name:
                groupname = cmd.name.split(".", maxsplit=1)[0]
                if groupname not in cmds_grouped:
                    cmds_grouped[groupname] = []
                cmds_grouped[groupname].append((cmd.name, cmd.description))
            else:
                cmds_grouped["General"].append((cmd.name, cmd.description))

        for cmds in cmds_grouped.values():
            # sort using the lowercase command name
            cmds.sort(key=lambda x: x[0].lower())

        answer = discordpy.Embed(title="All available commands")
        for groupname, cmds in cmds_grouped.items():
            commands_texts = []
            for name, desc in cmds:
                commands_texts.append(f"**{name}**")
                commands_texts.append(desc.strip("__hidden__") or "None")
            answer.add_field(name=groupname, value="\n".join(commands_texts), inline=False)

        return answer

    def _generate_help_general_slash(self, sent_by_owner: bool = False) -> discordpy.Embed:
        cmds_grouped: dict[str, list[tuple[str, str]]] = {}
        cmds_grouped["General"] = []

        for cmd in self.bot.tree.get_commands():
            if cmd.description.startswith("__hidden__") and not sent_by_owner:
                continue

            if isinstance(cmd, discordpy.app_commands.Group):
                cmds_grouped[cmd.name] = [(item.name, item.description) for item in cmd.commands]
            elif isinstance(cmd, discordpy.app_commands.Command):
                cmds_grouped["General"].append((cmd.name, cmd.description))
            else:
                raise TypeError(f"Unexpected type {type(cmd)}")

        for cmds in cmds_grouped.values():
            # sort using the lowercase command name
            cmds.sort(key=lambda x: x[0].lower())

        answer = discordpy.Embed(title="All available commands")
        for groupname, cmds in cmds_grouped.items():
            commands_texts = []
            for name, desc in cmds:
                commands_texts.append(f"**{name}**")
                commands_texts.append(desc.strip("__hidden__") or "None")
            answer.add_field(name=groupname, value="\n".join(commands_texts), inline=False)

        return answer

    def _generate_help_specific_normal(self, command_name: str) -> discordpy.Embed:
        for cmd in self.bot.commands:
            # help for module
            if "." in cmd.name \
               and cmd.name.split(".", maxsplit=1)[0].lower() == command_name.lower():
                module_name = cmd.name.split(".", maxsplit=1)[0].lower()
                answer = discordpy.Embed(title=f"Help for module '{module_name}'")

                answer.add_field(name="Description", value=cmd.description)

                commands_texts = []
                for command in self.bot.commands:
                    if "." in command.name \
                       and command.name.split(".", maxsplit=1)[0].lower() == module_name.lower():
                        commands_texts.append(f"**{command.name}**")
                        commands_texts.append(command.description or "None")
                answer.add_field(name="Available commands", value="\n".join(commands_texts), inline=False)

                return answer
            # help for command
            if cmd.name.lower() == command_name.lower() \
               or ("." in cmd.name \
               and cmd.name.split(".", maxsplit=1)[1].lower() == command_name.lower()):
                answer = discordpy.Embed(title=f"Help for '{cmd.name}'")

                desc = cmd.description.strip("__hidden__")
                if "." in cmd.name:
                    desc += f"\nCommand is a part of the '{cmd.name.split(".", maxsplit=1)[0]}' module"
                answer.add_field(name="Description", value=desc)

                return answer

        return discordpy.Embed(title=f"Command '{command_name}' not found")

    def _generate_help_specific_slash(self, command_name: str) -> discordpy.Embed:
        for cmd in self.bot.tree.walk_commands():
            if cmd.name == command_name:
                # help for module
                if isinstance(cmd, discordpy.app_commands.Group):
                    answer = discordpy.Embed(title=f"Help for module '{cmd.name}'")

                    answer.add_field(name="Description", value=cmd.description)

                    commands_texts = []
                    for command in cmd.commands:
                        commands_texts.append(f"**{command.name}**")
                        commands_texts.append(command.description or "None")
                    answer.add_field(name="Available commands", value="\n".join(commands_texts), inline=False)

                    return answer

                # help for command
                answer = discordpy.Embed(title=f"Help for '{cmd.name}'")

                desc = cmd.description.strip("__hidden__")
                if cmd.parent is not None:
                    desc += f"\nCommand is a part of the '{cmd.parent.name}' module"
                answer.add_field(name="Description", value=desc)

                return answer

        return discordpy.Embed(title=f"Command '{command_name}' not found")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Help(bot))
