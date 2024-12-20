import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import db

app = Flask(__name__)
app.secret_key = "gtg" 


def GetDB():
    """Connect to the database and return the connection object."""
    db = sqlite3.connect(".database/gtg.db")
    db.row_factory = sqlite3.Row
    return db

def CheckLogin(username, password):
    """Check if the provided username and password match a user in the database."""
    db = GetDB()
    try:
        user = db.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None
    finally:
        db.close()

    if user is not None:

        if check_password_hash(user['password'], password):
            return user
    return None

def RegisterUser(username, password):
    """Register a new user in the database."""
    if not username or not password:
        return False

    db = GetDB()
    try:
        existing_user = db.execute("SELECT * FROM Users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            return False


        hash = generate_password_hash(password)
        db.execute("INSERT INTO Users(username, password) VALUES(?, ?)", (username, hash))
        db.commit()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return False
    finally:
        db.close()

    return True


def load_games_from_txt(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            games = file.readlines()
        return [game.strip() for game in games]
    return []

def search_games(query):
    games = load_games_from_txt("G:/My Drive/IST - 12/Assignment/Game Review/TextDump_GameOnly.txt")
    return [game for game in games if query.lower() in game.lower()]  


@app.route("/")
def home():
    """Home page displaying the newest reviews."""



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = CheckLogin(username, password)
        if user:
            session['username'] = username
            session['id'] = user['id']
            flash('Logged in successfully!', 'success')
            return redirect('/')
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None) 
    session.pop('id', None)  
    flash('Logged out successfully!', 'success')
    return redirect('/')


@app.route('/write_review/<game_name>', methods=['GET', 'POST'])
def write_review(game_name):
    if request.method == 'POST':
        review_text = request.form['review']
        user_id = session.get('id') 
        score = request.form['rating']  
        

        if db.AddReview(user_id, game_name, review_text, score):
            flash(f'Review for {game_name} submitted!', 'success')
        else:
            flash('There was an issue submitting your review. Please try again.', 'danger')
        
        return redirect('/search')  

    return render_template('write_review.html', game_name=game_name)

@app.route('/profile')
def profile():
    """Display the user's profile, including their reviews."""
    if 'id' not in session:
        flash("You need to be logged in to view your profile.", "danger")
        return redirect('/login')

    user_id = session['id']
    
    db = GetDB()
    try:
        user_reviews = db.execute("""
            SELECT Reviews.id, Reviews.date, Reviews.game, Reviews.review_text, Reviews.score 
            FROM Reviews
            WHERE user_id = ?
            ORDER BY date DESC
        """, (user_id,)).fetchall()
        
        user_info = db.execute("SELECT username FROM Users WHERE id = ?", (user_id,)).fetchone()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        user_reviews = []
        user_info = None
    finally:
        db.close()
    
    return render_template('profile.html', user=user_info, reviews=user_reviews)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if RegisterUser(username, password):
            flash('Account created successfully!', 'success')
            return redirect('/login')
        else:
            flash('Username already exists or invalid input, please try again.', 'danger')
    return render_template('register.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
