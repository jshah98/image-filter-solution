# image-filter-solution
This repository includes code that scans a file for all images, identifies who is in each image, and creates a database with People and Images with columns that can be used for filtering.


Database Schema:

CREATE TABLE people (
    person_id INTEGER PRIMARY KEY,
    face_encoding BLOB, -- The face encoding (128-dimensional vector)
    name TEXT,          -- Will be NULL initially until manually assigned
    key_person BOOLEAN  -- Will be NULL or False initially
);

CREATE TABLE images (
    image_id INTEGER PRIMARY KEY,
    file_path TEXT,     -- Path to the image file
    event TEXT,         -- Event type (wedding, pre-wedding, etc.)
    quality INTEGER,    -- Image quality score (1-10)
    people TEXT         -- Comma-separated person_ids detected in the image
);
