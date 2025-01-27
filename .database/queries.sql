-- CREATE TABLE Games (
--     id INTEGER PRIMARY KEY,
--     name TEXT,
--     developer TEXT,
--     year INTEGER,
--     publisher TEXT,
--     platform TEXT,
--     genre TEXT
-- );

-- CREATE TABLE Reviews (
--     id INTEGER PRIMARY KEY,
--     user_id INTEGER NOT NULL,
--     date TEXT NOT NULL,
--     game TEXT NOT NULL,
--     review_text TEXT NOT NULL,
--     score INTEGER NOT NULL,
--     FOREIGN KEY (user_id) REFERENCES Users(id)
-- );

-- CREATE TABLE IF NOT EXISTS Users (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT UNIQUE NOT NULL,
--     password TEXT NOT NULL
-- );


                    
-- CREATE TABLE Games (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     genre TEXT,
--     release_date DATE,
--     developer TEXT,
--     publisher TEXT
-- );
-- DROP TABLE IF EXISTS Users;
