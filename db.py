import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random
import io
from datetime import datetime

# //////////////////////////////
# DEFINITIONS
# //////////////////////////////

def GetDB():
    """Connect to the database and return the connection object."""
    db = sqlite3.connect(".database/gtg.db")
    db.row_factory = sqlite3.Row
    return db

def GetAllGuesses():
    """Query all guesses and return them."""
    db = GetDB()
    try:
        guesses = db.execute("""
            SELECT Guesses.date, Guesses.game, Guesses.score, Users.username
            FROM Guesses
            JOIN Users ON Guesses.user_id = Users.id
            ORDER BY date DESC
        """).fetchall()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return []
    finally:
        db.close()
    return guesses

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

        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO Users(username, password) VALUES(?, ?)", (username, hashed_password))
        db.commit()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return False
    finally:
        db.close()

    return True

def AddReview(user_id, game_title, review_text, score):
    """
    Add a new review to the database.

    Args:
        user_id (int): ID of the user submitting the review.
        game_title (str): Title of the game being reviewed.
        review_text (str): The content of the review.
        score (int): The score given to the game.

    Returns:
        bool: True if the review was added successfully, False otherwise.
    """
    db = GetDB()
    try:
        current_time = datetime.now().replace(second=0, microsecond=0)

        db.execute("""
            INSERT INTO Reviews(user_id, date, game, review_text, score)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, current_time, game_title, review_text, score))

        db.commit()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return False
    finally:
        db.close()

    return True
 