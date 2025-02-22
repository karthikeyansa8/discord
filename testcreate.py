import discord


class TestReleaseView(discord.ui.View):
    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Choose The Test To Create!", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 3, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="PVA 7A - Knoing Number - HQ4",
                description="Question Selected C7M01 - Q1 ,Q5",value="HQ4"
            ),
            discord.SelectOption(
                label="PVA 7B - Knoing Number - HQ5",
                description="Question Selected C7M01 - Q1 ,Q5",value="HQ6"
            ),
            discord.SelectOption(
                label="PVA 7A - Knoing Number - HQ6",
                description="Question Selected C7M01 - Q1 ,Q7",value="HQ7"
            ),
        ]
    )
    async def select_callback(self,interaction,select): # the function called when the user is done selecting options
        
        selected_values = select.values

        messages_to_send = []
        for each_selected_value in selected_values:
            messages_to_send.append(f"Test Created {each_selected_value}")
            
        await interaction.response.send_message("\n\n".join(messages_to_send))
               
        # # Call a specific function based on the selected option
        # if selected_value == "TR":
        #     await self.test_release_for_today(interaction)
        # elif selected_value == "PWS":
        #     await self.worksheet_for_today(interaction)
        # elif selected_value == "SCV":
        #     await self.school_visit_this_week(interaction)
        # else:
        #     await interaction.response.send_message(f"You selected {selected_value}")

    async def test_release_for_today(self, interaction):
        items = ["PVA 7A - ", "Item 2", "Item 3"]

        # Create an embed
        embed = discord.Embed(title="Todays Test Release", color=discord.Color.blue())

        # Add items to the embed
        for index, item in enumerate(items, start=1):
            embed.add_field(name=f"Item {index}", value=item, inline=False)

        await interaction.response.send_message(embed=embed)
        # await interaction.response.send_message("You selected Vanilla!")

    async def worksheet_for_today(self, interaction):
        await interaction.response.send_message("You selected Chocolate!")

    async def school_visit_this_week(self, interaction):
        await interaction.response.send_message("You selected Strawberry!")
