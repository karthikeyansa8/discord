import time
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord import app_commands
from discord.ui import Button, View,Modal,TextInput,Select
import requests
import testcreate
import db_con
import api_testing
from password_handler import password_generator
import datetime
import asyncio
import logging
from image_comparison_bot import ImageComparison

import os

# https://guide.pycord.dev/interactions/ui-components/dropdowns

load_dotenv()

#DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

DISCORD_BOT_TOKEN =  "MTI5Njc5MDg2MTc2NTQxNDk0Mg.GjqOVM.MOurvhQFdIn9Odnv51r286X61Jwd_gpYddx7k0"   #For testing purpose (LB PYTHON TESTING TOKEN)

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable message content intent
intents.message_content = True  # Enable message content intent



# Create a bot instance with a command prefix
# bot = commands.Bot(command_prefix='/',intents = intents)

bot = commands.Bot(command_prefix='/', intents=intents)


# Dictionary to store events {date: {school_name: {description: (student_count, class_count)}}}
events = {}

# Dictionary to track total students per school on each date
total_students_per_school = {}

@bot.event
async def on_ready():
    
    synced = await bot.tree.sync()  
    print(synced)
    print(len(synced))
    print(f'We have logged in as {bot.user}')
    
    channel_id = 1281499626742222870  # Example Channel ID
    channel = bot.get_channel(channel_id)
    
    if channel:
        await channel.send("Hello! I'm ready and online new.")
        await channel.send("You can create, update or delete an event!")
    
    else:
        print("Channel not found.")

    await bot.tree.sync()
    print("Commands synced.")
    
    
    
    

@bot.tree.command(name='createevent')
@app_commands.describe(event_date="Date of the event (YYYY-MM-DD)", description="Event description", school_name="Name of the school", student_count="Approximate number of students", class_count="Number of classes")
async def create_event(interaction: discord.Interaction, event_date: str, description: str, school_name: str, student_count: int, class_count: int):
    """Create a new event or update an existing event."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    today = datetime.date.today()

    if date_obj < today:
        await interaction.response.send_message("Cannot create an event in the past.", ephemeral=True)
        return
    
    if (date_obj - today).days < 7:
        await interaction.response.send_message("Events can only be created up to 7 days in advance.", ephemeral=True)
        return
    
    
    if date_obj.weekday() == 6:  # Sunday is 6
        await interaction.response.send_message("Alert: Events cannot be created on Sundays.", ephemeral=True)
        return

    # Check the total student count for the day before adding the event
    if date_obj not in total_students_per_school:
        total_students_per_school[date_obj] = {}
    if school_name not in total_students_per_school[date_obj]:
        total_students_per_school[date_obj][school_name] = 0
    
    total_students_today = sum(total_students_per_school[date_obj].values()) + student_count

    if total_students_today > 320:
        await interaction.response.send_message(f"Total students for {event_date} would exceed 320. Event not created. Please decide whether to postpone or prepone the event.", ephemeral=True)
        return

    # Proceed to add the event since it does not exceed the limit
    if date_obj not in events:
        events[date_obj] = {}
    if school_name not in events[date_obj]:
        events[date_obj][school_name] = {}

    # Add the event and student/class counts
    events[date_obj][school_name][description] = (student_count, class_count)

    # Update total student count for the school
    total_students_per_school[date_obj][school_name] += student_count

    await interaction.response.send_message(f"Event created for {event_date}: {description} at {school_name} with {student_count} students and {class_count} classes.", ephemeral=True)


@bot.tree.command(name='updateevent')
@app_commands.describe(event_date="Date of the event (YYYY-MM-DD)", school_name="Name of the school", description="Event description", new_description="New description for the event", new_student_count="New student count", new_class_count="New class count")
async def update_event(interaction: discord.Interaction, event_date: str, school_name: str, description: str, new_description: str, new_student_count: int, new_class_count: int):
    """Update an existing event."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return
    
    if date_obj.weekday() == 6:  # Sunday is 6
        await interaction.response.send_message("Alert: Events cannot be updated on Sundays.", ephemeral=True)
        return

    if date_obj in events and school_name in events[date_obj] and description in events[date_obj][school_name]:
        # Retrieve the current student count and class count
        current_student_count, current_class_count = events[date_obj][school_name][description]

        # Remove the old event entry
        events[date_obj][school_name].pop(description)
        if not events[date_obj][school_name]:  # Remove the school if no events left
            del events[date_obj][school_name]

        # Decrease the student count for the school
        total_students_per_school[date_obj][school_name] -= current_student_count

        # Add the new event details
        if date_obj not in events:
            events[date_obj] = {}
        if school_name not in events[date_obj]:
            events[date_obj][school_name] = {}
        events[date_obj][school_name][new_description] = (new_student_count, new_class_count)

        # Update total student count for the date
        total_students_per_school[date_obj][school_name] += new_student_count

        # Check the total student count for the day
        total_students_today = sum(total_students_per_school[date_obj].values())
        if total_students_today > 320:
            await interaction.response.send_message(f"Total students for {event_date} exceed 320. Please decide whether to postpone or prepone the event.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Event updated on {event_date} for {school_name}: '{description}' changed to '{new_description}' with {new_student_count} students and {new_class_count} classes.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date} for {school_name} with description '{description}'.", ephemeral=True)


@bot.tree.command(name='preponeevent')
@app_commands.describe(event_date="Current date of the event (YYYY-MM-DD)", new_date="New date to prepone the event (YYYY-MM-DD)", school_name="Name of the school", description="Event description")
async def prepone_event(interaction: discord.Interaction, event_date: str, new_date: str, school_name: str, description: str):
    """Prepone an event to a new date."""
    try:
        old_date = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
        new_date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if new_date_obj.weekday() == 6:  # Sunday is 6
        await interaction.response.send_message("Alert: Events cannot be preponded on Sundays.", ephemeral=True)
        return

    if old_date in events and school_name in events[old_date] and description in events[old_date][school_name]:
        student_count, class_count = events[old_date][school_name].pop(description)
        if not events[old_date][school_name]:
            del events[old_date][school_name]  # Remove the school if no events left
        # Decrease the student count for the school
        total_students_per_school[old_date][school_name] -= student_count
        
        # Add to new date
        if new_date_obj not in events:
            events[new_date_obj] = {}
        if school_name not in events[new_date_obj]:
            events[new_date_obj][school_name] = {}
        events[new_date_obj][school_name][description] = (student_count, class_count)

        # Update total student count for the new date
        if new_date_obj not in total_students_per_school:
            total_students_per_school[new_date_obj] = {}
        if school_name not in total_students_per_school[new_date_obj]:
            total_students_per_school[new_date_obj][school_name] = 0
        total_students_per_school[new_date_obj][school_name] += student_count

        # Check the total student count for the new day
        total_students_today = sum(total_students_per_school[new_date_obj].values())
        if total_students_today > 320:
            await interaction.response.send_message(f"Total students for {new_date} exceed 320. Please decide whether to postpone or prepone the event.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Event prepone from {event_date} to {new_date} for {school_name} with {student_count} students and {class_count} classes.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date} for {school_name} with description '{description}'.", ephemeral=True)

@bot.tree.command(name='postponeevent')
@app_commands.describe(event_date="Current date of the event (YYYY-MM-DD)", new_date="New date to postpone the event (YYYY-MM-DD)", school_name="Name of the school", description="Event description")
async def postpone_event(interaction: discord.Interaction, event_date: str, new_date: str, school_name: str, description: str):
    """Postpone an event to a new date."""
    try:
        old_date = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
        new_date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if new_date_obj.weekday() == 6:  # Sunday is 6
        await interaction.response.send_message("Alert: Events cannot be postponed on Sundays.", ephemeral=True)
        return

    if old_date in events and school_name in events[old_date] and description in events[old_date][school_name]:
        student_count, class_count = events[old_date][school_name].pop(description)
        if not events[old_date][school_name]:
            del events[old_date][school_name]  # Remove the school if no events left
        # Decrease the student count for the school
        total_students_per_school[old_date][school_name] -= student_count

        # Add to new date
        if new_date_obj not in events:
            events[new_date_obj] = {}
        if school_name not in events[new_date_obj]:
            events[new_date_obj][school_name] = {}
        events[new_date_obj][school_name][description] = (student_count, class_count)

        # Update total student count for the new date
        if new_date_obj not in total_students_per_school:
            total_students_per_school[new_date_obj] = {}
        if school_name not in total_students_per_school[new_date_obj]:
            total_students_per_school[new_date_obj][school_name] = 0
        total_students_per_school[new_date_obj][school_name] += student_count

        # Check the total student count for the new day
        total_students_today = sum(total_students_per_school[new_date_obj].values())
        if total_students_today > 320:
            await interaction.response.send_message(f"Total students for {new_date} exceed 320. Please decide whether to postpone or prepone the event.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Event postponed from {event_date} to {new_date} for {school_name} with {student_count} students and {class_count} classes.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date} for {school_name} with description '{description}'.", ephemeral=True)


@bot.tree.command(name='checkevent')
@app_commands.describe(event_date="Date of the event (YYYY-MM-DD)")
async def check_event(interaction: discord.Interaction, event_date: str):
    """Check events for a given date."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if date_obj in events:
        response = f"Events on {event_date}:\n"
        for school, descriptions in events[date_obj].items():
            for description, (student_count, class_count) in descriptions.items():
                response += f"- {school}: '{description}' with {student_count} students and {class_count} classes\n"
        await interaction.response.send_message(response, ephemeral=True)
    else:
        await interaction.response.send_message(f"No events found on {event_date}.", ephemeral=True)


@bot.tree.command(name='deleteevent')
@app_commands.describe(event_date="Date of the event (YYYY-MM-DD)", school_name="Name of the school", description="Event description")
async def delete_event(interaction: discord.Interaction, event_date: str, school_name: str, description: str):
    """Delete an event."""
    try:
        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return

    if date_obj in events and school_name in events[date_obj] and description in events[date_obj][school_name]:
        student_count, class_count = events[date_obj][school_name].pop(description)
        if not events[date_obj][school_name]:
            del events[date_obj][school_name]  # Remove the school if no events left
        # Decrease the student count for the school
        total_students_per_school[date_obj][school_name] -= student_count
        
        await interaction.response.send_message(f"Event deleted on {event_date} for {school_name} with description '{description}'.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No event found on {event_date} for {school_name} with description '{description}'.", ephemeral=True)














class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.button(label="Release Schedule!", row=1,style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def button_callback(self, interaction,button):
        await interaction.response.send_message("Release Schedule") # Send a message when the button is clicked
        
    @discord.ui.button(label="Lapis Schedule",row=2, style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def button_callback(self, interaction,button):
        await interaction.response.send_message("Lapis Schedule") # Send a message when the button is clicked


class BugReport(Modal, title='bug Report'):
    options = [
        discord.SelectOption(label="Learnyst", value="LY"),
        discord.SelectOption(label="HUB", value="HUB"),
        discord.SelectOption(label="Other", value="other")
    ]
    
    # bug_type_select = discord.ui.Select(placeholder="Select Bug Type", options=options,row=1)
    name = TextInput(label='What Issue are you facing')
    answer = TextInput(label='Can You describe the issue', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        # selected_bug_type = self.bug_type_select.values[0]
        await interaction.response.send_message(f'Thanks for your response! You reported a :\n\nIssue: {self.name.value}\nDescription: {self.answer.value}', ephemeral=True)

class MyViewSelect(discord.ui.View):
    @discord.ui.select( # the decorastor that lets you specify the properties of the select menu
        placeholder = "Choose The Topic!", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Test Releases",
                description="Check Which test have to be released today",value="TR"
            ),
            discord.SelectOption(
                label="Worksheet",
                description="Check Which worksheet need to be delivered.",value="PWS"
            ),
            discord.SelectOption(
                label="School Visits",
                description="Check Upcoming Visits to schools.",value="SCV"
            )
        ]
    )
    async def select_callback(self,interaction,select): # the function called when the user is done selecting options
        
        selected_value = select.values[0]

               
        # Call a specific function based on the selected option
        if selected_value == "TR":
            await self.test_release_for_today(interaction)
        elif selected_value == "PWS":
            await self.worksheet_for_today(interaction)
        elif selected_value == "SCV":
            await self.school_visit_this_week(interaction)
        else:
            await interaction.response.send_message(f"You selected {selected_value}")

    async def worksheet_for_today(self, interaction):
        
        items = ["PVA 7A - ", "Item 2", "Item 3"]

        # Create an embed
        embed = discord.Embed(title="Todays Test Release", color=discord.Color.blue())

        # Add items to the embed
        for index, item in enumerate(items, start=1):
            embed.add_field(name=f"{item}", value=item, inline=False)

        await interaction.response.send_message(embed=embed)
        # await interaction.response.send_message("You selected Vanilla!")

    async def test_release_for_today(self, interaction):
        await interaction.response.send_message("Click the button below to create test.", view=testcreate.TestReleaseView())

    async def school_visit_this_week(self, interaction):
        await interaction.response.send_message("You selected Strawberry!")


@bot.tree.command(name='upcomingevents')
async def interactive_hello(interaction:discord.Interaction):
    """Get The list of upcoming task to be done."""
    
    await interaction.response.send_message("What Can I help You with", view=MyViewSelect(),ephemeral=True)


@bot.tree.command(name='reportperformance')
async def report_server_status(interaction:discord.Interaction):
    """Report Performance"""
    response,execution_time = api_testing.daily_report_performance()
    
    await interaction.response.send_message(f"Daily Report Generated in {round(execution_time,2)} seconds.",ephemeral=True)
    
@bot.tree.command(name='upcomingeventsnew')
async def interactive_hello(interaction:discord.Interaction):
    """Report A bug."""
    
    await interaction.response.send_message("What Can I help You with", view=MyViewSelect(),ephemeral=True,)


@bot.tree.command(name='bugreport')
async def bug_report_function(interaction:discord.Interaction):
# async def bug_report_function(ctx):
    """Report A Bug."""
    
    await interaction.response.send_modal(BugReport())
    ''

@bot.tree.command(name='getuserpasswordbysection')
@app_commands.describe(school_acronym = "Enteer School Name or acronym",std= "Enter Class Name",section="Enter Section Name")
async def get_user_password_for_section(interaction:discord.Interaction,school_acronym:str,std:int,section:str):

    file_name = f'student_password_{school_acronym}_{std}_{section}.csv'
    
    list_of_Student_df = db_con.get_student_password_by_school_name_class_section(school_name=school_acronym,class_name=std,section_name=section)
    
    list_of_Student_df.to_csv(file_name)
    
    if list_of_Student_df.empty:
        await interaction.response.send_message("No Students found")    
    
    message_to_be_sent = ''
    
    for index,row in list_of_Student_df.iterrows():
        message_to_be_sent += f"Roll Number - {row['roll_number']}, Name - {row['student_name']}, Password - {row['ly_password']}\n"
        

        if index % 20 == 0 and index != 0:
            print(message_to_be_sent)
            
            await interaction.channel.send(message_to_be_sent)
            
            
            time.sleep(1)
            
            message_to_be_sent = ''
        
    await interaction.channel.send(message_to_be_sent)
    
    await interaction.channel.send(file=discord.File(file_name))
    
    os.remove(file_name)

@bot.tree.command(name='getuserpassword')
@app_commands.describe(username = "User Roll Number,Name or email")
async def get_user_password_based_on_username_name_email_or_phone_number(interaction:discord.Interaction,username:str):

    list_of_Student = db_con.get_student_password_by_username_nad_name_from_db(username=username)
    
    
    if list_of_Student == 0:
        await interaction.response.send_message("No Students found")    
        
    embed = discord.Embed(title="Matching Students", color=discord.Color.blue())

    # Add items to the embed
    for index, item in enumerate(list_of_Student, start=1):
        embed.add_field(name=item['final_string'], value=f"Password - {item['ly_password']}", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='resetuserpassword')
@app_commands.describe(roll_number = "User Roll Number")
async def reset_ly_password(interaction:discord.Interaction,roll_number:str):

    
    student_is_present,ly_learner_id = db_con.check_student_present(roll_number=roll_number)
    
    print(student_is_present,ly_learner_id)

    if student_is_present == True:
        
        new_password = password_generator()
        
        url = "https://api.learnbasics.fun/learnyst/user/password/reset/"

        payload = {
            "ly_learner_id":ly_learner_id,
            "new_password":str(new_password)
        }

        response = requests.post(url=url,json=payload)

        print(response.content)

        db_con.excute_query(query="UPDATE school_data.student_detail SET ly_password = %(ly_password)s WHERE roll_number = %(roll_number)s",vars={
            "roll_number":roll_number.upper(),
            "ly_password":new_password
        })


        embed = discord.Embed(title=f"New Password for {roll_number}", color=discord.Color.blue())
        embed.add_field(name="Password", value=new_password, inline=False)

    else:
        embed = discord.Embed(title=f"No Student Found", color=discord.Color.red())
        embed.add_field(name="Error", value=f"No Student found with roll number {roll_number}", inline=False)
        

    await interaction.response.send_message(embed=embed)


    
@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Latency in milliseconds
    await ctx.send(f'Pong! Latency: {latency}ms \nUser ID: {ctx.author.id} \nChannel ID: {ctx.channel.id}\nGuild: {ctx.guild.id}')


# @bot.command(name='help') 
@bot.command(name='suggest') 
async def suggest(ctx, *, query = None):
    """
    Suggest a command based on the input query.
    Usage: !suggest <query>
    """
    command_names = [command.name for command in bot.commands]

    if query == None:
        
        suggestions = [name for name in command_names]
    else:
        suggestions = [name for name in command_names if query.lower() in name.lower()]
    
    if suggestions:
        response = f"Did you mean: {', '.join(suggestions)}?"
    else:
        response = "No suggestions found."

    await ctx.send(response)


@bot.tree.command(name='getstudentpwsquestions')
@app_commands.describe(roll_number = "User Roll Number",school_chapter_id = "School Chapter ID")
async def get_student_question_based_pws_bot(interaction:discord.Interaction,roll_number:str,school_chapter_id:int):

    student_questions = db_con.get_student_questions_in_worksheet(roll_number=roll_number,school_chapter_id=school_chapter_id)
    
    
    await interaction.response.send_message(student_questions)    


@bot.tree.command(name='getsampleworksheet')
@app_commands.describe(base_chapter="Enter Base Chapter")
async def get_full_pws_bot(interaction: discord.Interaction, base_chapter: str):

    print(base_chapter)

    await interaction.response.defer()

    url = "http://server.learnbasics.fun:4301/pws/worksheet/"
    payload = {
        "chaptag": base_chapter
    }


    try:
        # Asynchronous POST request
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Failed to fetch data from the server.")
                    return

                data = await resp.json()

        file_url = data.get('url')
        if not file_url:
            await interaction.followup.send("No file URL found in the response.")
            return

        # Asynchronous GET request to fetch the PDF
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as file_resp:
                if file_resp.status != 200:
                    await interaction.followup.send("Failed to download the file.")
                    return

                file_content = await file_resp.read()

        # Save the PDF file locally
        file_path = f"{base_chapter}.pdf"

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Send the file in the response
        await interaction.followup.send(file=discord.File(file_path))

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")





# This part for the image compare bot


intents = discord.Intents.default()

intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

channel_id = 1296792053052870743  # ---->  Replace with your channel id

@bot.event
async def on_ready():
    
    logging.info(f'{bot.user} has connected to Discord!')
    
    print(f'{bot.user} has connected to Discord!')

    channel = bot.get_channel(channel_id)
    
    if channel:
        await channel.send("Hey! I'm here to compare your images...")

# Register the slash command
@bot.tree.command(name="imagecompare", description="Compare uploaded images")
async def image_compare(interaction: discord.Interaction):
    
    await interaction.response.send_message("Please upload TWO or more images you want to compare.")
    logging.info("Waiting for user to upload images for comparison.")

    def check(message):
        return (
            message.author == interaction.user and
            message.channel == interaction.channel and
            len(message.attachments) > 0
        )

    try:
        while True:
            # Wait for message with image attachments
            message = await bot.wait_for("message", timeout=60.0, check=check)
            
            # Check if the user uploaded fewer than 2 images
            if len(message.attachments) < 2:
                await interaction.followup.send("Please upload two or more images to compare.")
                continue  # Repeat the loop until they upload at least 2 images

            # If two or more images are uploaded, proceed with processing
            comparison = ImageComparison()
            
            logging.info("Image comparison process started...")
            
            await comparison.fetch_images_from_discord(channel_id)
            
            logging.info("Image comparison completed and results sent to Discord.")
            await interaction.followup.send("Image comparison completed.")
            
            print("Image comparison completed.")
            break  # Exit the loop once processing is done

    except asyncio.TimeoutError:
        await interaction.followup.send("Image comparison request timed out. Please try again.")


print(DISCORD_BOT_TOKEN)
bot.run(DISCORD_BOT_TOKEN)

