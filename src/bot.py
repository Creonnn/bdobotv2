import discord, os
from dotenv import load_dotenv
from discord.ext import tasks
from item import *
from message import Item as ItemMessage
from message import Craftable as CraftableMessage

item_message = ItemMessage()
craftable_message = CraftableMessage()

channel_id_test = 715392947608354886

def run_discord_bot():
    client = discord.Client(intents=discord.Intents.all())

    '''
    @tasks.loop(seconds = 30)
    async def pearl_alert():
        channel = client.get_channel(channel_id_test)
        pearl_outfit_sitting = pearl_outfit_alert()

        if pearl_outfit_sitting:
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=pearl_outfit_sitting,
                                  title=f"Pearl Outfit Alert")
            
            await channel.send(embed=embed)
    '''

    @client.event
    async def on_ready():
        print("We have logged in as {0.user}".format(client))
        # pearl_alert.start()
    
    @client.event
    async def on_message(message):
        disc_id = str(message.author.id)
        user_message = str(message.content).lower()
        svr_id = str(message.guild.id)

        if message.author == client.user:
            return

        if "!m" in user_message:
            input = user_message.replace('!m', '').strip()
            info = Item(input)
            deliverable = item_message.deliverable(info)
            header = f"{info.enhancement_level.upper()}: {info.name}" if info.enhancement_level else info.name
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=deliverable,
                                  title=f"{header} (Market Info)")
            
            await message.channel.send(embed=embed)

        elif "!r" in user_message:
            verbose = True if '!v' in user_message.lower() else False
            mastery = 1000
            clean_input = user_message.replace('!r', '').replace('!v', '').strip()
            if clean_input.split(" ")[-1].isdigit():
                mastery = int(clean_input.split(" ")[-1])
                clean_input = ' '.join(clean_input.split(" ")[:-1])

            info = Craftable(clean_input, mastery, verbose)
            deliverable = craftable_message.deliverable(info)
            header = f"{info.enhancement_level.upper()}: {info.name}" if info.enhancement_level else info.name
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=deliverable,
                                  title=f"{header} (Recipe Info)")
            
            await message.channel.send(embed=embed)

        
    
    load_dotenv()
    client.run(os.getenv('TOKEN'))