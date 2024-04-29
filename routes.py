from app import app
from flask import redirect, render_template, request, session
import data, users

#returns the home page
@app.route("/")
def index():
    most_popular = data.releases(3, "rating", "desc")
    most_recent = data.releases(3, "id", "desc")
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
        file = request.files["file"]

        name = file.filename
        if not name.endswith((".jpg", ".png", ".jpeg")) and name!="":
            return render_template("/create_user.html", error="Kuvan täytyy olla jpg tai png muodossa!")
        d = file.read()
        if len(d) > 10000*1024:
            return render_template("/create_user.html", error="Liian suuri kuvatiedosto!")
        
        if users.register(username, password, d):
            return redirect("/account")
        else:
            return render_template("create_user.html", error="Käyttäjätunnus on jo olemassa")
        
#returns the account page
@app.route("/account")
def account():
    id = None
    if "id" in session:
        id = session["id"]
    releases = data.own_releases(id, 3)
    likes = data.likes()
    return render_template("/account.html", result=releases, likes=likes)

#returns a profile picture(/pfp) or an album cover(/cover) based on given id
@app.route("/show/<string:source>/<int:id>")
def show(source, id):
    return data.pic(source, id)

#updates users profile picture
@app.route("/change_pfp", methods = ["POST"])
def change_pfp():
    file = request.files["file"]
    name = file.filename
    if not name.endswith((".jpg", ".png", ".jpeg")):
        return render_template("/upload.html", error="Kuvan täytyy olla jpg tai png muodossa!")
    d = file.read()
    if len(d) > 10000*1024:
        return render_template("/upload.html", error="Liian suuri kuvatiedosto!")
    data.change_pfp(d)
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

        name = cover.filename
        if not name.endswith((".jpg", ".png", ".jpeg")):
            return render_template("/upload.html", error="Kuvan täytyy olla jpg tai png muodossa!")
        d = cover.read()
        if len(d) > 10000*1024:
            return render_template("/upload.html", error="Liian suuri kuvatiedosto!")
        
        name = file.filename
        if not name.endswith((".mp3", ".wav")):
            return render_template("/upload.html", error="Äänitiedoston täytyy olla mp3 tai wav muodossa!")
        
        if not title:
            return render_template("/upload.html", error="Syötä julkaisun nimi")

        result = data.upload(file, d, title, genre)
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
    user_id = 0
    liked = None
    if "id" in session:
        user_id = session["id"]
        liked = data.liked(id)
    likes = data.likes_count(id)
    reviews = data.reviews(id, user_id)
    review = reviews[1]
    reviews = reviews[0]
    ratings = data.ratings(id)
    rating = data.own_rating(id)
    return render_template("/release.html", id=id, title=release_data.title, genre=release_data.genre, user=release_data.username, reviews=reviews, ratings=ratings, review=review, date=release_data.date, user_id=release_data.user_id, rating=rating, liked=liked, likes=likes)

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

#returns the page with all releases sorted by rating
@app.route("/releases")
def releases_null():
    return redirect("/releases/rating_desc")

#returns the page with all releases sorted by given parameter
@app.route("/releases/<string:order>")
def releases(order):
    order = order.split("_")
    if len(order) < 2:
        order = [order[0], None]
    releases_data = data.releases(1000, order[0], order[1])
    return render_template("/releases.html", data=releases_data)


@app.route("/releases/search/", methods = ["POST"])
def search():
    query = request.form["query"]
    releases_data = data.search(query)
    return render_template("/search.html", data=releases_data)

@app.route("/account/reviews/")
def reviews():
    reviews_data = None
    if "id" in session:
        user_id = session["id"]
        reviews_data = data.reviews2(user_id)
    return render_template("/reviews.html", reviews=reviews_data)

@app.route("/delete_review/", methods = ["POST"])
def delete_review():
    review_id = request.form["id"]
    path = request.form["path"]
    if not data.delete_review(review_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    return redirect(path)

@app.route("/delete_release/", methods = ["POST"])
def delete_release():
    release_id = request.form["id"]
    path = request.form["path"]
    if not data.delete_release(release_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    return redirect(path)

@app.route("/delete_account/", methods = ["POST"])
def delete_account():
    user_id = request.form["id"]
    if session["id"] != int(user_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    data.delete_account(user_id)
    return redirect("/")

@app.route("/like", methods = ["POST"])
def like():
    release_id = request.form["id"]
    url = request.form["url"]
    data.like(release_id)
    return redirect(url)