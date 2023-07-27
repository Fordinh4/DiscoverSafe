import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# Use flask for the Oauth and automating process

app = Flask(__name__)

app.config["SessionCookieName"] = "Spotify Cookie" # -> Work like dict
app.secret_key = "l;dskfjL:KJl;234sadfLKjdsf"
TOKEN_INFO = 'token_info'

# it begin at @app.route -> give the user the login page by redirect that url -> after logged in and accept to authorize, move to /redirect -> in that route, it will save the token info in the session storage -> then we get redirect to /SaveDiscoveryWeekly and this is where we do the magic


@app.route("/")
def login():
    auth_url = CreateSpotifyOauth().get_authorize_url() # Gets the URL to use to authorize this app -> to allow my app to access user data
    return redirect(auth_url)

@app.route("/redirect")
# When get back the information from Oauth it will save the token info and save it in session storage
def redirect_page():
    session.clear()
    code = request.args.get('code') # Used to retrieve the value of the RL and allows you to access data sent to the server
    TokenInfo = CreateSpotifyOauth().get_access_token(code) # Gets the access token for the app given the code -> used for authentication, security, and access control to ensure authorized and secure access to the Spotify API resources
    session[TOKEN_INFO] = TokenInfo

    return redirect(url_for('SaveDiscoveryWeekly', _external = True))
    # url_for => can change the content of the URL in one shot
    # _external = True => generates an absolute URL (including the domain name)


@app.route("/saveDiscoverWeekly")
def SaveDiscoveryWeekly():
    try:
        TokenInfo = get_token()

    except:
        print("User not logged in!")
        return redirect("/")
    
    sp = spotipy.Spotify(auth= TokenInfo["access_token"])

    SearchPlaylists = sp.search("discover weekly", limit= 10, offset= 0, type= "playlist")["playlists"]["items"]

    try:
        for playlist in SearchPlaylists:
            if playlist["name"] == "Discover Weekly":
                DiscoverPlaylistId = playlist["id"]
    
    except:
        return "Discover weekly not found! -> If you r a new users, please listen to more songs :)"

    else:
        # Either create a new playlist or save all of it in one place! -> in one place
        CurrentPlaylists = sp.current_user_playlists()["items"]
        SavedDiscoverPlaylistId = None

        for playlist in CurrentPlaylists:
            if playlist["name"] == "Saved Discover Weekly":
                SavedDiscoverPlaylistId = playlist["id"]
        
        user_id = sp.current_user()["id"]
        if not SavedDiscoverPlaylistId:
            NewPlaylist = sp.user_playlist_create(user_id,"Saved Discover Weekly", True)
            SavedDiscoverPlaylistId = NewPlaylist["id"]


        # get the tracks from the Discover Weekly playlist
        discover_weekly_playlist = sp.playlist_items(DiscoverPlaylistId)
        song_uris = []
        for song in discover_weekly_playlist['items']:
            song_uri= song['track']['uri']
            song_uris.append(song_uri)
        
        # add the tracks to the Saved Weekly playlist
        sp.user_playlist_add_tracks(user_id, SavedDiscoverPlaylistId, song_uris, None)

        # return a success message
        return ('Discover Weekly songs added successfully!')



def get_token():
    TokenInfo = session.get(TOKEN_INFO, None) # To retrieve our token -> if there no token in session, it will return None
    if not TokenInfo:
        redirect(url_for('login', _external=False))
    
    now = int(time.time())

    is_expired = TokenInfo["expires_at"] - now < 60 # The token info will return 3 keys: access_token, token_type, and expires_in

    if is_expired:
        spotify_oauth = CreateSpotifyOauth()
        TokenInfo = spotify_oauth.refresh_access_token(TokenInfo['refresh_token'])
        # .refresh_token => method in SpotifyOAuth obtains a new access token using a refresh token, ensuring continuous access to the user's Spotify data without requiring re-authentication.
    
    return TokenInfo



def CreateSpotifyOauth():
    # TODO: What if I want to save the playlist without saving the discover weekly at the first place?
    # Setting up the login page for the user to authorize my app to do in scope like read their library, modify public/private playlist
    return SpotifyOAuth(client_id="f68ecf6643c34970bedea990375c3bb7", client_secret= "ff7e0fc2fc734208ac938458ef45d4a2", redirect_uri= url_for("redirect_page", _external=True), scope= "user-library-read playlist-modify-private playlist-modify-public")
    # The redirect uri is where the client will get send to after the account authorization is successful. You could also set up a redirect for an authorization failure.


app.run(debug=True)
