from flask import Flask, request, redirect, session, url_for
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a secure key in production

# Replace with your Spotify Developer credentials
CLIENT_ID = '0c1714d29eb94aad9ab372b577434e8e'
CLIENT_SECRET = 'eeadce497f15453ca9fc391670194317'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-library-read playlist-read-private playlist-modify-private'

# Moods and their color gradients
mood_data = {
    'calm': 'linear-gradient(to right, #00c6ff, #0072ff)',  # Calm - Blue gradient
    'contentment': 'linear-gradient(to right, #fbc2eb, #a6c1ee)',  # Contentment - Light pink & purple
    'energetic': 'linear-gradient(to right, #ff6a00, #ee0979)',  # Energetic - Orange & pink
    'happy': 'linear-gradient(to right, #fbd786, #f7797d)',  # Happy - Yellow & pink
    'sad': 'linear-gradient(to right, #1e3c72, #2a5298)',  # Sad - Dark blue
    'depressed': 'linear-gradient(to right, #485563, #29323c)',  # Depressed - Grey & dark
    'party': 'linear-gradient(to right, #00f260, #0575e6)',  # Party - Green & blue
    'pop': 'linear-gradient(to right, #ff9a9e, #fecfef)',  # Pop - Pink shades
    'workout': 'linear-gradient(to right, #f85032, #e73827)',  # Workout - Red gradient
    'dinner': 'linear-gradient(to right, #ee9ca7, #ffdde1)',  # Dinner - Soft pink
    'sleep': 'linear-gradient(to right, #2980b9, #2c3e50)',  # Sleep - Calm dark blue
    'romantic': 'linear-gradient(to right, #ffafbd, #ffc3a0)'  # Romantic - Soft red & peach
}

@app.route('/')
def index():
    return '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <div class="container">
        <h1 style='margin-left:100px;'>Welcome to the Moodify!</h1><br>
        <p style='margin-left:40px;font-size:medium;'>Moodify is a personalized music experience that integrates with Spotify, 
            <br>giving users the ability to link their accounts and manage their 
            <br>playlists based on mood.
            <br>Users can select their preferred moods and playlists,
            <br>and Moodify will create and update mood-based playlists, 
            <br>delivering fresh music selections tailored to their current emotions.</p>
        <button style='margin-left:170px;margin-top:100px;'>
        <a href="/login" class="button" >Login with Spotify</a>
        </button>
    </div>
    '''

@app.route('/login')
def login():
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Exchange the authorization code for an access token
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    
    token_info = response.json()
    access_token = token_info.get('access_token')
    
    if access_token:
        session['access_token'] = access_token
        return redirect(url_for('playlists'))
    else:
        return '<h1>Error obtaining access token</h1>'

@app.route('/playlists', methods=['GET', 'POST'])
def playlists():
    access_token = session.get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Get liked songs as a "playlist"
    liked_songs_url = 'https://api.spotify.com/v1/me/tracks'
    liked_songs_response = requests.get(liked_songs_url, headers=headers)
    liked_songs_data = liked_songs_response.json()
    liked_songs_total = liked_songs_data.get('total', 0)  # Total number of liked songs

    # Fetch user playlists
    playlists_data = []
    offset = 0
    limit = 50  # Number of items per request (max is 50)

    # Fetch playlists from the Spotify API
    while True:
        response = requests.get(f'https://api.spotify.com/v1/me/playlists?offset={offset}&limit={limit}', headers=headers)
        data = response.json()

        playlists_data.extend(data.get('items', []))

        # Break if we get fewer than 'limit' playlists (i.e., we've fetched all playlists)
        if len(data.get('items', [])) < limit:
            break

        offset += limit

    # If no playlists are found
    if not playlists_data:
        return '<h1>No playlists found. Please ensure you have playlists in your account.</h1>'

    # Generate playlist selection page
    playlist_list = '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1 style='margin-left:500px;'>Select Your Playlists</h1>
    <form method="POST" id="playlistForm">
    <div class="playlist-container">
    '''

    # Add "Liked Songs" as a box if available
    if liked_songs_total > 0:
        playlist_list += f'''
        <div class="playlist-box" data-value="liked_songs">
            Liked Songs (Total Tracks: {liked_songs_total})
        </div>
        '''

    # Add other playlists as boxes
    for playlist in playlists_data:
        playlist_list += f'''
        <div class="playlist-box" data-value="{playlist['id']}">
            {playlist['name']} (Total Tracks: {playlist['tracks']['total']})
        </div>
        '''

    playlist_list += '''
    </div>
    <input type="hidden" name="selected_playlists" id="selected_playlists">
    <button type="submit" class="button" style='margin-top:200px;'>Choose Mood</button>
    </form>
    <br><button style='margin-left:1080px;margin-top:-86px;'><a href="/" class="button">Home</a></button>

    <script>
        const playlistBoxes = document.querySelectorAll('.playlist-box');
        const selectedPlaylistsInput = document.getElementById('selected_playlists');

        playlistBoxes.forEach(box => {
            box.addEventListener('click', function() {
                // Toggle the green border on click
                box.classList.toggle('selected');
                
                // Collect selected playlist values
                const selectedPlaylists = Array.from(document.querySelectorAll('.playlist-box.selected')).map(b => b.getAttribute('data-value'));
                selectedPlaylistsInput.value = selectedPlaylists.join(',');
            });
        });
    </script>
    '''

    if request.method == 'POST':
        # Retrieve selected playlists from hidden input
        selected_playlists = request.form['selected_playlists']
        selected_playlists = selected_playlists.split(',')
        return redirect(url_for('select_mood'))  # Redirect to mood selection page

    return playlist_list


@app.route('/select_mood', methods=['GET', 'POST'])
def select_mood():
    # List of moods with gradient backgrounds
    moods = {
        'Calm': 'linear-gradient(to right, #00c6ff, #0072ff)',  # Calm - Blue gradient
        'Contentment': 'linear-gradient(to right, #fbc2eb, #a6c1ee)',  # Contentment - Light pink & purple
        'Energetic': 'linear-gradient(to right, #ff6a00, #ee0979)',  # Energetic - Orange & pink
        'Happy': 'linear-gradient(to right, #fbd786, #f7797d)',  # Happy - Yellow & pink
        'Sad': 'linear-gradient(to right, #1e3c72, #2a5298)',  # Sad - Dark blue
        'Depressed': 'linear-gradient(to right, #485563, #29323c)',  # Depressed - Grey & dark
        'Party': 'linear-gradient(to right, #00f260, #0575e6)',  # Party - Green & blue
        'Pop': 'linear-gradient(to right, #ff9a9e, #fecfef)',  # Pop - Pink shades
        'Workout': 'linear-gradient(to right, #f85032, #e73827)',  # Workout - Red gradient
        'Dinner': 'linear-gradient(to right, #ee9ca7, #ffdde1)',  # Dinner - Soft pink
        'Sleep': 'linear-gradient(to right, #2980b9, #2c3e50)',  # Sleep - Calm dark blue
        'Romantic': 'linear-gradient(to right, #ffafbd, #ffc3a0)'  # Romantic - Soft red & peach
    }

    # Generate the HTML for the mood selection page
    mood_page = '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1 style='text-align:center;'>Select Your Mood</h1>
    <form method="POST" id="moodForm">
    <div class="mood-container">
    '''

    # Add the mood boxes with gradients in rows of 4
    for mood, gradient in moods.items():
        mood_page += f'''
        <div class="mood-box" data-value="{mood.lower()}" style="background: {gradient};">
            {mood}
        </div>
        '''

    mood_page += '''
    </div>
    <input type="hidden" name="selected_moods" id="selected_moods">
    <div class="button-container">
        <button type="button" class="button"><a href="/" class="button-link">Home</a></button>
        <button type="button" class="button"><a href="/playlists" class="button-link">Playlists</a></button>
        <button type="submit" class="button">Continue</button>
    </div>
    </form>

    <script>
        const moodBoxes = document.querySelectorAll('.mood-box');
        const selectedMoodsInput = document.getElementById('selected_moods');

        moodBoxes.forEach(box => {
            box.addEventListener('click', function() {
                // Toggle the green border on click
                box.classList.toggle('selected');
                
                // Collect selected moods
                const selectedMoods = Array.from(document.querySelectorAll('.mood-box.selected')).map(b => b.getAttribute('data-value'));
                selectedMoodsInput.value = selectedMoods.join(',');
            });
        });
    </script>
    '''

    if request.method == 'POST':
        # Retrieve selected moods and redirect to processing page
        selected_moods = request.form['selected_moods']
        selected_moods = selected_moods.split(',')

        # Store selected moods in the session
        session['selected_moods'] = selected_moods
        
        return redirect(url_for('process_playlist'))

    return mood_page

@app.route('/process_playlist')
def process_playlist():
    selected_moods = session.get('selected_moods')
    access_token = session.get('access_token')

    if not selected_moods or not access_token:
        return redirect(url_for('playlists'))

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Fetch user's liked songs
    liked_songs_url = 'https://api.spotify.com/v1/me/tracks'
    liked_songs_response = requests.get(liked_songs_url, headers=headers)
    liked_songs_data = liked_songs_response.json().get('items', [])

    # Filter songs based on selected mood
    filtered_songs = []
    for song in liked_songs_data:
        track_id = song['track']['id']
        
        # Fetch audio features of each song
        audio_features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
        audio_features_response = requests.get(audio_features_url, headers=headers)
        audio_features = audio_features_response.json()

        # Example mood filtering logic based on valence and energy
        valence = audio_features.get('valence')
        energy = audio_features.get('energy')

        # Example: Filter "Sad" songs with low valence and energy
        if 'sad' in selected_moods and valence < 0.4 and energy < 0.5:
            filtered_songs.append(track_id)
        
        # Similar filtering can be applied for other moods

    # Create a new playlist
    user_profile_url = 'https://api.spotify.com/v1/me'
    user_profile_response = requests.get(user_profile_url, headers=headers)
    user_id = user_profile_response.json().get('id')

    create_playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    playlist_response = requests.post(create_playlist_url, json={
        'name': f"{selected_moods[0].capitalize()} Mood Playlist",
        'description': f"A playlist based on your {selected_moods[0]} mood",
        'public': False
    }, headers=headers)

    playlist_id = playlist_response.json().get('id')

    # Add the filtered songs to the new playlist
    add_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    requests.post(add_tracks_url, json={
        'uris': [f'spotify:track:{track_id}' for track_id in filtered_songs]
    }, headers=headers)

    return redirect(url_for('congratulations', mood=selected_moods[0]))


@app.route('/congratulations/<mood>')
def congratulations(mood):
    return f'''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1 style='text-align:center;'>Congratulations!</h1>
    <p style='text-align:center;'>Your new {mood.capitalize()} playlist has been created!</p>
    <button style='display: block; margin: 0 auto;'>
        <a href="https://open.spotify.com/" class="button-link">Open Spotify</a>
    </button>
    <button style='display: block; margin: 0 auto; margin-top: 20px;'>
        <a href="/" class="button-link">Home</a>
    </button>
    '''



if __name__ == '__main__':
    app.run(port=5000, debug=True)
