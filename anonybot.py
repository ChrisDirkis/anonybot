from dotenv import load_dotenv
import os
import random
import datetime

import discord

def main():
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')
    emoji_timeout_seconds = 60 * 60

    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)

    emoji_options = [
        "🐢","🐤","🐒","🦊","🐔","🐧","🐦","🦤","🦅","🐛","🦄","🐴","🐌","🐷","🐮","🐨","🐻‍❄️","🐳","🐬","🐟","🦭","🐠","🐘","🦛","🦬","🦣","🦏","🐫","🦒","🦘","🐐","🐑","🐖","🦌","🦩","🦚","🦃","🐓","🦜","🦢","🦫","🦡","🦦","🐀","🐁","🦥","🐉","🕊️","🏍️","🚗","🚑","🗿","🚀","✈️","🎺","🎷","🪘","🎸","🪕","🎻","🎯","🥓","🥩","🥞","🌮","🥑","🫐","🍿","☕","🍵","🍺","🥂","🧂"
    ]
    author_emojis = dict()
    in_use = set()


    @client.event
    async def on_ready():
        print(f'{client.user.name} connected')


    @client.event
    async def on_message(message):
        # Don't post my own messages
        if message.author == client.user:
            return
        # Only care about DMs
        if not isinstance(message.channel, discord.DMChannel):
            return

        clear_stale_author_emojis()
        
        # Get the user's anon channel, or bail if can't
        channel = await find_anon_channel(client, message)
        if channel == None:
            return

        # Get emoji from the cache, or make an emoji
        author_id = message.author.id
        author_emoji = author_emojis[author_id]["emoji"] \
            if author_id in author_emojis \
            else random_new_emoji()

        # Update the emoji cache
        author_emojis[author_id] = {
            "emoji": author_emoji,
            "time": message.created_at
        }
        in_use.add(author_emoji)

        # Send the message with the emoji prepended
        return await channel.send(f"{author_emoji}: {message.content}")


    async def find_anon_channel(client, message):
        guild = next((g for g in client.guilds if g.get_member(message.author.id)), None)
        if guild:

            guild = client.guilds[0]
            channel = next((c for c in guild.channels if c.name == "anonymous"), None)

            if channel:
                return channel
            else:
                await message.channel.send("No #anonymous channel in the server")
                return None
        else:
            await message.channel.send("More than one matching server, panic")
            return None


    def clear_stale_author_emojis():
        expiry = datetime.datetime.utcnow() - datetime.timedelta(seconds=emoji_timeout_seconds)
        to_remove = []
        for user_id in author_emojis:
            if author_emojis[user_id]["time"] < expiry:
                in_use.remove(author_emojis[user_id]["emoji"])
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del author_emojis[user_id]


    def random_new_emoji():
        emoji = random.choice(emoji_options)
        while emoji in in_use:
            emoji = random.choice(emoji_options)
        
        return emoji

    
    client.run(TOKEN)


if __name__ == "__main__":
    main()