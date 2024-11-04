from concurrent.futures import ThreadPoolExecutor
from spotipy.oauth2 import SpotifyOAuth
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import aiosqlite
import discord
import spotipy
import aiohttp
import asyncio
import json
import os


class playlist(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.executor = ThreadPoolExecutor()

        load_dotenv()
        self.SPOTIFY_ID = os.getenv('SPOTIFY_ID')
        self.SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
        self.SPOTIFY_URI = os.getenv('SPOTIFY_URI')
        self.SPOTIFY_UID = os.getenv('SPOTIFY_UID')
        self.SCOPE = 'playlist-modify-private playlist-modify-public'

        self.sp_oauth = SpotifyOAuth(client_id=self.SPOTIFY_ID, client_secret=self.SPOTIFY_SECRET, redirect_uri=self.SPOTIFY_URI, scope=self.SCOPE)
        self.sp = self.get_spotify_client()


    def get_spotify_client(self):
        token_file = 'token_info.json'

        token_info = self.sp_oauth.get_cached_token()
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token_info = json.load(f)

        if self.sp_oauth.is_token_expired(token_info):
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])

        with open(token_file, 'w') as f:
            json.dump(token_info, f)

        return spotipy.Spotify(auth=token_info['access_token'])


    async def refresh_token(self):
        while not self.bot.is_closed():
            try:
                self.sp = self.get_spotify_client()
                await asyncio.sleep(3601)
            except Exception as error:
                print('Exception trying to refresh spotify token')
                print(error)


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    async def get_playlist(self):
        # check if playlist exists
        loop = asyncio.get_event_loop()
        playlists = await loop.run_in_executor(self.executor, self.sp.current_user_playlists)
        for playlist in playlists['items']:
            if playlist['name'] == 'Teensforlife Colab':
                return playlist

        # else create playlist
        user_id = self.sp.current_user()['id']
        bearer_id = self.sp_oauth.get_access_token()['access_token']
        async with aiohttp.ClientSession() as session:
            playlist_data = {
                'name': 'Teensforlife Colab',
                'description': 'Collaborative playlist for Teensforlife',
                'public': True
            }
            response = await session.post(
                f'https://api.spotify.com/v1/users/{user_id}/playlists',
                headers={
                    'Authorization': f'Bearer {bearer_id}',
                    'Content-Type': 'application/json'
                },
                json=playlist_data
            )
            if response.status == 201:
                playlist = await response.json()
                print('Created Teensforlife playlist')
                return playlist
            else:
                print(f'Failed to create playlist: {response.status} {await response.text()}')

    @app_commands.command(name='add', description='Add a song to the Teensforlife Spotify playlist')
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def add_song(self, inter: discord.Interaction, url: str):
        await inter.response.defer()
        specified_channel_id = await self.execute_query('SELECT musicChannel FROM guildConfigs WHERE guildid = ?', (inter.guild.id,))
        specified_channel_id = specified_channel_id[0][0]
        if specified_channel_id is not None:
            if specified_channel_id != inter.channel.id:
                channel = self.bot.get_channel(specified_channel_id)
                await inter.response.send_message(f'Please use this command in {channel.mention}', ephemeral=True)
                return

        playlist = await self.get_playlist()
        track_id = url.split('/')[-1].split('?')[0]
        try:
            loop = asyncio.get_event_loop()
            track = await loop.run_in_executor(self.executor, self.sp.track, track_id)
            response = self.sp.playlist_add_items(playlist['id'], [track_id])
            await inter.followup.send(f'Added song: `{track['name']} - {', '.join(artist['name'] for artist in track['artists'])}` to [Teensforlife playlist]({playlist['external_urls']['spotify']})')
            await self.execute_query('INSERT INTO spotifyPlaylist (url, addedByUser) VALUES (?, ?)', (url, inter.user.id))
        except Exception as error:
            await inter.response.send_message('Error adding track to playlist!', ephemeral=True)

    @add_song.error
    async def command_error(self, inter: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            await inter.response.send_message(f'This command is on coodown. You can use it again in {error.retry_after:.2f} seconds.', ephemeral=True)
        else:
            print(error)


    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.refresh_token())


async def setup(bot):
    await bot.add_cog(playlist(bot))
