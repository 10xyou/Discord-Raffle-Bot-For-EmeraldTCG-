import discord
from discord import state
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import json

# Load bot token
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Channel raffle state
channel_states = {}

STATE_FILE = "raffle_state.json"

def is_unclaimed(owner):
    return not owner or owner.strip() == ""

# Load raffle state from file
def load_state():
    global channel_states
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            channel_states = {int(k): v for k, v in data.items()}
    except FileNotFoundError:
        channel_states = {}

# Save raffle state to file
def save_state():
    # Convert message objects to message IDs
    safe_states = {}
    for k, v in channel_states.items():
        safe = v.copy()
        if "spots_messages" in safe:
            safe["spots_messages"] = [m.id if hasattr(m, "id") else m for m in safe["spots_messages"]]
        safe_states[k] = safe
    with open(STATE_FILE, "w") as f:
        json.dump(safe_states, f)

@bot.event
async def on_ready():
    load_state()
    print(f"✅ Logged in as {bot.user}")

    # Restore spot messages as message objects
    for channel_id, state in channel_states.items():
        if state.get("active"):
            channel = bot.get_channel(channel_id)
            if channel:
                restored_msgs = []
                for msg_id in state.get("spots_messages", []):
                    try:
                        msg = await channel.fetch_message(msg_id)
                        restored_msgs.append(msg)
                    except discord.NotFound:
                        print(f"Message ID {msg_id} not found in channel {channel.name}")
                state["spots_messages"] = restored_msgs
                await channel.send("🔄 Bot restarted and restored raffle state.")

@bot.command()
@commands.has_role("Trusted Seller")
async def start(ctx):
    channel_id = ctx.channel.id

    if channel_states.get(channel_id, {}).get("active", False):
        await ctx.send("❗A raffle is already running in this channel. Use `!stop` to end it.")
        return

    await ctx.send("What are you raffling?")
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    x = (await bot.wait_for('message', check=check)).content

    await ctx.send("How many spots:")
    y = int((await bot.wait_for('message', check=check)).content)

    await ctx.send("Price per spot (Insert Number Only e.g 3):")
    z = float((await bot.wait_for('message', check=check)).content)

    await ctx.send("What's your Revolut?")
    rev = (await bot.wait_for('message', check=check)).content

    await ctx.send(f"✅ Raffling \n\n {x} \n\n At {y} spots \n\n €{z} Per spot \n \n <@&1155197605597434037>")

    if "@" not in rev:
        rev = f"@{rev}"
    elif "@" in rev:
        pass

    spot_owners = [None] * y
    spots_messages = []
    spots_per_message = 50

    for start in range(0, y, spots_per_message):
        chunk = ""
        for i in range(start, min(start + spots_per_message, y)):
            chunk += f"{i + 1}.\n"
        msg = await ctx.send(chunk)
        spots_messages.append(msg)

    channel_states[channel_id] = {
        "spot_owners": spot_owners,
        "total_spots": y,
        "active": True,
        "spots_messages": spots_messages,
        "price_per_spot": z,
        "paused": False,
        "revolut": rev
    }

    save_state()

@bot.command()
async def remove(ctx, *args):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    try:
        removed_spots = set(int(arg) for arg in args)
    except ValueError:
        await ctx.send("❌ Invalid input. Use numbers only e.g. `!remove 3 5 1`.")
        return

    updated = False
    for r_spot in removed_spots:
        if 1 <= r_spot <= state["total_spots"]:
            index = r_spot - 1
            owner = state["spot_owners"][index]
            if is_unclaimed(owner):
                await ctx.send(f"❌ Spot {r_spot} is already empty.")
            elif ctx.author.mention in owner:
                state["spot_owners"][index] = None
                updated = True
            else:
                await ctx.send(f"❌ You do not own spot {r_spot}, it belongs to {owner}.")
        else:
            await ctx.send(f"❌ Spot {r_spot} is out of range.")
    await ctx.message.add_reaction("✅")
    if updated:
        await update_spots_message(state)
        save_state()

@bot.command()
async def spots(ctx, *args):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]
    paused = state["paused"]

    if paused == True:
        await ctx.send("⚠️ Main is closed. Last spots are in Mini.")
        return

    try:
        selected_spots = set(int(arg) for arg in args)
    except ValueError:
        await ctx.send("❌ Invalid input. Use numbers only e.g. `!spots 3 5 1`.")
        return

    for spot in selected_spots:
        if 1 <= spot <= state["total_spots"]:
            index = spot - 1
            if is_unclaimed(state["spot_owners"][index]):
                state["spot_owners"][index] = ctx.author.mention
            else:
                await ctx.send(f"❌ Spot {spot} is already taken.")
                if len(args) < 2:
                    return
        else:
            await ctx.send(f"❌ Spot {spot} is out of range.")
            return

    if state["spot_owners"].count(None) == 0:
        await ctx.send("✅ All spots are filled!")

        spot_owers = state["spot_owners"]
        rev = state["revolut"]

        owner_spots = {}
        for i, owner in enumerate(spot_owners):
            if owner is not None:
                owner_spots.setdefault(owner, []).append(i + 1)
            else:
                owner_spots[owner] = [i + 1]

        for owner, spots in owner_spots.items():
            spot_word = "spot" if len(spots) == 1 else "spots"
            spots_list = ', '.join(map(str, spots))
            if 'Mini' not in owner:
                amount = price_per_spot * len(spots)
                await ctx.send(
                    f"{owner} has {len(spots)} {spot_word}: {spots_list}. Amount to pay: €{amount:.2f}")
        if 'gmail' in rev:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Paypal:** {rev}")
        else:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Revolut:** {rev}")
    await ctx.message.add_reaction("✅")
    await update_spots_message(state)
    save_state()

@bot.command()
async def minirandoms(ctx, arg):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]
    paused = state["paused"]

    if paused == True:
        await ctx.send("⚠️ Main is closed. Last spots are in Mini.")
        return

    try:
        randomSpot = int(arg)
    except ValueError:
        await ctx.send("❌ Please provide a valid number for spots to claim randomly. e.g. `!minirandoms 3`.")
        return

    notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]

    if randomSpot > len(notFilled):
        await ctx.send(f"❌ You requested {randomSpot} spots, but only {len(notFilled)} are available.")
        return

    for _ in range(randomSpot):
        notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]
        if not notFilled:
            break
        randomNumber = random.choice(notFilled)
        index = randomNumber - 1
        spot_owners[index] = f"{ctx.author.mention} Mini 💰"

    if state["spot_owners"].count(None) == 0:
        await ctx.send("✅ All spots are filled!")

        spot_owers = state["spot_owners"]
        rev = state["revolut"]

        owner_spots = {}
        for i, owner in enumerate(spot_owners):
            if owner is not None:
                owner_spots.setdefault(owner, []).append(i + 1)
            else:
                owner_spots[owner] = [i + 1]

        for owner, spots in owner_spots.items():
            spot_word = "spot" if len(spots) == 1 else "spots"
            spots_list = ', '.join(map(str, spots))
            if 'Mini' not in owner:
                amount = price_per_spot * len(spots)
                await ctx.send(
                    f"{owner} has {len(spots)} {spot_word}: {spots_list}. Amount to pay: €{amount:.2f}")

        if 'gmail' in rev:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Paypal:** {rev}")
        else:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Revolut**: {rev}")

    await ctx.message.add_reaction("✅")
    await update_spots_message(state)
    save_state()


@bot.command()
async def randoms(ctx, arg):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]
    paused = state["paused"]

    if paused == True:
        await ctx.send("⚠️ Main is closed. Last spots are in Mini.")
        return

    try:
        randomSpot = int(arg)
    except ValueError:
        await ctx.send("❌ Please provide a valid number for spots to claim randomly. e.g. `!randoms 3`.")
        return

    notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]

    if randomSpot > len(notFilled):
        await ctx.send(f"❌ You requested {randomSpot} spots, but only {len(notFilled)} are available.")
        return

    for _ in range(randomSpot):
        notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]
        if not notFilled:
            break
        randomNumber = random.choice(notFilled)
        index = randomNumber - 1
        spot_owners[index] = ctx.author.mention

    if state["spot_owners"].count(None) == 0:
        await ctx.send("✅ All spots are filled!")

        spot_owers = state["spot_owners"]
        rev = state["revolut"]

        owner_spots = {}
        for i, owner in enumerate(spot_owners):
            if owner is not None:
                owner_spots.setdefault(owner, []).append(i + 1)
            else:
                owner_spots[owner] = [i + 1]

        for owner, spots in owner_spots.items():
            spot_word = "spot" if len(spots) == 1 else "spots"
            spots_list = ', '.join(map(str, spots))
            if 'Mini' not in owner:
                amount = price_per_spot * len(spots)
                await ctx.send(
                    f"{owner} has {len(spots)} {spot_word}: {spots_list}. Amount to pay: €{price_per_spot * len(spots)}")
        if 'gmail' in rev:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Paypal:** {rev}")
        else:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Revolut:** {rev}")
    await ctx.message.add_reaction("✅")
    await update_spots_message(state)
    save_state()


@bot.command()
async def mini(ctx, *args):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ No active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]
    paused = state["paused"]

    if paused == True:
        await ctx.send("⚠️ Main is closed. Last spots are in Mini.")
        return

    try:
        selected_mini = set(int(arg) for arg in args)
    except ValueError:
        await ctx.send("❌ Invalid input. Use numbers only e.g. `!mini 3 5 1`. or `!minirandoms 3' for 3 randoms`.")
        return

    for spot in selected_mini:
        if 1 <= spot <= state["total_spots"]:
            index = spot - 1
            if is_unclaimed(state["spot_owners"][index]):
                state["spot_owners"][index] = f"{ctx.author.mention} Mini 💰"
            else:
                await ctx.send(f"❌ Spot {spot} is already taken by {state['spot_owners'][index]}.")
                return
        else:
            await ctx.send(f"❌ Spot {spot} is out of range.")
            return

    if state["spot_owners"].count(None) == 0:
        await ctx.send("✅ All spots are filled!")

        spot_owers = state["spot_owners"]
        rev = state["revolut"]

        owner_spots = {}
        for i, owner in enumerate(spot_owners):
            if owner is not None and 'Mini'not in owner:
                owner_spots.setdefault(owner, []).append(i + 1)
            else:
                owner_spots[owner] = [i + 1]

        for owner, spots in owner_spots.items():
            spot_word = "spot" if len(spots) == 1 else "spots"
            spots_list = ', '.join(map(str, spots))
            if 'Mini' not in owner:
                amount = price_per_spot * len(spots)
                await ctx.send(
                    f"{owner} has {len(spots)} {spot_word}: {spots_list}. Amount to pay: €{amount:.2f}")
        if 'gmail' in rev:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Paypal:** {rev}")
        else:
            await ctx.send("\u200b\n\n\n")
            await ctx.send(f"**Revolut:** {rev}")
    await ctx.message.add_reaction("✅")
    await update_spots_message(state)
    save_state()

@bot.command()
async def paid(ctx):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ No active raffle in this channel.")
        return

    updated = False
    for i, owner in enumerate(state["spot_owners"]):
        if owner and ctx.author.mention in owner and "💰" not in owner and 'Mini' in owner:
            state["spot_owners"][i] = f"{ctx.author.mention} Mini 💰"
            updated = True

        elif owner and ctx.author.mention in owner and "💰" not in owner:
            state["spot_owners"][i] = f"{ctx.author.mention} 💰"
            updated = True

    await ctx.message.add_reaction("💰")

    for i, owner in enumerate(state["spot_owners"]):
        if "💰" in owner:
            allPaid = True
        elif "💰" not in owner:
            allPaid = False
            break
    if allPaid == True:
        await ctx.send("✅ Everyone has paid, Razz will be ran soon.")

    if updated:
        await update_spots_message(state)
        save_state()
    else:
        await ctx.send("❌ You haven't claimed any spots to mark as paid.")

@bot.command()
@commands.has_role("Trusted Seller")
async def stop(ctx):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There's no active raffle in this channel.")
        return

    state["active"] = False
    await ctx.send("🛑 The raffle has been stopped. It is now locked and visible, but cannot be edited. Use `!start` to begin a new one.")
    save_state()

@bot.command()
async def remaining(ctx):

    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]


    notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]

    remaining_numbers = []

    for i, owner in enumerate(spot_owners):
        j = i + 1
        if owner is None:
            remaining_numbers.append(j)
        else:
            pass

    remaining_text = ', '.join(map(str, remaining_numbers))

    await ctx.send(
        f"**{len(remaining_numbers)}** spots remaining\n\n"
        f"Spots:"
    )

    for chunk in [remaining_text[i:i + 2000] for i in range(0, len(remaining_text), 2000)]:
        await ctx.send(chunk)


@commands.has_role("Trusted Seller")
@bot.command()
async def payment(ctx):
    state = channel_states.get(ctx.channel.id)
    if not state or not state.get("active"):
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]
    rev = state["revolut"]


    not_paid = {}

    for i, owner in enumerate(spot_owners):
        if owner is not None and "💰" not in owner:
            not_paid.setdefault(owner, []).append(i + 1)

    if len(not_paid) == 0:
        await ctx.send("✅ Everyone has paid!")
        return

    for owner, spots in not_paid.items():
        amount = price_per_spot * len(spots)
        await ctx.send(f"{owner} has to pay. Amount to pay: €{amount:.2f}")
    if 'gmail' in rev:
        await ctx.send("\u200b\n\n\n")
        await ctx.send(f"**Paypal:** {rev}")
    else:
        await ctx.send("\u200b\n\n\n")
        await ctx.send(f"**Revolut:** {rev}")

@bot.command()
async def myspots(ctx):
    state = channel_states.get(ctx.channel.id)
    if state is None:
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    spot_owners = state["spot_owners"]
    total_spots = state["total_spots"]
    price_per_spot = state["price_per_spot"]

    state = channel_states.get(ctx.channel.id)
    if state is None:
        await ctx.send("❌ There is no active raffle in this channel.")
        return

    if not any(owner and ctx.author.mention in owner for owner in spot_owners):
        await ctx.send("❌ You do not currently own spots in this razz.")
        return

    channelTag = ctx.channel.id

    spotOwned = []
    miniOwned = []
    countSpot = 0
    countMini = 0

    for i, owner in enumerate(spot_owners):
        if not owner:
            continue

        owner_str = str(owner) if owner is not None else ""

        if owner_str == ctx.author.mention:
            j = 1 + i
            spotOwned.append(j)
            countSpot += 1
        elif "Mini" in owner_str and ctx.author.mention in owner_str:
            j = 1 + i
            miniOwned.append(j)
            countMini += 1
        elif "💰" in owner_str and ctx.author.mention in owner_str and "Mini" not in owner_str:
            j = 1 + i
            spotOwned.append(j)
            countSpot += 1

    try:
        await ctx.author.send(
            f"\u200b\n\n\n**Spots for razz in** <#{channelTag}> \n\n **You own spots:** {', '.join(map(str, spotOwned))} \n \n **Total Spots:** {countSpot} \n \n **Mini Spots:** {', '.join(map(str, miniOwned))} \n \n **Total Mini spots:** {countMini}")
        await ctx.message.add_reaction("📩")
    except discord.Forbidden:
        await ctx.send(f"❌ I couldn't DM you, {ctx.author.mention}. Content & Social > Social Permissions > Allow DM's from other members in this server.")
        return


@bot.command()
async def razz(ctx):
    state = channel_states.get(ctx.channel.id)

    keyword = "✅ Raffling "

    async for message in ctx.channel.history(limit=600):
        if keyword in message.content:
            await ctx.send(f"Current Razz: {message.jump_url}")
            return
    await ctx.send("❌ There is no active raffle in this channel.")

@bot.command()
async def pause(ctx):
    state = channel_states.get(ctx.channel.id)
    paused = state["paused"]

    state["paused"] = True
    await ctx.send("⚠️ Main is closed. Last spots are in Mini.")
    await ctx.message.add_reaction("⏸️")


@bot.command()
async def unpause(ctx):
    state = channel_states.get(ctx.channel.id)
    paused = state["paused"]

    state["paused"] = False

    await ctx.send("🤖 Razz has been unpaused.")
    await ctx.message.add_reaction("▶️")

@bot.command()
async def rev(ctx):
    state = channel_states.get(ctx.channel.id)
    rev = state["revolut"]

    if 'gmail' in rev:
        await ctx.send(f"**Paypal:** {rev}")
    else:
        await ctx.send(f"**Revolut:** {rev}")



@payment.error
async def payment_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("🚫 You need the 'Trusted Seller' role to use this command.")

@start.error
async def start_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("🚫 You need the 'Trusted Seller' role to use this command.")


async def update_spots_message(state):
    spots_per_message = 50
    spot_owners = state["spot_owners"]
    messages = state["spots_messages"]


    content_chunks = []
    notFilled = [i + 1 for i, owner in enumerate(spot_owners) if owner is None]



    for start in range(0, len(spot_owners), spots_per_message):
        chunk = ""

        for i in range(start, min(start + spots_per_message, len(spot_owners))):

            owner = spot_owners[i]
            chunk += f"{i + 1}. {owner or '—'}\n"

        content_chunks.append(chunk)

    for i, chunk in enumerate(content_chunks):
        if i < len(messages):
            await messages[i].edit(content=chunk)
        else:
            msg = await messages[0].channel.send(chunk)
            messages.append(msg)

    while len(messages) > len(content_chunks):
        msg_to_delete = messages.pop()
        await msg_to_delete.delete()


    state["spots_messages"] = messages

# Run the bot
bot.run(token)
