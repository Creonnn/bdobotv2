BDOBOTv2

For the game Black Desert Online.
This is a Discord bot that can provide live market data and whether an item is worth crafting based on current market prices.

How to use the bot:
  1. Invite the bot to your server: https://discord.com/oauth2/authorize?client_id=1232481937248227409&permissions=1084479764544&scope=bot
  2. How to use:
     - Type "!m <ITEM_NAME>" to get live market data
     - Type "!r <ITEM_NAME> <OPTIONAL: MASTERY>" to get profit margins on a craftable item
         - To get a verbose reply, use command "!r!v ..."
      
Additional info:
  1. main.py: Main file to run
  2. bot.py: Listens to Discord messenger for user commands. Also handles deliverables when command is called.
  3. item.py: Creates Item object. Stores all required data within the object.
  4. message.py: Formats Item data into a deliverable message.
  5. search.py: Based on user's command, find the item within database that closely matches the query.
  6. helper.py: Module of helper functions.
  7. unpack_bytes.py: Some API responses are Huffman encoded. Need to decode them.
