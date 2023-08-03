"""Because my Spotify app is in development mode so it only accept up to 25 users"""
import spotipy
import datetime
from setting import Setting
from sqlalchemy import create_engine

#Initialize the setting
setting = Setting()

def ValidateUser(refresh_token):
    # Check if the user have revoked my app yet, if yes then delete from the database
    sp_oauth = CreateSpotifyOauth()

    try:
        token_info = sp_oauth.refresh_access_token(refresh_token)

    except Exception as e:
        # Check if the user have revoked my app yet, if yes then delete from the database
        if "revoked" in vars(e)["error_description"]:
            engine = create_engine("mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
                                    username=setting.dbUsername,
                                    password=setting.dbPassword,
                                    hostname=setting.dbHostname,
                                    databasename=setting.dbName))


            with engine.connect() as connection:
                # It automatically takes care of closing the connection once the block is exited
                connection.execute(f'DELETE FROM users_tokens WHERE refresh_token = "{refresh_token}"')

            return False

    else:
        # The user haven't revoked my app yet
        return True


def ExtractDatabase():
    refresh_tokens = []
    engine = create_engine("mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
                            username=setting.dbUsername,
                            password=setting.dbPassword,
                            hostname=setting.dbHostname,
                            databasename=setting.dbName))

    with engine.connect() as connection:
        # It automatically takes care of closing the connection once the block is exited
        result = connection.execute('SELECT refresh_token FROM users_tokens')

    for row in result:
        refresh_tokens.append(row[0])

    return refresh_tokens


def AddDiscoverWeekly(refresh_token):
    # Initialize SpotipyOAuth with your client_id, client_secret, and redirect_uri
    sp_oauth = CreateSpotifyOauth()

    # Get a new access token using the refresh token
    token_info = sp_oauth.refresh_access_token(refresh_token)

    # Create a new instance of Spotify class using the new access token
    spotify = spotipy.Spotify(auth=token_info['access_token'])


    # Searching for discover weekly
    DiscoverPlaylistId = None
    flag = False
    SearchPlaylists = spotify.search("discover weekly", limit= 10, offset= 0, type= "playlist")["playlists"]["items"]

    for playlist in SearchPlaylists:
        if playlist["name"] == "Discover Weekly":
            flag = True
            DiscoverPlaylistId = playlist["id"]

    if not flag:
        # If the user is still new to Spotify, it may take some weeks for the app to get enough info from user
        print("Discover weekly not found! -> If you r a new users, please listen to more songs :)")

    else:
        # Create a new playlist to save all of Discover Weekly in one place!
        CurrentPlaylists = spotify.current_user_playlists()["items"]
        user_id = spotify.current_user()["id"]
        SavedDiscoverPlaylistId = None

        for playlist in CurrentPlaylists:
            if playlist["name"] == "Saved Discover Weekly":
                SavedDiscoverPlaylistId = playlist["id"]

        if not SavedDiscoverPlaylistId:
            # If the new playlist not found, create a new one
            NewPlaylist = spotify.user_playlist_create(user_id,"Saved Discover Weekly", True)
            SavedDiscoverPlaylistId = NewPlaylist["id"]

        # get the tracks from the Discover Weekly playlist
        discover_weekly_playlist = spotify.playlist_items(DiscoverPlaylistId)
        song_uris = []
        # song URI => The resource identifier of, for example, an artist, album or track.
        for song in discover_weekly_playlist['items']:
            song_uri= song['track']['uri']
            song_uris.append(song_uri)

        # Add the tracks to the Saved Weekly playlist
        spotify.user_playlist_add_tracks(user_id, SavedDiscoverPlaylistId, song_uris, None)

        # Return a success message
        print('Discover Weekly songs added successfully!')

def CreateSpotifyOauth():
    return spotipy.SpotifyOAuth(client_id=setting.client_id,
                                    client_secret=setting.client_secret,
                                    redirect_uri=setting.redirect_uri,
                                    scope=setting.scope)



def main():
    today = datetime.date.today()
    weekday = today.weekday()

    if weekday == 3:
        refresh_tokens = ExtractDatabase()
        for refresh_token in refresh_tokens:
            if ValidateUser(refresh_token):
                # If the user haven't revoked my app, proceed adding the songs
                AddDiscoverWeekly(refresh_token)
    else:
        print(f"Nuh Uh, today is {today} and not Tuesday!")



if __name__ == '__main__':
    main()