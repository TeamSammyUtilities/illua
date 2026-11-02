import discord

class Paginator(discord.ui.View):
    def __init__(self, pages: list[discord.Embed]):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= len(self.pages) - 1

    def get_embed(self):
        return self.pages[self.current_page]

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        emoji="◀"
    )
    async def previous(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.current_page -= 1
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        emoji="▶"
    )
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.current_page += 1
        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )