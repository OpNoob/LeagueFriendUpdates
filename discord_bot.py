import discord, typing
from discord.ext import commands, tasks
from discord import app_commands
from LOL import *

with open("data/discord_key.txt", "r") as key_f:
    TOKEN = key_f.read()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="active", description="shows which players are active")
async def active(interaction):
    active_list = getActive()

    if len(active_list) == 0:
        text = "Everyone else has a life.  Touch some grass please."
    else:
        text = f"{len(active_list)} Players Active:"
        for name in active_list:
            text += '\n\t' + name

    await interaction.response.send_message(text)


@tree.command(name="sammy", description="show Sammy bussin stats")
async def sammy(interaction):
    text = getStats("BroskiSammy")

    await interaction.response.send_message(text)


# @app_commands.choices(option=[
#     app_commands.Choice(name="summoner_name", value="BroskiSammy"),
# ])
@tree.command(name="stats", description="gets stats of any player /stats summonerName")
async def stats(interaction, summoner_name: str):
    text = getStats(summoner_name)
    await interaction.response.send_message(text)


@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")

    gameResultAnnouncements.start()


@tasks.loop(seconds=60)
async def gameResultAnnouncements():
    for result in getGameResultUpdates():
        name, kills, deaths, assists, win, lane, champion = result
        for guild in client.guilds:
            channel = guild.system_channel  # getting system channel
            if channel.permissions_for(guild.me).send_messages:  # making sure you have permissions
                win_text = "won" if win else "loss"

                msg = f"{name} has {win_text} the game as {lane} lane ({champion}) with kda {kills}/{deaths}/{assists}"
                await channel.send(msg)


client.run(TOKEN)
