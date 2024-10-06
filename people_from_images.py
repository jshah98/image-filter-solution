import os
import sqlite3
import face_recognition
import numpy as np

# Function to check if face encoding is already in the database (cosine similarity)
def is_new_face(new_encoding, existing_encodings, threshold=0.6):
    if len(existing_encodings) == 0:
        return True
    distances = face_recognition.face_distance(existing_encodings, new_encoding)
    return np.min(distances) > threshold

# Load all people from the database
def load_existing_people(cursor):
    cursor.execute("SELECT person_id, face_encoding FROM people")
    existing_people = cursor.fetchall()

    # Convert face_encoding BLOBs back to NumPy arrays
    existing_encodings = [np.frombuffer(person[1], dtype=np.float64) for person in existing_people]
    person_ids = [person[0] for person in existing_people]
    
    return existing_encodings, person_ids

# Process a single image to find faces and add to the database
def process_image(image_path, cursor, existing_encodings, person_ids):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    detected_people_ids = []
    
    for face_encoding in face_encodings:
        # Check if the face encoding is a new person
        if is_new_face(face_encoding, existing_encodings):
            # Add new person to the people table
            cursor.execute("INSERT INTO people (face_encoding) VALUES (?)", [face_encoding.tobytes()])
            person_id = cursor.lastrowid
            detected_people_ids.append(person_id)
            
            # Add the new encoding to our list of known encodings
            existing_encodings.append(face_encoding)
            person_ids.append(person_id)
        else:
            # Existing person, find their ID
            idx = np.argmin(face_recognition.face_distance(existing_encodings, face_encoding))
            detected_people_ids.append(person_ids[idx])
    
    # Insert the image into the images table
    cursor.execute("""
        INSERT INTO images (file_path, event, quality, people) 
        VALUES (?, ?, ?, ?)
    """, (image_path, "wedding", 10, ','.join(map(str, detected_people_ids))))

# Recursively scan a directory for image files and process them
def scan_directory(directory, cursor, existing_encodings, person_ids):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_path = os.path.join(root, file)
                print(f"Processing image: {image_path}")
                process_image(image_path, cursor, existing_encodings, person_ids)

# Main function to structure the flow
def main():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('wedding_photos.db')
    cursor = conn.cursor()

    # Load all existing people from the database
    existing_encodings, person_ids = load_existing_people(cursor)

    # Directory containing the wedding images
    image_directory = 'test photos'

    # Start processing images in the directory and subdirectories
    scan_directory(image_directory, cursor, existing_encodings, person_ids)

    # Commit changes and close the database connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
