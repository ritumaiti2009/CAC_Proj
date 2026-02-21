import os

from helpers import error
from werkzeug.utils import secure_filename

# Handles image directory
UPLOAD_PATH = "static/uploads"
os.makedirs(UPLOAD_PATH, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "heic", "heif"}


# Check if file is accepted by checking if file type matches the accepted ones
def check_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Get unique filename for image upload
def get_unique_filepath(filename):
    # Seperate name from extension
    base, ext = os.path.splitext(filename)

    counter = 1
    unique_name = filename
    while os.path.exists(os.path.join(UPLOAD_PATH, unique_name)):
        unique_name = f"{base}_{counter}{ext}"
        counter += 1
    return os.path.join(UPLOAD_PATH, unique_name)


# Save image to UPLOAD_PATH
def save_image(image):
    filepath = None
    if image and image.filename != "":
        if check_allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = get_unique_filepath(filename)
            image.save(filepath)
            return filepath
        else:
            return error("Error uploading image: Invalid file type", 415)


# Remove image from UPLOAD_PATH
def del_image(image_path):
    os.remove(image_path)
