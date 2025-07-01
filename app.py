from urllib import request
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
app.secret_key = 'supergeheim'

def get_db_connection():
    conn = sqlite3.connect('datenbank.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_spender', methods=['GET', 'POST'])
def register_spender():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        passwort = request.form['passwort']
        passwort_repeat = request.form['passwort_repeat']
        adresse = request.form['adresse']

        if passwort != passwort_repeat:
            return render_template('register_spender.html', fehler='Die Passwörter stimmen nicht überein.')

        hashed_password = generate_password_hash(passwort)

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO spender (name, email, passwort, adresse) VALUES (?, ?, ?, ?)',
                (name, email, hashed_password, adresse)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login_spender'))

        except sqlite3.IntegrityError:
            return 'E-Mail bereits registriert. Bitte verwende eine andere.'

    return render_template('register_spender.html', fehler='E-Mail bereits registriert.')

@app.route('/register_organisation')
def register_organisation():
    return render_template('register_organisation.html')

@app.route('/login_spender', methods=['GET', 'POST'])
def login_spender():
    if request.method == 'POST':
        email = request.form['email']
        passwort = request.form['passwort']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM spender WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['passwort'], passwort):
            session['user_id'] = user['id']
            return redirect(url_for('startseite'))
        else:
            return render_template('login_spender.html', fehler='Login fehlgeschlagen. Bitte überprüfe deine Daten.')

    return render_template('login_spender.html')

@app.route('/login_organisation')
def login_organisation():
    return render_template('login_organisation.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/startseite')
def startseite():
    return render_template('startseite.html')

@app.route('/suche')
def suche():
    return render_template('suche.html')

@app.route('/spenden')
def spenden():
    return render_template('spenden.html')

@app.route('/einstellungen')
def einstellungen():
    return render_template('einstellungen.html')

if __name__ == '__main__':
    app.run(debug=True)