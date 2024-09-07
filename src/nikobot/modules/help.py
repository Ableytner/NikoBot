import discord
from discord.ext import commands

from .. import util

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @util.hybrid_command(
        "help",
        "Show information about a command or module, or list all available commands"
    )
    async def help(self, ctx: commands.context.Context | discord.interactions.Interaction, command_name: str | None = None):
        if command_name is None:
            if util.is_slash_command(ctx):
                answer = self._generate_help_general_slash()
            else:
                answer = self._generate_help_general_normal()
        else:
            if util.is_slash_command(ctx):
                answer = self._generate_help_specific_slash(command_name)
            else:
                answer = self._generate_help_specific_normal(command_name)
        await util.reply(ctx, embed=answer)

    def _generate_help_general_normal(self) -> discord.Embed:
        cmds: dict[str, list[tuple[str, str]]] = {}
        cmds["General"] = []

        for cmd in self.bot.commands:
            if "." in cmd.name:
                groupname = cmd.name.split(".", maxsplit=1)[0]
                if groupname not in cmds:
                    cmds[groupname] = []
                cmds[groupname].append((cmd.name, cmd.description))
            else:
                cmds["General"].append((cmd.name, cmd.description))

        for groupname in cmds:
            # sort using the lowercase command name
            cmds[groupname].sort(key=lambda x: x[0].lower())

        answer = discord.Embed(title="All available commands")
        for groupname, commands in cmds.items():
            commands_texts = []
            for name, desc in commands:
                commands_texts.append(f"**{name}**")
                commands_texts.append(desc or "None")
            answer.add_field(name=groupname, value="\n".join(commands_texts), inline=False)

        return answer

    def _generate_help_general_slash(self) -> discord.Embed:
        cmds: dict[str, list[tuple[str, str]]] = {}
        cmds["General"] = []

        for cmd in self.bot.tree.get_commands():
            if isinstance(cmd, discord.app_commands.Group):
                cmds[cmd.name] = [(item.name, item.description) for item in cmd.commands]
            elif isinstance(cmd, discord.app_commands.Command):
                cmds["General"].append((cmd.name, cmd.description))
            else:
                raise TypeError(f"Unexpected type {type(cmd)}")

        for groupname in cmds:
            # sort using the lowercase command name
            cmds[groupname].sort(key=lambda x: x[0].lower())

        answer = discord.Embed(title="All available commands")
        for groupname, commands in cmds.items():
            commands_texts = []
            for name, desc in commands:
                commands_texts.append(f"**{name}**")
                commands_texts.append(desc or "None")
            answer.add_field(name=groupname, value="\n".join(commands_texts), inline=False)

        return answer

    def _generate_help_specific_normal(self, command_name: str) -> discord.Embed:
        for cmd in self.bot.commands:
            # help for module
            if "." in cmd.name \
               and cmd.name.split(".", maxsplit=1)[0].lower() == command_name.lower():
                module_name = cmd.name.split(".", maxsplit=1)[0].lower()
                answer = discord.Embed(title=f"Help for module '{module_name}'")

                answer.add_field(name="Description", value=cmd.description)

                commands_texts = []
                for command in self.bot.commands:
                    if "." in command.name \
                       and cmd.name.split(".", maxsplit=1)[0].lower() == module_name.lower():
                        commands_texts.append(f"**{command.name}**")
                        commands_texts.append(command.description or "None")
                answer.add_field(name="Available commands", value="\n".join(commands_texts), inline=False)

                return answer
            # help for command
            if cmd.name.lower() == command_name.lower() \
               or ("." in cmd.name \
               and cmd.name.split(".", maxsplit=1)[1].lower() == command_name.lower()):
                answer = discord.Embed(title=f"Help for '{cmd.name}'")

                desc = cmd.description
                if "." in cmd.name:
                    desc += f"\nCommand is a part of the '{cmd.name.split(".", maxsplit=1)[0]}' module"
                answer.add_field(name="Description", value=desc)

                return answer
        
        return discord.Embed(title=f"Command '{command_name}' not found")

    def _generate_help_specific_slash(self, command_name: str) -> discord.Embed:
        for cmd in self.bot.tree.walk_commands():
            if cmd.name == command_name:
                # help for module
                if isinstance(cmd, discord.app_commands.Group):
                    answer = discord.Embed(title=f"Help for module '{cmd.name}'")

                    answer.add_field(name="Description", value=cmd.description)

                    commands_texts = []
                    for command in cmd.commands:
                        commands_texts.append(f"**{command.name}**")
                        commands_texts.append(command.description or "None")
                    answer.add_field(name="Available commands", value="\n".join(commands_texts), inline=False)

                    return answer
                # help for command
                else:
                    answer = discord.Embed(title=f"Help for '{cmd.name}'")

                    desc = cmd.description
                    if cmd.parent is not None:
                        desc += f"\nCommand is a part of the '{cmd.parent.name}' module"
                    answer.add_field(name="Description", value=desc)

                    return answer

        return discord.Embed(title=f"Command '{command_name}' not found")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Help(bot))
