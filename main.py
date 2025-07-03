from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename


def get_db_connection():
    conn = sqlite3.connect('datenbank.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['UPLOAD_FOLDER_ZERTIFIKATE'] = 'static/zertifikate'
app.config['UPLOAD_FOLDER_SPENDEN'] = 'static/spenden_bilder'
app.config['DEBUG'] = True

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

    return render_template('register_spender.html')

@app.route('/register_organisation', methods=['GET', 'POST'])
def register_organisation():
    if request.method == 'POST':
        name = request.form['org-name']
        email = request.form['email']
        passwort = request.form['passwort']
        passwort_repeat = request.form['passwort-repeat']
        adresse = request.form['adresse']
        file = request.files.get('zertifikat')

        if passwort != passwort_repeat:
            return 'Passwörter stimmen nicht überein'

        hashed_password = generate_password_hash(passwort)

        zertifikat_pfad = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            zertifikat_pfad = os.path.join(app.config['UPLOAD_FOLDER_ZERTIFIKATE'], filename)
            file.save(zertifikat_pfad)

        conn = get_db_connection()
        conn.execute('INSERT INTO organisation (name, email, passwort, adresse, zertifikat) VALUES (?, ?, ?, ?, ?)',
                     (name, email, hashed_password, adresse, zertifikat_pfad))
        conn.commit()
        conn.close()

        return redirect(url_for('login_organisation'))

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

@app.route('/login_organisation', methods=['GET', 'POST'])
def login_organisation():
    if request.method == 'POST':
        email = request.form['email']
        passwort = request.form['passwort']

        conn = get_db_connection()
        org = conn.execute('SELECT * FROM organisation WHERE email = ?', (email,)).fetchone()
        conn.close()

        if org and check_password_hash(org['passwort'], passwort):
            session['org_id'] = org['id']
            return redirect(url_for('startseite'))
        else:
            return render_template('login_organisation.html', fehler='Login fehlgeschlagen. Bitte überprüfe deine Daten.')

    return render_template('login_organisation.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/startseite')
def startseite():
    if 'user_id' in session:
        return render_template('startseite.html')
    elif 'org_id' in session:
        return render_template('startseite_organisation.html')
    else:
        return redirect(url_for('index'))

@app.route('/suche')
def suche():
    conn = get_db_connection()

    sachspenden = conn.execute(
        'SELECT * FROM sachspende WHERE org_id IS NULL'
    ).fetchall()

    conn.close()
    return render_template('suche.html', sachspenden=sachspenden)

@app.route('/spenden', methods=['GET', 'POST'])
def spenden():
    if 'user_id' not in session:
        return redirect(url_for('login_spender'))

    if request.method == 'POST':
        spendenart = request.form.get('spendenart')
        conn = get_db_connection()
        user_id = session['user_id']

        try:
            if spendenart == 'sache':
                produkt = request.form['produkt']
                ort = request.form['ort']
                kaufdatum = request.form['kaufdatum']

                file = request.files.get('bild')
                bild_pfad = None
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    spenden_bilder_ordner = app.config['UPLOAD_FOLDER_SPENDEN']
                    os.makedirs(spenden_bilder_ordner, exist_ok=True)
                    full_path = os.path.join(spenden_bilder_ordner, filename)
                    file.save(full_path)
                    bild_pfad = os.path.join('spenden_bilder', filename).replace('\\', '/')
                else:
                    fehler = "Ungültiges Dateiformat. Bitte nur JPG, PNG oder JPEG hochladen."
                    return render_template('spenden.html', fehler=fehler)

                conn.execute(
                    'INSERT INTO sachspende (produkt, ort, kaufdatum, user_id, bild) VALUES (?, ?, ?, ?, ?)',
                    (produkt, ort, kaufdatum, user_id, bild_pfad)
                )

            elif spendenart == 'geld':
                betrag = float(request.form['betrag'])
                zahlungsmethode = request.form['zahlungsmethode']
                organisation = request.form['organisation']
                conn.execute(
                    'INSERT INTO geldspende (betrag, zahlungsmethode, organisation, user_id) VALUES (?, ?, ?, ?)',
                    (betrag, zahlungsmethode, organisation, user_id)
                )

            conn.commit()
            erfolg = "Spende erfolgreich eingetragen!"
            return render_template('spenden.html', erfolg=erfolg)

        except Exception as e:
            fehler = f"Fehler beim Speichern: {e}"
            return render_template('spenden.html', fehler=fehler)

        finally:
            conn.close()

    return render_template('spenden.html')

@app.route('/einstellungen')
def einstellungen():
    if 'user_id' in session:
        conn = get_db_connection()
        nutzer = conn.execute('SELECT * FROM spender WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return render_template('einstellungen.html', nutzer=nutzer)

    elif 'org_id' in session:
        conn = get_db_connection()
        orga = conn.execute('SELECT * FROM organisation WHERE id = ?', (session['org_id'],)).fetchone()
        conn.close()
        return render_template('einstellungen.html', nutzer=orga)

    return redirect(url_for('index'))

@app.route('/meine_spenden')
def meine_spenden():
    if 'user_id' not in session:
        return redirect(url_for('login_spender'))

    user_id = session['user_id']
    conn = get_db_connection()
    sachspenden = conn.execute(
        'SELECT * FROM sachspende WHERE user_id = ?', (user_id,)
    ).fetchall()
    geldspenden = conn.execute(
        'SELECT * FROM geldspende WHERE user_id = ?', (user_id,)
    ).fetchall()
    conn.close()

    return render_template('meine_spenden.html', sachspenden=sachspenden, geldspenden=geldspenden)

@app.route('/spende_annehmen/<int:spende_id>', methods=['POST'])
def spende_annehmen(spende_id):
    if 'org_id' not in session:
        return redirect(url_for('login_organisation'))

    org_id = session['org_id']
    conn = get_db_connection()

    conn.execute('UPDATE sachspende SET org_id = ? WHERE id = ?', (org_id, spende_id))
    conn.commit()
    conn.close()

    return redirect(url_for('suche'))

@app.route('/zertifikate', methods=['GET', 'POST'])
def zertifikate():
    if 'org_id' not in session:
        return redirect(url_for('login_organisation'))

    conn = get_db_connection()

    if request.method == 'POST':
        file = request.files.get('zertifikat')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            pfad = os.path.join(app.config['UPLOAD_FOLDER_SPENDEN'], filename)
            file.save(pfad)

            conn.execute("UPDATE organisation SET zertifikat = ? WHERE id = ?", (pfad, session['org_id']))
            conn.commit()

    org = conn.execute('SELECT * FROM organisation WHERE id = ?', (session['org_id'],)).fetchone()
    conn.close()

    return render_template('zertifikate.html', org=org)

@app.route('/org_spenden')
def org_spenden():
    if 'org_id' not in session:
        return redirect(url_for('login_organisation'))

    conn = get_db_connection()
    org_id = session['org_id']

    angenommene_sachspenden = conn.execute(
        'SELECT * FROM sachspende WHERE org_id = ?', (org_id,)
    ).fetchall()

    verfuegbare_sachspenden = conn.execute(
        'SELECT * FROM sachspende WHERE org_id IS NULL'
    ).fetchall()

    geldspenden = conn.execute(
        'SELECT * FROM geldspende WHERE organisation_id = ?', (org_id,)
    ).fetchall()

    conn.close()

    return render_template(
        'org_spenden.html',
        angenommene_sachspenden=angenommene_sachspenden,
        verfuegbare_sachspenden=verfuegbare_sachspenden,
        geldspenden=geldspenden
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)