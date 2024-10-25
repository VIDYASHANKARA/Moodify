from flask import Flask, request, redirect, session, url_for
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


CLIENT_ID = '0c1714d29eb94aad9ab372b577434e8e'
CLIENT_SECRET = 'eeadce497f15453ca9fc391670194317'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = 'user-library-read playlist-read-private playlist-modify-private playlist-modify-public'


mood_data = {
    'sad': {'valence': (0.0, 0.4), 'energy': (0.0, 0.5)},
    'happy': {'valence': (0.6, 1.0), 'energy': (0.5, 1.0)},
    'calm': {'valence': (0.4, 0.6), 'energy': (0.0, 0.5)},
    'energetic': {'valence': (0.5, 1.0), 'energy': (0.7, 1.0)},
   
}

@app.route('/')
def index():
    return '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    
    <div class="container">
        <h1 style='margin-left:150px;margin-top:25px;'>Welcome to Moodify!</h1>
        <p style='margin-left:100px;margin-top:35px;margin-right:100px;font-size:large;'>Moodify is a personalized music experience that integrates with Spotify, giving users the ability to link their accounts and manage their playlists based on mood. Users can select their preferred moods and playlists, and Moodify will create and update mood-based playlists, delivering fresh music selections tailored to their current emotions.</p>
        <button style='margin-left:150px;margin-top:50px;background-color:none;width:300px;height:50px; '>
            <a href="/login" class="button">Login with Spotify</a>
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
    headers = {'Authorization': f'Bearer {access_token}'}

    liked_songs_url = 'https://api.spotify.com/v1/me/tracks'
    liked_songs_response = requests.get(liked_songs_url, headers=headers)
    liked_songs_data = liked_songs_response.json()
    liked_songs_total = liked_songs_data.get('total', 0)

    playlists_data = []
    offset, limit = 0, 50

    while True:
        response = requests.get(f'https://api.spotify.com/v1/me/playlists?offset={offset}&limit={limit}', headers=headers)
        data = response.json()
        playlists_data.extend(data.get('items', []))
        if len(data.get('items', [])) < limit:
            break
        offset += limit

    playlist_list = '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1 style='margin-left:500px;'>Select Your Playlists</h1>
    <form method="POST" id="playlistForm">
    <div class="playlist-container">
    '''
    if liked_songs_total > 0:
        playlist_list += f'''
        <div class="playlist-box" data-value="liked_songs">
            Liked Songs (Total Tracks: {liked_songs_total})
        </div>
        '''
    for playlist in playlists_data:
        playlist_list += f'''
        <div class="playlist-box" data-value="{playlist['id']}">
            {playlist['name']} (Total Tracks: {playlist['tracks']['total']})
        </div>
        '''
    playlist_list += '''
    </div>
    <input type="hidden" name="selected_playlists" id="selected_playlists">
    <button type="submit" class="button" style='margin-top:100px;margin-left:540px;'>Choose Mood</button>
    </form>
    <script>
        const playlistBoxes = document.querySelectorAll('.playlist-box');
        const selectedPlaylistsInput = document.getElementById('selected_playlists');
        playlistBoxes.forEach(box => {
            box.addEventListener('click', function() {
                box.classList.toggle('selected');
                const selectedPlaylists = Array.from(document.querySelectorAll('.playlist-box.selected')).map(b => b.getAttribute('data-value'));
                selectedPlaylistsInput.value = selectedPlaylists.join(',');
            });
        });
    </script>
    '''
    if request.method == 'POST':
        selected_playlists = request.form['selected_playlists'].split(',')
        session['selected_playlists'] = selected_playlists
        return redirect(url_for('select_mood'))
    return playlist_list

@app.route('/select_mood', methods=['GET', 'POST'])
def select_mood():
    moods = ['Sad', 'Happy', 'Calm', 'Energetic']
    mood_page = '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1  style='margin-left:500px;'>Select Your Mood</h1>
    <form method="POST" id="moodForm">
    <div class="mood-container">
    '''
    for mood in moods:
        mood_page += f'''
        <div class="mood-box" data-value="{mood.lower()}">
            {mood}
        </div>
        '''
    mood_page += '''
    </div>
    <input type="hidden" name="selected_moods" id="selected_moods">
    <button type="submit" class="button" style='margin-top:60px;margin-left:540px;'>Continue</button>
    </form>
    <p  style='margin-left:550px;margin-top:35px;margin-right:100px;font-size:large;'>Process takes a bit time :_( </p>
    <script>
        const moodBoxes = document.querySelectorAll('.mood-box');
        const selectedMoodsInput = document.getElementById('selected_moods');
        moodBoxes.forEach(box => {
            box.addEventListener('click', function() {
                box.classList.toggle('selected');
                const selectedMoods = Array.from(document.querySelectorAll('.mood-box.selected')).map(b => b.getAttribute('data-value'));
                selectedMoodsInput.value = selectedMoods.join(',');
            });
        });
    </script>
    '''
    if request.method == 'POST':
        selected_moods = request.form['selected_moods'].split(',')
        session['selected_moods'] = selected_moods
        return redirect(url_for('process_playlist'))
    return mood_page

@app.route('/process_playlist')
def process_playlist():
    access_token = session.get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    selected_playlists = session.get('selected_playlists', [])
    selected_moods = session.get('selected_moods', [])

    filtered_songs = []
    for playlist_id in selected_playlists:
        songs_url = 'https://api.spotify.com/v1/me/tracks' if playlist_id == 'liked_songs' else f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        response = requests.get(songs_url, headers=headers)
        songs = response.json().get('items', [])
        for song in songs:
            track = song['track']
            track_id = track['id']
            features_response = requests.get(f'https://api.spotify.com/v1/audio-features/{track_id}', headers=headers)
            features = features_response.json()
            valence, energy = features.get('valence'), features.get('energy')
            for mood in selected_moods:
                mood_criteria = mood_data.get(mood)
                if mood_criteria and mood_criteria['valence'][0] <= valence <= mood_criteria['valence'][1] and mood_criteria['energy'][0] <= energy <= mood_criteria['energy'][1]:
                    filtered_songs.append(f'spotify:track:{track_id}')
                    break

    if not filtered_songs:
        return '<h1>No songs matched the selected mood criteria.</h1>'

    user_id = requests.get('https://api.spotify.com/v1/me', headers=headers).json()['id']
    new_playlist = requests.post(f'https://api.spotify.com/v1/users/{user_id}/playlists', json={
        'name': f"Moodify - {'/'.join(selected_moods)} Playlist",
        'public': False
    }, headers=headers).json()
    new_playlist_id = new_playlist.get('id')

    for i in range(0, len(filtered_songs), 100):
        requests.post(f'https://api.spotify.com/v1/playlists/{new_playlist_id}/tracks', json={
            'uris': filtered_songs[i:i + 100]
        }, headers=headers)

    return redirect(url_for('success_page'))

@app.route('/success')
def success_page():
    return '''
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <h1  style='margin-left:520px;margin-top:25px;'>Congratulations!</h1>
    <p style='margin-left:490px;margin-top:35px;margin-right:100px;font-size:large;'>Your mood-based playlist has been created.</p>
    <button style='margin-top:30px;margin-left:540px;'><a href="https://open.spotify.com/" target="_blank">Open Spotify</a></button>
    '''

if __name__ == '__main__':
    app.run(debug=True)
