import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import face_recognition
import os
import numpy as np

# Connect to the SQLite database
conn = sqlite3.connect('wedding_photos.db')
cursor = conn.cursor()

# Fetch all people from the database (including those with names)
def fetch_all_people():
    cursor.execute("SELECT person_id, name FROM people")
    return cursor.fetchall()

# Fetch images for a specific person
def fetch_images_of_person(person_id):
    cursor.execute("SELECT file_path FROM images WHERE people LIKE ?", (f"%{person_id}%",))
    return cursor.fetchall()

# Update the person's name in the database
def update_person_name(person_id, new_name):
    cursor.execute("UPDATE people SET name = ? WHERE person_id = ?", (new_name, person_id))
    conn.commit()

# Delete the person from the database
def delete_person(person_id):
    cursor.execute("DELETE FROM people WHERE person_id = ?", (person_id,))
    conn.commit()

# Fetch the face encoding and crop the face from the image
def crop_face_from_image(image_path, face_encoding):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    # Find the matching face location for the given encoding
    for face_location, encoding in zip(face_locations, face_encodings):
        if face_recognition.compare_faces([encoding], face_encoding)[0]:
            top, right, bottom, left = face_location
            pil_image = Image.fromarray(image[top:bottom, left:right])
            return pil_image

    return None

# Fetch one of the images where a person's face appears and show their face
def fetch_person_image_and_encoding(person_id):
    cursor.execute("""
        SELECT images.file_path, people.face_encoding
        FROM images 
        JOIN people ON images.people LIKE '%' || people.person_id || '%' 
        WHERE people.person_id = ? LIMIT 1
    """, (person_id,))
    result = cursor.fetchone()

    if result:
        image_path, face_encoding_blob = result
        face_encoding = np.frombuffer(face_encoding_blob, dtype=np.float64)
        face_image = crop_face_from_image(image_path, face_encoding)
        return face_image

    return None

# UI to view and adjust labels for all people, including viewing their face
def view_all_people_ui():
    all_people = fetch_all_people()

    if not all_people:
        messagebox.showinfo("Info", "No people found!")
        return

    window = tk.Toplevel(root)
    window.title("All People")

    # Create a listbox to display all people
    people_listbox = tk.Listbox(window, height=15)
    people_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Function to refresh the people listbox
    def refresh_people_listbox():
        people_listbox.delete(0, tk.END)
        all_people = fetch_all_people()
        for person_id, name in all_people:
            display_name = name if name else f"Person {person_id}"
            people_listbox.insert(tk.END, f"{person_id}: {display_name}")

    refresh_people_listbox()

    # Frame for update and delete options and face display
    control_frame = tk.Frame(window)
    control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Image display area for selected person's face
    img_label = tk.Label(control_frame)
    img_label.pack()

    # Input field for updating person's name
    name_label = tk.Label(control_frame, text="Update Name:")
    name_label.pack()

    name_entry = tk.Entry(control_frame)
    name_entry.pack()

    # Function to update the selected person's name
    def update_name():
        selected = people_listbox.curselection()
        if selected:
            person_info = people_listbox.get(selected[0])
            person_id = int(person_info.split(":")[0])
            new_name = name_entry.get()
            if new_name:
                update_person_name(person_id, new_name)
                messagebox.showinfo("Success", "Name updated successfully!")
                refresh_people_listbox()
            else:
                messagebox.showwarning("Warning", "Please enter a name.")

    # Button to update the name
    update_button = tk.Button(control_frame, text="Update Name", command=update_name)
    update_button.pack()

    # Function to delete the selected person
    def delete_person_entry():
        selected = people_listbox.curselection()
        if selected:
            person_info = people_listbox.get(selected[0])
            person_id = int(person_info.split(":")[0])
            delete_person(person_id)
            messagebox.showinfo("Success", "Person deleted successfully!")
            refresh_people_listbox()

    # Button to delete the person
    delete_button = tk.Button(control_frame, text="Delete Person", command=delete_person_entry)
    delete_button.pack()

    # Function to show the selected person's face when clicked
    def on_person_select(event):
        selected = people_listbox.curselection()
        if selected:
            person_info = people_listbox.get(selected[0])
            person_id = int(person_info.split(":")[0])
            face_image = fetch_person_image_and_encoding(person_id)
            if face_image:
                face_image.thumbnail((200, 200))  # Resize for display
                face_img_display = ImageTk.PhotoImage(face_image)
                img_label.config(image=face_img_display)
                img_label.image = face_img_display  # Keep a reference to avoid garbage collection
            else:
                img_label.config(image=None)

    # Bind listbox selection to face display function
    people_listbox.bind("<<ListboxSelect>>", on_person_select)

    window.mainloop()

# UI to display images of a selected person
def display_images_ui():
    def on_person_select(event):
        selected_person = people_dropdown.get()
        if selected_person:
            person_id = selected_person.split(":")[0]  # Extract person_id from the dropdown text
            images = fetch_images_of_person(person_id)
            if images:
                for widget in images_frame.winfo_children():
                    widget.destroy()  # Clear old images before showing new ones
                for img_path in images:
                    img = Image.open(img_path[0])
                    img.thumbnail((200, 200))  # Resize for UI
                    img_display = ImageTk.PhotoImage(img)

                    img_label = tk.Label(images_frame, image=img_display)
                    img_label.image = img_display  # Keep a reference to avoid garbage collection
                    img_label.pack()
            else:
                messagebox.showinfo("Info", "No images found for this person.")

    # Fetch all people from the database
    all_people = fetch_all_people()

    # Create a new window
    window = tk.Toplevel(root)
    window.title("Select Person")

    # Dropdown menu for selecting a person
    people_var = tk.StringVar(window)
    people_dropdown = ttk.Combobox(window, textvariable=people_var)
    people_dropdown['values'] = [f"{person_id}: {name}" for person_id, name in all_people]
    people_dropdown.bind("<<ComboboxSelected>>", on_person_select)
    people_dropdown.pack()

    # Frame to display images
    images_frame = tk.Frame(window)
    images_frame.pack()

    window.mainloop()

# Main Tkinter window
root = tk.Tk()
root.title("People Labeling and Image Viewer")

# Button for viewing and adjusting labels for all people
view_all_people_button = tk.Button(root, text="View/Adjust All People", command=view_all_people_ui)
view_all_people_button.pack(pady=10)

# Button for selecting a person and viewing images
view_images_button = tk.Button(root, text="View Images by Person", command=display_images_ui)
view_images_button.pack(pady=10)

root.mainloop()

# Close the SQLite connection when done
conn.close()
