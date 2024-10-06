import sqlite3

# Create a connection to a SQLite database
conn = sqlite3.connect('wedding_photos.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Creating DB tables 
cursor.execute('''
CREATE TABLE people (
    person_id INTEGER PRIMARY KEY,
    face_encoding BLOB, -- The face encoding (128-dimensional vector)
    name TEXT,          -- Will be NULL initially until manually assigned
    key_person BOOLEAN  -- Will be NULL or False initially
);
''')

cursor.execute('''
CREATE TABLE images (
    image_id INTEGER PRIMARY KEY,
    file_path TEXT,     -- Path to the image file
    event TEXT,         -- Event type (wedding, pre-wedding, etc.)
    quality INTEGER,    -- Image quality score (1-10)
    people TEXT         -- Comma-separated person_ids detected in the image
);

''')

# Commit changes and close the connection
conn.commit()
conn.close()
