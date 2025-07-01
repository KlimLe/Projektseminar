import sqlite3

conn = sqlite3.connect('datenbank.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS spender (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, passwort TEXT, adresse TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS sachspende (id INTEGER PRIMARY KEY, produkt TEXT, ort TEXT, kaufdatum TEXT, user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS geldspende (id INTEGER PRIMARY KEY, betrag REAL, zahlungsmethode TEXT, organisation TEXT, user_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL)")
conn.commit()
conn.close()