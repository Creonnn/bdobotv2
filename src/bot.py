import discord, os
from dotenv import load_dotenv
from discord.ext import tasks
from market_recipe import *


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
        """
        if '!m' in user_message:
            name, info = market_info(user_message[3:])
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=info,
                                  title=f'{name} (Market Info)')
            
            await message.channel.send(embed=embed)

        elif '!r' in user_message:
            verbose = True if '!v' in user_message.lower() else False
            mastery = 1000
            clean_input = user_message.replace('!r', '').replace('!v', '').strip()
            if user_message.split()[-1].isdigit():
                mastery = int(clean_input.split()[-1])
                name, info = recipe_info(clean_input, mastery, verbose)
            else:
                name, info = recipe_info(clean_input, mastery, verbose)

            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=info,
                                  title=f"{name} (Recipe Info)")
            await message.channel.send(embed=embed)
        """

        if "!m" in user_message:
            input = user_message.replace('!t1', '').strip()
            info = Market(input)
            name = f"{info.enhancement_level.upper()}: {info.name}" if info.enhancement_level else info.name
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=info.deliverable(),
                                  title=f"{name} (Market Info)")
            
            await message.channel.send(embed=embed)

        elif "!r" in user_message:
            verbose = True if '!v' in user_message.lower() else False
            mastery = 1000
            clean_input = user_message.replace('!t2', '').replace('!v', '').strip()
            if clean_input.split(" ")[-1].isdigit():
                mastery = int(clean_input.split(" ")[-1])
                clean_input = ' '.join(clean_input.split(" ")[:-1])

            info = Craftable(clean_input, mastery, verbose)
            name = f"{info.enhancement_level.upper()}: {info.name}" if info.enhancement_level else info.name
            embed = discord.Embed(colour=discord.Colour.red(),
                                  description=info.deliverable(),
                                  title=f"{name} (Recipe Info)")
            
            await message.channel.send(embed=embed)

        
    
    load_dotenv()
    client.run(os.getenv('TOKEN'))