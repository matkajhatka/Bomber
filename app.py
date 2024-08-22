from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')  # Store this securely in production

# Google Sheets setup
SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', r'C:\\Users\\JJ ALWAYS\\Desktop\\BOMBER II\\BOMBER 2.0\\BOMBER 4.0\\FLASK App\\stable-electron-420205-4065e78b4988.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '1AxX4wbMFewrDvifpEufLr76zOxyFtsnfslxGUujuGdo')

# Helper functions
def get_users_data():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Users!A2:C").execute()
    return result.get('values', [])

def update_user_balance(username, new_balance):
    users = get_users_data()
    for index, user in enumerate(users, start=2):
        if user[0] == username:
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"Users!C{index}",
                valueInputOption="USER_ENTERED",
                body={"values": [[new_balance]]}
            ).execute()
            break

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('game'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = get_users_data()
    
        for user in users:
            if user[0] == username and check_password_hash(user[1], password):
                try:
                    session['balance'] = int(float(user[2]))  # Convert to float first, then to int
                except ValueError:
                    return 'Invalid balance format in the database', 400
                session['username'] = username
                return redirect(url_for('game'))
        return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = get_users_data()

        if any(user[0] == username for user in users):
            return 'Username already exists'

        hashed_password = generate_password_hash(password)
        new_user = [[username, hashed_password, 50]]  # Start with a balance of 50
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Users!A:C",
            valueInputOption="USER_ENTERED",
            body={"values": new_user}
        ).execute()

        session['username'] = username
        session['balance'] = 50
        return redirect(url_for('game'))
    return render_template('register.html')

@app.route('/game')
def game():
    if 'username' in session:
        return render_template('game.html', balance=session['balance'])
    return redirect(url_for('home'))

@app.route('/update_balance', methods=['POST'])
def update_balance():
    if 'username' in session:
        try:
            new_balance = int(float(request.json.get('balance')))
            session['balance'] = new_balance
            update_user_balance(session['username'], new_balance)
            return jsonify({'status': 'success'})
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid balance format'}), 400
    return jsonify({'status': 'not_logged_in'})

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('balance', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
