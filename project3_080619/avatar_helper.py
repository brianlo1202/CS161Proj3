import os
import sys
import shutil

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
CREATE_DIR_MSG = 'Creating a directory for {username} at avatar_images/{username}/'
CREATE_FILE_MSG = 'Creating a file for {username} at {filepath}'
DELETE_FILE_MSG = 'Deleting {filepath}'
BAD_FILEPATH = "Attempting to read/write bad filepath: {path}"

def allowed_extension(path):
    return '.' in path and \
        path.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_path(path):
    path_to_avatar_images = os.path.realpath('avatar_images')
    my_path = os.path.realpath(path)
    if path_to_avatar_images in my_path:
        return True
    else:
        print(BAD_FILEPATH.format(path=path), file=sys.stderr)
        return False


def init_user_dir(username):
    user_dir = os.path.join('avatar_images', username)
    if not os.path.isdir(user_dir) and allowed_path(user_dir):
        print(CREATE_DIR_MSG.format(username=username), file=sys.stderr)
        os.makedirs(user_dir)
    return user_dir

def list_user_dir(username):
    user_dir = init_user_dir(username)
    if allowed_path(user_dir):
        return [os.path.join(user_dir, f) for f in os.listdir(user_dir)]

def save_avatar_image(avatar, username):
    try:
        assert avatar.filename != ''
        assert allowed_extension(avatar.filename)    
        user_dir = init_user_dir(username)
        file_filepath = os.path.join(user_dir, avatar.filename)
        assert allowed_path(file_filepath)
        print(CREATE_FILE_MSG.format(username=username, filepath=file_filepath), file=sys.stderr)
        avatar.save(file_filepath)
        return file_filepath
    except AssertionError:
        pass

def delete_avatar_image(avatar_filename, username):
    user_dir = init_user_dir(username)
    try:
        assert allowed_path(avatar_filename)
        assert os.path.isfile(avatar_filename)
        assert user_dir in avatar_filename
        print(DELETE_FILE_MSG.format(filepath=avatar_filename), file=sys.stderr)
        os.remove(avatar_filename)
    except AssertionError:
        pass

def init_avatar_images():
    """
    This sets up the avatar_images/ folder up for you with 
    a picture for the user dirks.
    """
    print("Reloading avatar_images/", file=sys.stderr)
    shutil.rmtree('avatar_images', ignore_errors=True)
    os.makedirs('avatar_images')
    dirks_dir = init_user_dir("dirks")
    file_filepath = os.path.join(dirks_dir, 'dirks.jpg')
    shutil.copyfile('static/images/dirks.jpg', file_filepath)

init_avatar_images()
