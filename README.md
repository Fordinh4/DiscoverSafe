# DiscoverSafe

## Description
DiscoverSafe is an app that automates the process of saving the Spotify Discover Weekly playlist to users' playlists every Thursday. Aimed at enhancing the Spotify experience, DiscoverSafe provides a seamless integration for users to back up their favorite discoveries.

**Note:** Since the app is in the development phase, it currently accepts up to 25 users only.

## Problems & Solutions
During the development phase, a variety of problems were encountered and solved:

1. **Handling User Tokens**
    - **Problem**: Storing user's refresh tokens and continuously using them was a challenge.
    - **Solution**: Utilizing SQLAlchemy, the user's access tokens and refresh tokens were saved in a MySQL database hosted on PythonAnywhere, allowing automatic retrieval instead of manual interaction by the user.

2. **Automating Playlist Saving**
    - **Problem**: Automating the process of saving the playlist instead of relying on the user to manually press the button.
    - **Solution**: A separate Python script (`automate.py`) was developed to run through the database, validate users, and add the Discover Weekly songs to the user's playlist.

3. **User Authentication and Revoking**
    - **Problem**: Handling cases where users revoke access or are new to Spotify and have not generated a Discover Weekly playlist.
    - **Solution**: Implemented validation checks for user authentication and cases where the Discover Weekly playlist isn't found.

4. **Email Notification for New Users**
    - **Problem**: Notifying the developer about new users to add them to the Spotify developer user management.
    - **Solution**: Implemented an email notification system to alert the developer when a new user signs up, allowing easy addition to user management on the Spotify developer dashboard.


## Features
1. **Automated Saving of Discover Weekly:** Automatically saves Spotify's Discover Weekly playlist to a user-specific playlist named "DiscoverSafe."
   
2. **Email Notifications:** Sends me email notifications to let me know when new users sign up so I can add them to Spotify for Developers' user management.
   
3. **Automated Token Management:** Efficiently stores and retrieves user tokens from a MySQL database.
   
4. **User Authentication & Authorization:** Secure user authentication and authorization using Spotify OAuth.

## Technologies Used
- **Flask**: Web application framework.
- **Spotipy**: Library for Spotify Web API.
- **Flask-SQLAlchemy**: Database management.
- **MySQL**: For storing user tokens.
- **SMTP & SSL**: For sending email notifications.

## How to Use This App
1. Clone the repository.
2. Set up the necessary environment variables (found in `setting.py`).
3. Run `app.py` to launch the Flask app.
4. Navigate to the hosted web page and sign in with your Spotify account.
5. Allow permissions for the app to manage your playlists.
6. The app will handle the rest, saving your Discover Weekly playlist automatically!

## Future Updates
1. **Multiple Playlist Options**
   - Users will have the option to save all songs in one playlist named DiscoverSafe or separate playlists named DiscoverSafe | (DD/MM/YYYY).
     
2. **Enhanced Spotify Features**
   - Incorporation of a mini version of Spotify warped, showing top songs that users listen to, the top artist, and more personalized insights.
     
3. **User-Customized Schedule**
   - Providing users with the ability to customize the schedule for automatic playlist saving, allowing daily, weekly, or monthly backups according to personal preferences.
     
4. **Advanced Notification System**
   - Implementing push notifications and/or email summaries to notify users about successful backups or any issues, along with a weekly summary of their musical discoveries.
     
5. **Collaborative Playlists**
    - Allowing users to create collaborative playlists with friends, merging different Discover Weekly playlists into a shared experience.
      
6. **Enhanced Security Measures**
    - Implementing additional security layers to ensure user data protection and compliance with privacy regulations.


**-> Stay tunned for future updates!**

