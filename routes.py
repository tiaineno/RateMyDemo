from app import app
from flask import redirect, render_template, request, session
import data, users

#returns the home page
@app.route("/")
def index():
    most_popular = data.releases("rating DESC", 3)
    most_recent = data.releases("id DESC", 3)
    return render_template("index.html", releases=most_recent, most_popular=most_popular)

#returns the login page or handles the user login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", v = False) 
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("login.html", v = True)
        
# Handles user logout and returns the home page
@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")

#returns the user creation page or handles the user creation process
@app.route("/create_user", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("create_user.html")
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        file = request.form["file"]

        if users.register(username, password, file):
            return redirect("/account")
        else:
            return render_template("create_user.html", error="Käyttäjätunnus on jo olemassa")
        
#returns the account page
@app.route("/account")
def account():
    id = None
    if "id" in session:
        id = session["id"]
    result = data.releases("id", 3, f"AND R.user_id = :id", id)
    return render_template("/account.html", result=result)

#returns a profile picture(/pfp) or an album cover(/cover) based on given id
@app.route("/show/<string:source>/<int:id>")
def show(source, id):
    return data.pic(source, id)

#updates users profile picture
@app.route("/change_pfp", methods = ["POST"])
def change_pfp():
    file = request.files["file"]
    data.change_pfp(file)
    return redirect("/account")

#returns the uploading page or handles the upload process and returns the page of that release
@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("/upload.html")

    if request.method == "POST":
        genre = request.form["genre"]
        title = request.form["title"]
        file = request.files["file"]
        cover = request.files["cover"]
        #TODO: tarkista lataus
            #return render_template("/upload", error=True)
        result = data.upload(file, cover, title, genre)
        return redirect(f"/release/{result.fetchone()[0]}")

#returns the audio file
@app.route("/audio/<int:id>")
def audio(id):
    file = data.audio(id)
    return file

#fetches all data related to the given release and returns its page
@app.route("/release/<int:id>")
def release(id):
    release_data = data.release(id)
    reviews = data.reviews("R.release_id",id)
    ratings = data.ratings(id)
    return render_template("/release.html", id=id, title=release_data.title, genre=release_data.genre, user=release_data.username, reviews=reviews, ratings=ratings)

#adds the new review to the database
@app.route("/review/<int:id>", methods = ["POST"])
def review(id):
    content = request.form["message"]
    data.review(content, id)
    return redirect(f"/release/{id}")

#adds new rating to the database
@app.route("/rate/<int:id>", methods = ["POST"])
def rating(id):
    rating = request.form["rating"]
    data.rate(id, rating)
    return redirect(f"/release/{id}")

#returns the page with all releases sorted by id
@app.route("/releases")
def releases_null():
    return redirect("/releases/id")

#returns the page with all releases sorted by given parameter
@app.route("/releases/<string:order>")
def releases(order):
    order = order.replace("_", " ")
    releases_data = data.releases(order, 1000000)
    return render_template("/releases.html", data=releases_data)