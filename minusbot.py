import discord
from discord.ext import commands
from discord import app_commands
from requests import RequestException
import logging
from dotenv import load_dotenv
import os
import aiohttp
import asyncio
from scraper import scrape_movies
import datetime
from scraper import Movie
import random
from custom_exceptions import AccessDeniedError, NotFoundError

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
discord_guild_key = os.getenv("DISCORD_GUILD_KEY")
w2g_api_key = os.getenv("WATCH2GETHER_API_KEY")
w2g_room_id = os.getenv("WATCH2GETHER_ROOM_ID")

guild_id = discord.Object(id=discord_guild_key)

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        try:
            guild = discord.Object(id=discord_guild_key)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")
        except Exception as e:
            print(f"Error syncing commands: {e}")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

page_size = 2
current_page_index = 0
movies: list[Movie] = []
w2g_room_url = f"https://w2g.tv/en/room/?r={w2g_room_id}"

flixhq_base_url = "https://flixhq.one"
lookmovie2_base_url = "https://lookmovie2.to"

no_movies_found_strings = ["Inga filmer hittades.", "Här var det tomt...", "Ska vi kolla i arkivet också?"]
movies_found_strings = ["Här fanns det filmer!", "Bra val!", "Är ni säkra på den här?", "Ska Dias vara med och kolla film också?", "Har inte du redan sett den här Davve?", "Robin har sett ALLA de här 10+ gånger..."]
end_of_list_strings = ["Här var det slut på det roliga...", "Slut på filmer!", "Letade ni verkligen så här långt?", "Grabbarna gräver efter guld..."]
play_start_strings = ["Join the party!", "Dags att poppa popcorn!", "MAMMA DET BÖRJAR NU!", "Nu kör vi!", "Baller!"]
chosen_movie_card_id = ""

async def handle_play_to_w2g(interaction: discord.Interaction, link: str, message: discord.View):
    try: 
        await play_to_w2g(link)
        await interaction.followup.send(view=message)
    except NotFoundError:
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.red(), f"## 404: Not found", footer="Kolla W2G URL."))
    except AccessDeniedError:
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.red(), f"## 403: Forbidden", footer="Kolla W2G API-key och W2G room ID."))
    except RequestException:
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.red(), f"## Ett oväntat fel har inträffat", footer="Shit happens I guess lmao"))

async def play_to_w2g(link: str):
    url = f"https://api.w2g.tv/rooms/{w2g_room_id}/sync_update"

    payload = {
        "w2g_api_key": w2g_api_key,
        "item_url": link
    }

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return
            elif response.status == 404:
                raise NotFoundError
            elif response.status == 403:
                raise AccessDeniedError
            else:
                raise RequestException

@client.tree.command(name="play", description="Tar en media-länk startar den i Sällskapsbion", guild=guild_id)
@app_commands.describe(media="Länk till media")
async def play_media(interaction: discord.Interaction, media: str):
    await interaction.response.defer()
    await handle_play_to_w2g(interaction, media, SimpleTextLayout(discord.Color.blurple(), f"# {random.choice(play_start_strings)}", w2g_room_url))

class MovieLayout(discord.ui.LayoutView):
    def __init__(self, movie: Movie, play_button: PlayButton):
        super().__init__()

        container = discord.ui.Container(accent_color=discord.Color.blurple() if movie.quality == "HD" or movie.quality == "FHD" else discord.Color.red())
        container.add_item(discord.ui.TextDisplay(f"# ***{movie.title}***"))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(discord.ui.TextDisplay(f"### Released:\n {movie.release_year}"))
        container.add_item(discord.ui.TextDisplay(f"### Quality:\n {movie.quality}"))
        container.add_item(discord.ui.TextDisplay(f"### Runtime:\n {movie.runtime}" if movie.runtime else f"### Rating:\n {movie.rating}/10"))
        
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media=movie.poster_url)
        container.add_item(gallery)
    
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        line = discord.ui.ActionRow()
        line.add_item(play_button)
        container.add_item(line)

        self.add_item(container)

class SimpleTextLayout(discord.ui.LayoutView):
    def __init__(self, color: discord.Color, *args: str, footer: str = None):
        super().__init__()
        container = discord.ui.Container(accent_color=color)
        for index, text in enumerate(args, 0):
            if len(args) > 1 and index != len(args) - 1:
                container.add_item(discord.ui.TextDisplay(text))
                container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            else:
                container.add_item(discord.ui.TextDisplay(text))
        if footer != None:
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(discord.ui.TextDisplay(f"-# {footer}"))
        self.add_item(container)

class ButtonBox(discord.ui.LayoutView):
    def __init__(self, *args: discord.ui.Button, label: str = None):
        super().__init__()

        container = discord.ui.Container(accent_color=discord.Color.blurple())

        if label != None:
            container.add_item(discord.ui.TextDisplay(f"## {label}"))
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        line = discord.ui.ActionRow()
        for button in args:
            line.add_item(button)
        
        container.add_item(line)

        self.add_item(container)

class PlayButton(discord.ui.Button):
    def __init__(self, movie_title: str, movie_url: str):
        super().__init__(
            label="▶️",
            style=discord.ButtonStyle.primary,
            custom_id=f"play_button_{movie_title}"
        )
        self.movie_title = movie_title
        self.movie_url = movie_url

    async def callback(self, interaction: discord.Interaction):
        global chosen_movie_card_id
        chosen_movie_card_id = interaction.message.id
        await interaction.response.defer()
        self.label = "✔️"
        self.style = discord.ButtonStyle.success
        self.disabled = True
        await interaction.edit_original_response(view=self.view)
        await clear_movie_options(interaction=interaction)
        await handle_play_to_w2g(interaction, self.movie_url, SimpleTextLayout(discord.Color.blurple(), f"# ***{self.movie_title}***\nspelas nu upp!", w2g_room_url, footer=f"Ikväll är det {interaction.user.mention} som styr upp."))

class ClearButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="clear_button"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await clear_movie_options(interaction=interaction)

class PaginationButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label=f"⬇️",
            style=discord.ButtonStyle.primary,
            custom_id="pagination_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        global current_page_index, page_size
        current_page_index += page_size
        await interaction.message.delete()
        await pagination(interaction, current_page_index)

@client.tree.command(name="search", description="Sök efter filmer på FlixHQ eller Lookmovie", guild=guild_id)
@app_commands.describe(titel="Titel på film att söka efter")
@app_commands.choices(streaming_service=[
    app_commands.Choice(name="FlixHQ", value="FlixHQ"),
    app_commands.Choice(name="Lookmovie2", value="Lookmovie2")
])
async def search_movie(interaction: discord.Interaction, titel: str, streaming_service: app_commands.Choice[str]):
    await interaction.response.defer()
    global flixhq_base_url
    global lookmovie2_base_url
    base_url = flixhq_base_url if streaming_service.value == "FlixHQ" else lookmovie2_base_url
    global chosen_movie_card_id
    chosen_movie_card_id = ""
    global movies
    if movies:
        movies.clear()
    try:
        movies = scrape_movies(titel, base_url, streaming_service=streaming_service.name)
        if not movies:
            await interaction.followup.send(view=SimpleTextLayout(discord.Color.red(), f"### {random.choice(no_movies_found_strings)}"))
        else:
            await interaction.followup.send(view=SimpleTextLayout(discord.Color.blurple(), f"## {random.choice(movies_found_strings)}", f"Visar resultat för '{titel}' på {streaming_service.value}"))
            await pagination(interaction, 0)
    except RequestException as e:
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.red(), f"## Anslutning till `{streaming_service.value}` misslyckades.", footer="Troligtvis har de tvingats byta domän igen. Använd `/help` och `/update`"))

@client.tree.command(name="update", description="Uppdaterar URL som botten använder för att söka efter filmer", guild=guild_id)
@app_commands.choices(streaming_service=[
    app_commands.Choice(name="FlixHQ", value="FlixHQ"),
    app_commands.Choice(name="Lookmovie2", value="Lookmovie2")
])
@app_commands.describe(url="Ny URL")
async def update_url(interaction: discord.Interaction, streaming_service: app_commands.Choice[str], url: str):
    await interaction.response.defer()
    if streaming_service.name == "FlixHQ":
        global flixhq_base_url
        flixhq_base_url = url
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.green(), f"## `{streaming_service.name}` URL har ändrats till: `{url}`", footer="Don't let them catch up"))
    elif streaming_service.name == "Lookmovie2":
        global lookmovie2_base_url
        lookmovie2_base_url = url
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.green(), f"## `{streaming_service.name}` URL har ändrats till: `{url}`", footer="Don't let them catch up"))

help_commands = [
    app_commands.Choice(name="/play", value="play"),
    app_commands.Choice(name="/search", value="search"),
    app_commands.Choice(name="/update", value="update")
]

@client.tree.command(name="help", description="Visar information och hjälp om hur botten kan användas.", guild=guild_id)
@app_commands.choices(kommando=help_commands)
async def help_command(interaction: discord.Interaction, kommando: app_commands.Choice[str] = None):
    await interaction.response.defer()
    if kommando is None:
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.blue(), f"# Disney-", f"## Nuvarande konfig: \n### FlixHQ: \n`{flixhq_base_url}`\n### Lookmovie2: \n`{lookmovie2_base_url}`", f"Kommandon som går att använda: \n{", ".join(f"`{option.name}`" for option in help_commands)}", f"Använd `/help [kommando]` för hjälp angående det specifika kommandot."))
    elif kommando.value == "play":
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.blue(), f"## /play", f"`/play` tar emot en länk till valfri media och spelar upp i Watch2Gether-rummet. Kan vara Youtube, FlixHQ, Lookmovie osv osv. No one really knows.", "### Exempel: \n `/play` https://youtu.be/pXMkcpJN8QI"))
    elif kommando.value == "search":
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.blue(), f"## /search", f"`/search` tar emot en sökning av film eller serie, och ett val från listan av *streamingtjänster* och presenterar resultatet direkt i chatten.", "### Exempel: \n `/search` Jurassic Park `FlixHQ`"))
    elif kommando.value == "update":
        await interaction.followup.send(view=SimpleTextLayout(discord.Color.blue(), f"## /update", f"`/search` tar emot ett val av *streamingtjänst* och en URL och uppdaterar botten för att använda den nya URL:en, används när de har tvingats byta domän.", "### Exempel: \n `/update` `FlixHQ` https://flixhq.com"))

async def pagination(interaction: discord.Interaction, pagination_index: int):
    current_movies = movies[pagination_index: pagination_index + page_size if pagination_index + page_size < len(movies) else len(movies)]

    for index, movie in enumerate(current_movies):
            play_button = PlayButton(movie_title=movie.title, movie_url=movie.stream_link)
            layout = MovieLayout(movie, play_button)
            await interaction.channel.send(view=layout)

            if index == page_size - 1:
                clear_button = ClearButton()
                pagination_button = PaginationButton()
                buttonbox = ButtonBox(pagination_button, clear_button)
                
                if pagination_index + index == len(movies) - 1:
                    buttonbox_no_pagination = ButtonBox(clear_button, label=random.choice(end_of_list_strings))
                    await interaction.channel.send(view=buttonbox_no_pagination)
                    break
                
                await interaction.channel.send(view=buttonbox)
                break

async def clear_movie_options(interaction: discord.Interaction):
    global chosen_movie_card_id
    async for message in interaction.channel.history(limit=200):
        if message.author.id == client.user.id and message.id != chosen_movie_card_id:
            await message.delete()

client.run(token)