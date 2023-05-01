import re
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
        funcs = [anonymous, bucket]
        for func in funcs:
            if await func(message):
                #print(f"applying {func.__name__}")
                break

    async def anonymous(message):
        # Don't post my own messages
        if message.author == client.user:
            return False
        # Only care about DMs
        if not isinstance(message.channel, discord.DMChannel):
            return False

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
        await channel.send(f"{author_emoji} {message.content}")
        return True


    bucket_storage = []
    async def bucket(message):
        # Don't respond to my own messages
        if message.author == client.user:
            return False

        # Don't care about DMs
        if isinstance(message.channel, discord.DMChannel):
            return False

        # Check if the message is a bucket command
        lower_message = message.content.lower()
        
        regex_match = re.match(r"(?i)^[\*\_]*(give|hand|pass)(s)? bucket (.*)", lower_message)
        if not regex_match:
            return False

        bucket_take_phrases = ["takes", "grabs", "yoinks", "steals", "snatches", "snags", "pilfers", "nabs", "swipes", "plunders", "filches", "purloins", "lifts", "pinches", "liberates", "misappropriates", "acquires", "confiscates", "expropriates", "annexes", "\"impounds\"", "seizes hold of", "commandeers", "hijacks", "kidnaps", "embezzles"]
        take_phrase = bucket_take_phrases[random.randrange(len(bucket_take_phrases))]

        item = regex_match[3]
        if len(bucket_storage) > 10:
            to_remove = bucket_storage.pop(random.randrange(len(bucket_storage)))
            bucket_storage.append(item)            
            
            bucket_drop_phrases = ["drops", "yeets", "spits out", "vomits", "farts out", "releases, like a small pigeon,"]
            drop_phrase = bucket_drop_phrases[random.randrange(len(bucket_drop_phrases))]

            await message.channel.send(f"bucket {take_phrase} {item} but {drop_phrase} {to_remove}")
        else:
            bucket_eat_phrases = ["caresses it gently", "yeets it within itself", "consumes it with a belch"]
            bucket_storage.append(item)
            eat_phrase = bucket_eat_phrases[random.randrange(len(bucket_eat_phrases))]

            await message.channel.send(f"bucket {take_phrase} {item} and {eat_phrase}")
        
        return True

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
        emoji_options_copy = emoji_options.copy()
        for emoji in in_use:
            emoji_options_copy.remove(emoji)
        if len(emoji_options_copy) == 0:
            print("No unused emoji left!")
            return "💩"
        else:
            return random.choice(emoji_options_copy)

    
    client.run(TOKEN)


if __name__ == "__main__":
    main()