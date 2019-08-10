from flask import *
import database, auth_helper, avatar_helper

app = Flask(__name__)

# Editing HTTP Headers

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def disable_xss_protection(response):
    """
    This disables the XSS auditor in Google Chrome which prevents some
    exploits from working.

    DO NOT count this as a vulnerability, we only do it to make finding
    the vulnerabilities easier.
    """
    response.headers['X-XSS-Protection'] = '0'
    return response

# No caching at all for API endpoints.
@app.after_request
def no_caching(response):
    """
    This disables caching static files so that all images displayed on 
    site are up-to-date.

    DO NOT count this as a vulnerability, we only do it to make finding
    the vulnerabilities easier.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Helper Functions

def make_escaper(replacements):
    def escaper(inp):
        for old, new in replacements.items():
            inp = inp.replace(old, new)
        return inp
    return escaper

escape_sql = make_escaper({
    "'": "''",
    '--': '&ndash;',
    '*': '&#42;',
    ';': ''
    })

escape_html = make_escaper({
    '<': '&lt;',
    '>': '&gt;'
    })

def get_user_info(username):
    pinfo = database.fetchone("SELECT avatar, age FROM users WHERE username='{}';".format(username))
    if not pinfo:
        return '', 0

    avatar = escape_html(pinfo[0])
    age = pinfo[1]
    return avatar, age

# Routes

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/avatar_images/<path:path>')
def send_avatar_images(path):
    return send_from_directory('avatar_images', path)

@app.route('/')
@auth_helper.get_username
def index(username):
    return render_template('index.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
@auth_helper.get_username
def login(username):
    if username:
        return render_template('index.html', username=username, error='Already logged in.')

    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    if not username.isalnum():
        return render_template('login.html', error='Bad username!')

    correct = auth_helper.check_login(username, password)
    if not correct:
        return render_template('login.html', error='Incorrect password.')

    session_id = auth_helper.generate_session_id()
    database.execute("INSERT INTO sessions VALUES ('{}', '{}');".format(session_id, username))

    resp = redirect(url_for('wall'))
    resp.set_cookie('SESSION_ID', session_id)
    return resp

@app.route('/logout')
@auth_helper.get_username
@auth_helper.csrf_protect
def logout(username):
    if not username:
        return render_template('index.html', error='Error')

    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('SESSION_ID', '')
    return resp

@app.route('/wall')
@app.route('/wall/<other_username>')
@auth_helper.get_username
@auth_helper.csrf_protect
def wall(username, other_username=None):
    other_username = other_username or auth_helper.get_username_from_session()
    if not other_username:
        return redirect(url_for('index'))

    other_username = escape_sql(other_username)
    if not auth_helper.is_valid_username(other_username):
        return render_template('no_wall.html', username=other_username)

    db_posts = database.fetchall("SELECT post FROM posts WHERE username='{}';".format(other_username))
    posts = [post[0] for post in db_posts]
    avatar, age = get_user_info(other_username)

    return render_template('wall.html', username=username, other_username=other_username, posts=posts, avatar=avatar, age=age)

@app.route('/profile', methods=['GET', 'POST'])
@auth_helper.get_username
@auth_helper.csrf_protect
def profile(username):
    if not username:
        return render_template('login.html', error='Please log in.')

    if request.method == 'GET':
        avatar_filename, age = get_user_info(username)
        age = escape_html(str(age))
        return render_template('profile.html', username=username, avatar=avatar_filename, age=age)

    if 'avatar' in request.files:
        avatar = request.files['avatar']
        stored_avatar_filename = avatar_helper.save_avatar_image(avatar, username)
        stored_avatar_filename = escape_sql(escape_html(stored_avatar_filename))
        if stored_avatar_filename:
            database.execute("UPDATE users SET avatar='{}' WHERE username='{}';".format(stored_avatar_filename, username))
    else:
        username = escape_sql(request.form['username'])
        age = escape_html(escape_sql(request.form['age']))
        database.execute("UPDATE users SET age={} WHERE username='{}';".format(age, username))

    return redirect(url_for('wall'))

@app.route('/delete_avatars', methods=['GET', 'POST'])
@auth_helper.get_username
@auth_helper.csrf_protect
def delete_avatars(username):
    if not username:
        return render_template('login.html', error='Please log in.')

    if request.method == 'GET':
        avatars = avatar_helper.list_user_dir(username)
        return render_template('delete_avatars.html', username=username, avatars=avatars)

    curr_avatar, age = get_user_info(username)
    user_dir = avatar_helper.init_user_dir(username)
    avatars = request.form.getlist('avatar')
    for avatar in avatars:
        if user_dir in avatar:
            avatar_helper.delete_avatar_image(avatar, username)
            if curr_avatar == avatar:
                database.execute("UPDATE users SET avatar='' WHERE username='{}';".format(username))
    
    return redirect(url_for('wall'))    

@app.route('/post', methods=['GET', 'POST'])
@auth_helper.get_username
@auth_helper.csrf_protect
def post(username):
    if not username:
        return render_template('login.html', error='Please log in.')

    if request.method == 'GET':
        return render_template('post.html', username=username)

    post = escape_sql(request.form['post'])
    database.execute("INSERT INTO posts VALUES ('{}', '{}');".format(username, post))
    return redirect(url_for('wall'))
