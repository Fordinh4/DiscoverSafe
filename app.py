from flask import Flask, session, request, redirect, render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import spotipy
import os


app = Flask(__name__, template_folder= "templates")
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'

# Add database
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="fordinh",
    password="thesecretpasswords4.",
    hostname="fordinh.mysql.pythonanywhere-services.com",
    databasename="fordinh$Users_tokens"
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
# To tell SQLAlchemy that it should throw away connections that haven’t been used for 299 seconds, so that it doesn’t give them to you and cause your code to crash because it’s trying to use a connection that has already been closed by the server.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Disables a SQLAlchemy feature that we’re not going to be using – explicitly saying that we don’t want to use it stops us from getting confusing warning messages later on.

Session(app)
# Initialize the database
db = SQLAlchemy(app)


# Create model for the database
class UsersTokens(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False)
    access_token = db.Column(db.String(500), nullable=False)
    refresh_token = db.Column(db.String(500), nullable=False)




@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
                                            client_id="f68ecf6643c34970bedea990375c3bb7", 
                                            client_secret= "ff7e0fc2fc734208ac938458ef45d4a2", 
                                            redirect_uri= "http://fordinh.pythonanywhere.com/", 
                                            scope='user-read-currently-playing user-library-read playlist-modify-private playlist-modify-public',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):

        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))

        # Step 3. Get the access token and other token info
        token_info = auth_manager.get_cached_token()

        # Store user data and tokens in the database
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        user_id = spotify.me()["id"]
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]

        store_user_data(user_id, access_token, refresh_token)

        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 3. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return render_template('index.html', display_name=spotify.me()["display_name"])


@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route("/discover_weekly")
def SaveDiscoveryWeekly():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id="f68ecf6643c34970bedea990375c3bb7", 
                                            client_secret= "ff7e0fc2fc734208ac938458ef45d4a2", 
                                            redirect_uri= "http://fordinh.pythonanywhere.com/", 
                                            scope='user-read-currently-playing user-library-read playlist-modify-private playlist-modify-public',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    
    spotify = spotipy.Spotify(auth_manager= auth_manager)

     # Searching for discover weekly 
    SearchPlaylists = spotify.search("discover weekly", limit= 10, offset= 0, type= "playlist")["playlists"]["items"]
    try:
        for playlist in SearchPlaylists:
            if playlist["name"] == "Discover Weekly":
                DiscoverPlaylistId = playlist["id"]

    except:
        # If the user is still new to Spotify, it may take some weeks for the app to get enough info from user
        return "Discover weekly not found! -> If you r a new users, please listen to more songs :)"

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
        return ('Discover Weekly songs added successfully!')


def store_user_data(user_id, access_token, refresh_token):
    # Create a new users_tokens object
    user_token = UsersTokens(user_id=user_id, access_token=access_token, refresh_token=refresh_token)

    # Validate the user_id
    exists = db.session.query(UsersTokens.user_id).filter_by(user_id = user_id).first() is not None
    
    if not exists:
        # Add the object to the session
        db.session.add(user_token)

        try:
            # Commit the changes to the database if exist
            db.session.commit()
        except Exception as e:
            # Rollback the transaction in case of an error
            db.session.rollback()
            print("Error:", e)

        # Close the database session
        db.session.close()


if __name__ == '__main__':
    app.run(debug=True)