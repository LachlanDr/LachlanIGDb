import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db

# //////////////////////////////
# FLASK + SECRET KEY (APP FUNCTIONS)
# //////////////////////////////

app = Flask(__name__)
app.secret_key = "gtg" 

# //////////////////////////////
# DEFINITIONS: USER AUTHENTICATION
# //////////////////////////////

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

    if user is not None and check_password_hash(user['password'], password):
        return user
    return None

def RegisterUser(username, password, pfp):
    if not username or not password:
        return False

    db = GetDB()
    try:
        existing_user = db.execute("SELECT * FROM Users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            return False

        hash = generate_password_hash(password)
        db.execute("INSERT INTO Users(username, password, profile_picture) VALUES(?, ?, ?)", (username, hash, pfp))
        db.commit()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return False
    finally:
        db.close()

    return True


def load_games_from_txt():
    """Dynamically find and load the games from the text file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    txt_filename = "TextDump_GameOnly.txt"
    txt_path = os.path.join(script_dir, txt_filename) 

    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as file:
            games = file.readlines()
        return [game.strip() for game in games]
    return []

def search_games(query):
    games = load_games_from_txt()
    return [game for game in games if query.lower() in game.lower()]

def GetLatestReviews():
    """Fetch the last 3 reviews from the database, including the user's profile picture."""
    db = GetDB()
    try:
        reviews = db.execute(""" 
            SELECT Reviews.date, Reviews.game, Reviews.review_text, Reviews.score, 
                   Users.username, Users.profile_picture 
            FROM Reviews 
            JOIN Users ON Reviews.user_id = Users.id 
            ORDER BY Reviews.date DESC 
            LIMIT 3 
        """).fetchall()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return []
    finally:
        db.close()
    return reviews



# //////////////////////////////
# APP ROUTES: DISPLAY PAGES
# //////////////////////////////

@app.route("/")
def home():
    """Home page displaying the newest reviews."""
    reviews = GetLatestReviews()
    return render_template("index.html", reviews=reviews)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    games = search_games(query) if query else []
    return render_template('search.html', games=games, query=query)

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
    if 'id' not in session:
        flash("You need to be logged in to write a review.", "danger")
        return redirect('/login')

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
    if 'id' not in session:
        flash("You need to be logged in to view your profile.", "danger")
        return redirect('/login')

    user_id = session['id']
    
    db = GetDB()
    try:
        user_info = db.execute("SELECT username, profile_picture FROM Users WHERE id = ?", (user_id,)).fetchone()
        user_reviews = db.execute(""" 
            SELECT Reviews.id, Reviews.date, Reviews.game, Reviews.review_text, Reviews.score 
            FROM Reviews
            WHERE user_id = ? 
            ORDER BY date DESC 
        """, (user_id,)).fetchall()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        user_info, user_reviews = None, []
    finally:
        db.close()
    
    return render_template('profile.html', user=user_info, reviews=user_reviews)


@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self';"
    return response

@app.route('/reviews', methods=['GET'])
def reviews():
    """Fetch all reviews from the database, optionally filtered by search query."""
    query = request.args.get('query', '').lower()  

    db = GetDB()
    try:
        if query:
            all_reviews = db.execute(""" 
                SELECT Reviews.date, Reviews.game, Reviews.review_text, Reviews.score, Users.username, Users.profile_picture 
                FROM Reviews 
                JOIN Users ON Reviews.user_id = Users.id 
                WHERE LOWER(Reviews.game) LIKE ? 
                   OR LOWER(Reviews.review_text) LIKE ? 
                   OR LOWER(Users.username) LIKE ? 
                ORDER BY Reviews.date DESC 
            """, ('%' + query + '%', '%' + query + '%', '%' + query + '%')).fetchall()
        else:
            all_reviews = db.execute(""" 
                SELECT Reviews.date, Reviews.game, Reviews.review_text, Reviews.score, Users.username, Users.profile_picture 
                FROM Reviews 
                JOIN Users ON Reviews.user_id = Users.id 
                ORDER BY Reviews.date DESC 
            """).fetchall()

    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        all_reviews = []
    finally:
        db.close()
    
    return render_template('reviews.html', reviews=all_reviews, query=query)


@app.route('/update_username', methods=['POST'])
def update_username():
    """Allow the user to update their username."""
    if 'id' not in session:
        flash("You must be logged in to update your username.", "danger")
        return redirect('/login')

    new_username = request.form['new_username']
    user_id = session['id']

    db = GetDB()
    try:
        existing_user = db.execute("SELECT id FROM Users WHERE username = ?", (new_username,)).fetchone()
        if existing_user:
            flash("Username already taken. Please choose another.", "danger")
        else:
            db.execute("UPDATE Users SET username = ? WHERE id = ?", (new_username, user_id))
            db.commit()
            session['username'] = new_username 
            flash("Username updated successfully!", "success")
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        flash("An error occurred while updating your username.", "danger")
    finally:
        db.close()

@app.route('/update_pfp', methods=['POST'])
def update_pfp():
    if 'id' not in session:
        flash("You need to be logged in to update your profile picture.", "danger")
        return redirect('/login')

    new_pfp = request.form.get('profile_picture', 0)  # Default to 0 if no selection
    print(f"Received profile picture: {new_pfp}")  # Debugging line

    if not new_pfp:
        flash("Please select a profile picture.", "danger")
        return redirect('/profile')

    db = GetDB()
    try:
        db.execute("UPDATE Users SET profile_picture = ? WHERE id = ?", (new_pfp, session['id']))
        db.commit()
        flash("Profile picture updated!", "success")
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        flash("Error updating profile picture.", "danger")
    finally:
        db.close()

    return redirect('/profile')


@app.route('/delete_account', methods=['POST'])
def delete_account():
    """Allow the user to delete their account."""
    if 'id' not in session:
        flash("You must be logged in to delete your account.", "danger")
        return redirect('/login')

    user_id = session['id']

    db = GetDB()
    try:
        db.execute("DELETE FROM Users WHERE id = ?", (user_id,))
        db.commit()
        session.clear() 
        flash("Your account has been deleted.", "success")
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        flash("An error occurred while deleting your account.", "danger")
    finally:
        db.close()

    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        profile_picture = request.form.get('profile_picture', 0) 

        if RegisterUser(username, password, profile_picture):
            flash('Registration successful! You can now log in.', 'success')
            return redirect('/login')
        else:
            flash('Username already taken or error occurred.', 'danger')
            return redirect('/register')
    
    return render_template('register.html') 

    


# //////////////////////////////
# BEGIN
# //////////////////////////////
if __name__ == "__main__":
    app.run(debug=True, port=5000)
