# For the website
from flask import Flask, session, request, redirect, render_template
from flask_session import Session

# For the database
from flask_sqlalchemy import SQLAlchemy

# For the authorization of Spotify
import spotipy

# For sending email
from email.message import EmailMessage
import ssl
import smtplib

# Other
import os
from .setting import Setting


app = Flask(__name__, template_folder= "templates")
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize the setting
setting = Setting()

# Add database
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username=setting.dbUsername,
    password=setting.dbPassword,
    hostname=setting.dbHostname,
    databasename=setting.dbName
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
# To tell SQLAlchemy that it should throw away connections that haven’t been used for 299 seconds, so that it doesn’t give them to you and cause your code to crash because it’s trying to use a connection that has already been closed by the server.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Disables a SQLAlchemy feature that we’re not going to be using – explicitly saying that we don’t want to use it stops us from getting confusing warning messages later on.


# Initialize session in flask
Session(app)
# Initialize the database
db = SQLAlchemy(app)


# Create model for the database
class UsersTokens(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False)
    access_token = db.Column(db.String(500), nullable=False)
    refresh_token = db.Column(db.String(500), nullable=False)

# ================

@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = CreateSpotifyOauth(cache_handler)

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
        user_email = spotify.me()["email"]

        store_user_data(user_id, access_token, refresh_token, user_email)

        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        #TODO: Change this to another html for sign up for this app
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
    auth_manager = CreateSpotifyOauth(cache_handler)

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

# ================

def store_user_data(user_id, access_token, refresh_token, user_email):

    # Create a new users_tokens object
    user_token = UsersTokens(user_id=user_id, access_token=access_token, refresh_token=refresh_token)

    # Validate the user_id
    exists = db.session.query(UsersTokens.user_id).filter_by(user_id = user_id).first() is not None
    
    if not exists:
        # Only send the email if the user is new and not in the database
        send_email(user_email)

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

def CreateSpotifyOauth(cache_handler):
    auth_manager = spotipy.oauth2.SpotifyOAuth(
                                            client_id=setting.client_id, 
                                            client_secret= setting.client_secret, 
                                            redirect_uri= setting.redirect_uri, 
                                            scope= setting.scope,
                                               cache_handler=cache_handler,
                                               show_dialog=True)
    return auth_manager


def send_email(user_email):
    # To send the user_email to me to add it in Spotify developer user management
    subject = "There is a new user that use your Spotify Weekly app!"
    body = f"The new user email is: {user_email}. \nPlease add it to your user management in https://developer.spotify.com/dashboard!"

    # Preparing the email
    email = EmailMessage()
    email['From'] = setting.email_sender
    email['To'] = setting.email_receiver
    email['Subject'] = subject
    email.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context= context) as smtp:
        # Set the secure connection to send the email
        smtp.login(setting.email_sender, setting.email_password)
        smtp.sendmail(setting.email_sender, setting.email_receiver, email.as_string())

if __name__ == '__main__':
    app.run(debug=True)