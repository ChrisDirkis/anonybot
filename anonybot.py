import re
from dotenv import load_dotenv
import os
import random
import datetime
from collections import namedtuple

import discord
import requests

def main():
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')
    MODES = os.getenv('MODES', "ANON,BUCKET,EXPAND").split(',')
    MDB_POSE_THRESHOLD = float(os.getenv('MDB_POSE_THRESHOLD', "0"))

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
        for func in funcs:
            if await func(message):
                # print(f"applied {func.__name__}")
                break

    @no_self_respond(client)
    @dm_only
    async def anonymous(message):
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
    bucket_drop_phrases = [
        ("drops", 100),
        ("yeets", 5),
        ("spits out", 10),
        ("vomits", 5),
        ("farts out", 10),
        ("releases, like a small pigeon,", 1),
    ]

    @no_self_respond(client)
    @channel_only
    async def bucket_give_item(message):
        # Check if the message is a bucket give command, and if so, figure out what he's being given
        message_text = strip_formatting(message.content)
        bucket_processors = [bucket_put_processor, bucket_give_processor]
        for processor in bucket_processors:
            if item := processor(message_text):
                break
        else:
            return False

        # take the item, elaborately
        bucket_take_phrases = [
            ("takes", 100), 
            ("grabs", 100), 
            ("yoinks", 10), 
            ("steals", 10), 
            ("snatches", 20), 
            ("snags", 1), 
            ("pilfers", 1), 
            ("nabs", 1), 
            ("swipes", 1), 
            ("plunders", 1), 
            ("filches", 1), 
            ("purloins", 1), 
            ("lifts", 1), 
            ("pinches", 1), 
            ("liberates", 1), 
            ("misappropriates", 1), 
            ("acquires", 10), 
            ("confiscates", 1), 
            ("expropriates", 1), 
            ("annexes", 1), 
            ("\"impounds\"", 1), 
            ("seizes hold of", 1), 
            ("commandeers", 1), 
            ("hijacks", 1), 
            ("kidnaps", 1), 
            ("embezzles", 1),
        ]
        take_phrase = select_weighted(bucket_take_phrases)
        
        if len(bucket_storage) > 10:
            to_remove = bucket_storage.pop(random.randrange(len(bucket_storage)))
            bucket_storage.append(item)            
            
            drop_phrase = select_weighted(bucket_drop_phrases)

            await message.reply(f"Bucket {take_phrase} {item} but {drop_phrase} {to_remove}")
        else:
            bucket_storage.append(item)
            
            bucket_eat_phrases = [
                ("", 100),
                (", and caresses it gently", 50),
                (", and yeets it within itself",  50),
                (", and consumes it with a belch", 50),
                (", without a word of complaint", 50),
                (", begrudgingly", 50),
            ]
            eat_phrase = select_weighted(bucket_eat_phrases)
            await message.reply(f"Bucket {take_phrase} {item}{eat_phrase}")
        
        return True

    @no_self_respond(client)
    @channel_only
    async def bucket_take_item(message):
        # Check if the message is a bucket take command
        message_text = strip_formatting(message.content)
        regex_match = re.match(r"(?i)^(take|takes|steal|steals)( something|an item)? from bucket", message_text)
        if not regex_match:
            return None

        if len(bucket_storage) > 0:
            item = bucket_storage.pop(random.randrange(len(bucket_storage)))
            drop_phrase = select_weighted(bucket_drop_phrases)
            await message.reply(f"Bucket {drop_phrase} {item}")
        else:
            await message.reply("You tip Bucket over and shake him out, but there's nothing there :(")
        
        return True
    
    @no_self_respond(client)
    @channel_only
    async def bucket_inventory(message):
        # Check if the message is a bucket inventory command
        message_text = strip_formatting(message.content)
        regex_match = re.match(r"(?i)^(look|looks) in(to|side)? bucket", message_text)
        if not regex_match:
            return False

        if len(bucket_storage) > 0:
            await message.reply(f"Bucket currently contains: {'; '.join(bucket_storage)}")
        else:
            await message.reply("You tip Bucket over and shake him out, but there's nothing there :(")
        
        return True

    ai_url = "http://127.0.0.1:5000/v1/chat/completions"
    ai_headers ={"Content-Type": "application/json"}
    thinking_react = "💭"

    async def reply_split(message: discord.Message, response):
        await message.add_reaction(thinking_react)

        max_len = 1999

        response = [response]
        while len(response[-1]) > max_len:
            last = response[-1]
            del response[-1]

            # lol, this can still be stupid, but hopefully less stupid
            start_point = max_len if len(last) >= max_len * 2 else len(last) // 2 
            for i in range(start_point, 0, -1):
                if last[i] == " ":
                    response.append(last[:i])
                    response.append(last[i + 1:])
                    break

        for msg in response:
            await message.reply(msg)

        await message.remove_reaction(thinking_react, client.user)


    def ask_bucket(message, context = None):

        messages = []
        if context:
            messages += context
        messages.append({"role": "user", "content": message})
        
        print(messages)

        data = {
            "mode": "chat-instruct",
            "character": "Bucket",
            "max_tokens": 500,
            "messages": messages
        }
        
        response = requests.post(
            ai_url, 
            headers=ai_headers,
            json=data,
            verify=False
        )

        return strip_quotes(response.json()['choices'][0]['message']['content'])


    @no_self_respond(client)
    @channel_only
    async def million_dollars_but_answer(message):
        message_text = strip_formatting(message.content)
        regex_match = re.match(r"(?i)^would you rather|million dollars but", message_text)
        if not regex_match:
            return False

        async with message.channel.typing():
            await reply_split(message, ask_bucket(message_text))
        
        return True


    @no_self_respond(client)
    @channel_only 
    async def million_dollars_but_pose(message):
        if random.random() > MDB_POSE_THRESHOLD:
            return False

        instruction = "Pose a \"Would You Rather\" question. The condition should be weird and provoke discussion. The format should be \"Would you rather [x] or [y]?\". Don't be too verbose, just the question please."
        async with message.channel.typing():
            await reply_split(message, f"Bucket wonders: {ask_bucket(instruction)}")
        
        return True


    async def get_reply(message: discord.Message) -> discord.Message or None:
        if not message.reference:
            return None

        if message.reference.cached_message:
            return message.reference.cached_message
        else:
            return await message.channel.fetch_message(message.reference.message_id)


    @no_self_respond(client)
    @channel_only
    async def reply_to_bucket(message: discord.Message):

        if not message.reference:
            return False

        referenced_message = await get_reply(message)
        if referenced_message.author.id != client.user.id:
            return False

        name_pattern = r"(?i)\<\@" + str(client.user.id) + r"\>"
        reply_chain = []
        while referenced_message:
            role = "assistant" if referenced_message.author.id == client.user.id else "user" #referenced_message.author.display_name
            message_text = re.sub(name_pattern, "Bucket,", referenced_message.content)
            reply_chain.append({"role": role, "content": message_text})
            referenced_message = await get_reply(referenced_message)
        reply_chain.reverse()    
        
        name_pattern = r"(?i)\<\@" + str(client.user.id) + r"\>"
        message_text = strip_formatting(message.content)
        message_text = re.sub(name_pattern, "Bucket,", message_text)

        async with message.channel.typing():
            await reply_split(message, ask_bucket(message_text, context=reply_chain))
        
        return True

    @no_self_respond(client)
    @channel_only
    async def at_bucket(message):
        name_pattern = r"(?i)\<\@" + str(client.user.id) + r"\>"
        message_text = strip_formatting(message.content)
        regex_match = re.match(name_pattern, message_text)
        if not regex_match:
            return False

        message_text = re.sub(name_pattern, "Bucket,", message_text)
        async with message.channel.typing():
            await reply_split(message, ask_bucket(message_text))
        
        return True

    expansion = namedtuple("expansion", ["regex", "fr", "to"])
    expansions = [
        expansion(r"(?i)https?://twitter.com/[^/]+/status/\d+", "twitter.com/", "vxtwitter.com/"),
        expansion(r"(?i)https?://x.com/[^/]+/status/\d+", "x.com/", "vxtwitter.com/"),
        expansion(r"(?i)https?://(www.)?tiktok.com/", "tiktok.com/", "vxtiktok.com/"),
    ]

    @no_self_respond(client)
    @channel_only
    async def expand(message):
        content = message.content
        any_expanded = False
        for expansion in expansions:
            if not re.match(expansion["regex"], content):
                continue
            any_expanded = True
            content = content.replace(expansion["fr"], expansion["to"])
            
        if not any_expanded:
            return False
        
        await reply_split(message, content)
        return True


    async def find_anon_channel(client, message):
        guilds = [g for g in client.guilds if g.get_member(message.author.id)]
        channels = [[c for c in guild.channels if c.name == "anonymous"] for guild in guilds]
        channels = [channel for sublist in channels for channel in sublist]
        if not channels:
            message.channel.send("Couldn't find a matching #anonymous channel")
            return None
        if len(channels) > 1:
            await message.channel.send("More than one matching server, panic")
            return None
        return channels[0]


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
        remaining = set(emoji_options) - set(in_use)
        if len(remaining) == 0:
            print("No unused emoji left!")
            return "💩"
        else:
            return random.choice(remaining)
    

    funcs = []
    if "ANON" in MODES:
        funcs.append(anonymous)
    if "EXPAND" in MODES:
        funcs.append(expand)
    if "BUCKET" in MODES:
        funcs.append(bucket_give_item)
        funcs.append(bucket_take_item)
        funcs.append(bucket_inventory)
    if "AI" in MODES:
        funcs.append(reply_to_bucket)
        funcs.append(at_bucket)
        funcs.append(million_dollars_but_answer)
        funcs.append(million_dollars_but_pose)

    client.run(TOKEN)

def bucket_give_processor(message):
    give_options = ["give", "hand", "pass", "gives", "hands", "passes"]
    give_options_piped = "|".join(give_options)
    regex_match = re.match(fr"(?i)^({give_options_piped}) bucket (.*)", message)
    if not regex_match:
        return None
    return regex_match[2]

def bucket_put_processor(message: str):
    put_options = ["put", "place", "puts", "places"]
    put_options_piped = "|".join(put_options)
    regex_match = re.match(fr"(?i)^({put_options_piped}) (.*) in(to)? bucket", message)
    if not regex_match:
        return None
    return regex_match[2]

def select_weighted(lst):
    total = sum(item[1] for item in lst)
    r = random.uniform(0, total)
    upto = 0
    for item, weight in lst:
        if upto + weight >= r:
            return item
        upto += weight


def strip_formatting(message):
    while True:
        if message.startswith("*") and message.endswith("*"):
            message = message[1:-1]
        elif message.startswith("_") and message.endswith("_"):
            message = message[1:-1]
        else:
            break
    return message

def strip_quotes(message):
    while True:
        if message.startswith("\"") and message.endswith("\""):
            message = message[1:-1]
        else:
            break
    return message

def dm_only(func):
    async def wrapper(message):
        if not isinstance(message.channel, discord.DMChannel):
            return False
        return await func(message)
    return wrapper

def channel_only(func):
    async def wrapper(message):
        if isinstance(message.channel, discord.DMChannel):
            return False
        return await func(message)
    return wrapper

def no_self_respond(client):
    def decorator(func):
        async def wrapper(message):
            if message.author == client.user:
                return False
            return await func(message)
        return wrapper
    return decorator

if __name__ == "__main__":
    main()