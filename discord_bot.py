import discord, typing
from discord.ext import commands, tasks
from discord import app_commands
from discord.ext.commands import has_permissions
from LOL import *

with open("data/discord_key.txt", "r") as key_f:
    TOKEN = key_f.read()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

loop = asyncio.get_event_loop()


@tree.command(name="active", description="shows which players are active")
async def active(interaction):
    await interaction.response.send_message(f"Getting active users ...", ephemeral=False)
    active_list = getActive()

    if len(active_list) == 0:
        text = "Everyone else has a life.  Touch some grass please."
    else:
        text = f"{len(active_list)} Players Active:"
        for name in active_list:
            text += '\n\t' + name

    await interaction.edit_original_response(content=text)


@tree.command(name="sammy", description="show Sammy bussin stats")
async def sammy(interaction):
    await interaction.response.send_message(f"Getting stats OF MY LORD SAMMY...", ephemeral=False)
    text = getStats("BroskiSammy")
    await interaction.edit_original_response(content=text)


@tree.command(name="stats", description="gets stats of any player /stats summonerName")
async def stats(interaction, summoner_name: str, platform: str = "euw1", region: str = "europe"):
    await interaction.response.send_message(f"Getting stats ...", ephemeral=False)
    text = getStats(summoner_name, platform=platform, region=region)
    await interaction.edit_original_response(content=text)


@tree.command(name="add", description="add new user")
@has_permissions(administrator=True)
async def add(interaction, summoner_name: str, platform: str = "euw1", region: str = "europe"):
    await interaction.response.send_message(f"Adding summoner '{summoner_name}' ...", ephemeral=False)
    text = addSummoner(summoner_name, platform=platform, region=region)
    await interaction.edit_original_response(content=text)


@tree.command(name="remove", description="remove user")
@has_permissions(administrator=True)
async def remove(interaction, summoner_name: str, platform: str = "euw1", region: str = "europe"):
    await interaction.response.send_message(f"Removing summoner '{summoner_name}' ...", ephemeral=False)
    text = removeSummoner(summoner_name, platform=platform, region=region)
    await interaction.edit_original_response(content=text)


@tree.command(name="track", description="track when user is live")
@has_permissions(administrator=True)
async def track(interaction, summoner_name: str, platform: str = "euw1", region: str = "europe"):
    await interaction.response.send_message(f"Tracking summoner '{summoner_name}' ...", ephemeral=False)
    text = addTrackLive(interaction.guild.id, summoner_name, platform, region)
    await interaction.edit_original_response(content=text)


@tree.command(name="track-remove", description="remove user from live tracking")
@has_permissions(administrator=True)
async def track(interaction, summoner_name: str, platform: str = "euw1", region: str = "europe"):
    await interaction.response.send_message(f"Releasing tracker on summoner '{summoner_name}' ...", ephemeral=False)
    text = removeTrackLive(interaction.guild.id, summoner_name, platform, region)
    await interaction.edit_original_response(content=text)


@client.event
async def on_ready():
    await tree.sync()

    print("Ready!")

    frequentJobs.start()


@tasks.loop(seconds=60)
async def frequentJobs():
    # testing: 432531599972892672

    # getGameResultUpdates
    result_list = await client.loop.run_in_executor(None, yieldToList, (getGameResultUpdates()))
    for result in result_list:
        guild_ids, name, kills, deaths, assists, win, lane, champion = result
        for guild in client.guilds:
            if guild.id in guild_ids:
                channel = guild.system_channel  # getting system channel
                if channel.permissions_for(guild.me).send_messages:  # making sure you have permissions
                    win_text = "won" if win else "loss"

                    msg = f"{name} has {win_text} the game as {lane} lane ({champion}) with kda {kills}/{deaths}/{assists}"
                    await channel.send(msg)

    # getTrackLive
    result_list = await client.loop.run_in_executor(None, yieldToList, (getTrackLive()))
    for live in result_list:
        guild_ids, (summoner_name, platform, region) = live
        for guild in client.guilds:
            if guild.id in guild_ids:
                channel = guild.system_channel  # getting system channel
                if channel.permissions_for(guild.me).send_messages:  # making sure you have permissions
                    text = f"{summoner_name} is LIVE!  What are the changes of winning?"
                    message = await channel.send(text)
                    await message.add_reaction('✔')
                    await message.add_reaction('❌')


client.run(TOKEN)
