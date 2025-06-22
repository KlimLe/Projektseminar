from flask import Flask, render_template
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_spender')
def register_spender():
    return render_template('register_spender.html')

@app.route('/register_organisation')
def register_organisation():
    return render_template('register_organisation.html')

@app.route('/login_spender')
def login_spender():
    return render_template('login_spender.html')

@app.route('/login_organisation')
def login_organisation():
    return render_template('login_organisation.html')

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