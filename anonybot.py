from dotenv import load_dotenv
import os
import discord

def main():
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')

    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user.name} connected')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        guild = next((g for g in client.guilds if g.get_member(message.author.id)), None)
        if guild:

            guild = client.guilds[0]
            channel = next((c for c in guild.channels if c.name == "anonymous"), None)

            if channel:
                await channel.send(message.content)
            else:
                await message.channel.send("No #anonymous channel in the server")
        else:
            await message.channel.send("More than one matching server, panic")

    client.run(TOKEN)

if __name__ == "__main__":
    main()