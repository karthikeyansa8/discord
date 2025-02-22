import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

# Load Discord bot token from environment variable
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Alternatively, you can hardcode the token (not recommended for production)
DISCORD_BOT_TOKEN = "MTIxNzAwNzgwNzk3NTM5NTM2OA.GCl_sU.vUpu3kprE4E7MLmXx8Fs8WEJEDYTE1KxpMWjlg"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable message content intent
intents.message_content = True  # Enable message content intent


bot = commands.Bot(command_prefix='/', intents=intents)


# Dictionary to store events {date: event_description}
events = {}

@bot.event
async def on_ready():

    print(f'We have logged in as {bot.user}')
    channel = bot.get_channel(1281499626742222870)  
    await channel.send("Bot has logged in and is ready!")
    await channel.send("You can create, update or delete an event!")

    await bot.tree.sync()
    print("Commands synced.")


@bot.tree.command(name='createevent')
@app_commands.describe(event_date="Date of the event (YYYY-MM-DD)", description="Event description")
async def create_event(interaction: discord.Interaction, event_date: str, description: str):
    """Create a new event or update an existing event."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if date_obj in events:
        await interaction.response.send_message(f"An event already exists on {event_date}: {events[date_obj]}.\nWould you like to postpone or prepone the event?", ephemeral=True)
    else:
        events[date_obj] = description
        await interaction.response.send_message(f"Event created for {event_date}: {description}.", ephemeral=True)


# Command to postpone an existing event
@bot.tree.command(name='postponeevent')
@app_commands.describe(event_date="Current date of the event (YYYY-MM-DD)", new_date="New date to postpone the event (YYYY-MM-DD)")
async def postpone_event(interaction: discord.Interaction, event_date: str, new_date: str):
    """Postpone an event to a new date."""
    try:
        old_date = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
        new_date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if old_date in events:
        event_desc = events.pop(old_date)
        events[new_date_obj] = event_desc
        await interaction.response.send_message(f"Event postponed from {event_date} to {new_date}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date}.", ephemeral=True)


# Command to prepone an existing event
@bot.tree.command(name='preponeevent')
@app_commands.describe(event_date="Current date of the event (YYYY-MM-DD)", new_date="New date to prepone the event (YYYY-MM-DD)")
async def prepone_event(interaction: discord.Interaction, event_date: str, new_date: str):
    """Prepone an event to an earlier date."""
    try:
        old_date = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
        new_date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if old_date in events:
        event_desc = events.pop(old_date)
        events[new_date_obj] = event_desc
        await interaction.response.send_message(f"Event preponed from {event_date} to {new_date}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date}.", ephemeral=True)


# Command to delete an event
@bot.tree.command(name='deleteevent')
@app_commands.describe(event_date="Date of the event to delete (YYYY-MM-DD)")
async def delete_event(interaction: discord.Interaction, event_date: str):
    """Delete an event."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if date_obj in events:
        events.pop(date_obj)
        await interaction.response.send_message(f"Event on {event_date} deleted.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date}.", ephemeral=True)


# Command to check events on a specific date
@bot.tree.command(name='checkevent')
@app_commands.describe(event_date="Date to check for events (YYYY-MM-DD)")
async def check_event(interaction: discord.Interaction, event_date: str):
    """Check if an event exists on a specific date."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if date_obj in events:
        await interaction.response.send_message(f"Event on {event_date}: {events[date_obj]}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date}.", ephemeral=True)


# Run the bot


print(DISCORD_BOT_TOKEN)
bot.run(DISCORD_BOT_TOKEN)