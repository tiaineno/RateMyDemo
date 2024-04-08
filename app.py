#import all requires libraries
from os import getenv
from flask import Flask
from flask import redirect, render_template, request, session, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
load_dotenv()

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://"
db = SQLAlchemy(app)
app.secret_key = getenv("SECRET_KEY")

# Fetches recent releases and the most popular releases and returns the home page
@app.route("/")
def index():
    sql = text("""SELECT U.username as username, R.id, R.title FROM releases R, users U
               WHERE R.user_id = U.id ORDER BY R.id DESC LIMIT 3""")
    releases = db.session.execute(sql)
    releases = releases.fetchall()

    sql = text("""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               WHERE RA.rating IS NOT NULL GROUP BY R.id, U.username, R.title ORDER BY rating DESC LIMIT 3""")
    most_popular = db.session.execute(sql)
    most_popular = most_popular.fetchall()
    return render_template("index.html", releases=releases, most_popular=most_popular)

# Returns the login page
@app.route("/login")
def tili():
    return render_template("login.html", v = False)

# Handle user login and return the home page
@app.route("/login2", methods = ["POST"])
def login2():
    username = request.form["username"]
    password = request.form["password"]
    sql = text("SELECT id, password FROM users WHERE username = :username")
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    #return the login page if user is not found
    if not user:
        return render_template("/login.html", v = True)
    hash_value = user.password
    user_id = user.id
    session["username"] = username
    session["id"] = user_id
    #return the login page if password is incorrect
    if not check_password_hash(hash_value, password):
        return render_template("/login.html", v = True)
    return redirect("/")

# Handles user logout and returns the home page
@app.route("/logout")
def logout():
    del session["username"]
    del session["id"]
    return redirect("/")

# Returns the user creation page
@app.route("/create_user")
def create_user():
    return render_template("/create_user.html")

# Handles user creation and returns the account page
@app.route("/create_user2", methods = ["POST"])
def create_user2():
    file = request.files["file"]
    data = file.read()
    #optional lines for checking the uploaded file
    #name = file.filename
    #if not name.endswith(".jpg"):
        #return render_template("create_user.html", error="Virheellinen tiedosto")
    #if len(data) > 100 * 1024:
        #return render_template("create_user.html", error="Liian iso tiedosto")

    username = request.form["username"]
    password = request.form["password"]
    sql = text("SELECT id FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    #returns the user creation page if username already exists
    if user:
        return render_template("create_user.html", error="Käyttäjätunnus on jo olemassa")

    hash_value = generate_password_hash(password)
    sql = text("INSERT INTO users (username, password, data) VALUES (:username, :password, :data) RETURNING id")
    result = db.session.execute(sql, {"username": username, "password": hash_value, "data": data})
    user_id = result.fetchone()[0]
    db.session.commit()
    session["username"] = username
    session["id"] = user_id
    return redirect("/account")

#fetches all releases related to the active user and returns the account page
@app.route("/account")
def account():
    result = None
    if "id" in session:
        sql = text("SELECT id, title FROM releases WHERE user_id = :id")
        result = db.session.execute(sql, {"id":session["id"]}).fetchall()
    return render_template("/account.html", result=result)

#returns a profile picture(/pfp) or an album cover(/cover) based on given id
@app.route("/show/<string:source>/<int:id>")
def show(source, id):
    if source == "pfp":
        sql = text("SELECT data FROM users WHERE id = :id")
    elif source == "cover":
        sql = text("SELECT cover FROM releases WHERE id = :id")
    result = db.session.execute(sql, {"id":id})
    data = result.fetchone()[0]
    response = make_response(bytes(data))
    response.headers.set("Content-Type", "image/jpeg")
    return response

#updates users profile picture
@app.route("/change_pfp", methods = ["POST"])
def change_pfp():
    file = request.files["file"]
    data = file.read()
    user_id = session["id"]
    sql = text("UPDATE users SET data = :data WHERE id = :user_id")
    db.session.execute(sql, {"data": data, "user_id": user_id})
    db.session.commit()
    return redirect("/account")

#returns the upload page
@app.route("/upload")
def upload():
    return render_template("/upload.html")

#handles the upload process and returns the page of that release
@app.route("/upload2", methods = ["POST"])
def upload2():
    genre = request.form["genre"]
    title = request.form["title"]
    file = request.files["file"]
    cover = request.files["cover"]
    data = file.read()
    cover = cover.read()
    user_id = session["id"]
    sql = text("""INSERT INTO releases(user_id, title, genre, data, cover)
               VALUES (:user_id, :title, :genre, :data, :cover) RETURNING id""")
    result = db.session.execute(sql, {"user_id": user_id, "title": title, "genre": genre, "data": data, "cover":cover})
    db.session.commit()
    return redirect(f"/release/{result.fetchone()[0]}")

#returns the audio file
@app.route("/audio/<int:id>")
def audio(id):
    print(id)
    sql = text("SELECT data FROM releases WHERE id = :id")
    result = db.session.execute(sql, {"id":id})
    data = result.fetchone()[0]
    response = make_response(bytes(data))
    response.headers.set("Content-Type", "audio/mp3")
    return response

#fetches all data related to the given release and returns its page
@app.route("/release/<int:id>")
def release(id):
    sql = text("""SELECT R.user_id AS user_id, R.title AS title, R.genre AS genre, U.username AS username
               FROM releases R, users U WHERE R.id = :id AND R.user_id = U.id""")
    release_data = db.session.execute(sql, {"id":id})
    release_data = release_data.fetchone()
    sql = text("""SELECT R.content as content, R.sent_at as sent_at, R.user_id as id, U.username as username
               FROM reviews R, users U WHERE R.release_id = :id AND R.user_id = U.id""")
    reviews = db.session.execute(sql, {"id":id})
    reviews = reviews.fetchall()
    sql = text(f"SELECT AVG(rating) FROM ratings WHERE release_id = {id}")
    ratings = db.session.execute(sql)
    #checks if the release has been rated yet
    try:
        ratings = int(ratings.fetchone()[0])
    except TypeError:
        ratings = "Ei pisteytyksiä"
    return render_template("/release.html", id=id, title=release_data.title, genre=release_data.genre, user=release_data.username, reviews=reviews, ratings=ratings)

#adds the new review to the database
@app.route("/review/<int:id>", methods = ["POST"])
def review(id):
    content = request.form["message"]
    sql = text("SELECT id FROM reviews WHERE user_id = :user_id AND release_id = :id")
    check = db.session.execute(sql, {"user_id":session["id"], "id":id})
    if check.fetchone():
        #deletes the old review
        sql = text("DELETE FROM reviews WHERE user_id = :user_id AND release_id = :id")
        db.session.execute(sql, {"user_id":session["id"], "id":id})
    sql = text("INSERT INTO reviews (content, user_id, release_id) VALUES (:content, :user_id, :release_id)")
    db.session.execute(sql, {"content":content, "user_id":session["id"], "release_id":id})
    db.session.commit()
    return redirect(f"/release/{id}")

#adds new rating to the database
@app.route("/rate/<int:id>", methods = ["POST"])
def rating(id):
    sql = text("SELECT id FROM ratings WHERE user_id = :user_id AND release_id = :id")
    check = db.session.execute(sql, {"user_id":session["id"], "id":id})
    if check.fetchone():
        sql = text("UPDATE ratings SET rating = :rating WHERE user_id = :user_id AND release_id = :release_id")
    else:
        sql = text("INSERT INTO ratings (rating, user_id, release_id) VALUES (:rating, :user_id, :release_id)")
    rating = request.form["rating"]
    db.session.execute(sql, {"rating":rating, "user_id":session["id"], "release_id":id})
    db.session.commit()
    return redirect(f"/release/{id}")

#returns the page with all releases sorted by id
@app.route("/releases")
def releases_null():
    return redirect("/releases/id")

#returns the page with all releases sorted by given parameter
@app.route("/releases/<string:order>")
def releases(order):
    order = order.replace("_", " ")
    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               WHERE RA.rating IS NOT NULL GROUP BY R.id, U.username, R.title ORDER BY {order}""")
    releases_data = db.session.execute(sql)
    return render_template("/releases.html", data=releases_data)