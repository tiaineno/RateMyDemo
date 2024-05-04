from app import app
from flask import redirect, render_template, request, session, abort
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
        return render_template("login.html") 
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("login.html", error="Väärä käyttäjätunnus tai salasana")
        
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

        if len(username)>25:
            return render_template("create_user.html", error="Liian pitkä käyttäjätunnus!")
        if len(password)>100:
            return render_template("create_user.html", error="Liian pitkä käyttäjätunnus!")
        
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
    releases = data.own_releases(3, "id", "DESC")
    likes = data.likes()
    return render_template("/account.html", result=releases, likes=likes)

#returns a profile picture(/pfp) or an album cover(/cover) based on given id
@app.route("/show/<string:source>/<int:id>")
def show(source, id):
    return data.pic(source, id)

#updates users profile picture
@app.route("/change_pfp", methods = ["POST"])
def change_pfp():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    file = request.files["file"]
    name = file.filename
    if not name.endswith((".jpg", ".png", ".jpeg")):
        return render_template("/upload.html", error="Kuvan täytyy olla jpg tai png muodossa!")
    d = file.read()
    if len(d) > 10000*1024:
        return render_template("/upload.html", error="Liian suuri kuvatiedosto!")
    users.change_pfp(d)
    return redirect("/account")

#returns the uploading page or handles the upload process and returns the page of that release
@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("/upload.html")

    if request.method == "POST":
        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        genre = request.form["genre"]
        title = request.form["title"]
        file = request.files["file"]
        cover = request.files["cover"]

        name = cover.filename
        if not name.endswith((".jpg", ".png", ".jpeg")):
            return render_template("/upload.html", error="Kuvan täytyy olla jpg tai png muodossa!")
        cover = cover.read()
        if len(cover) > 10000*1024:
            return render_template("/upload.html", error="Liian suuri kuvatiedosto!")
        
        name = file.filename
        if not name.endswith((".mp3", ".wav")):
            return render_template("/upload.html", error="Äänitiedoston täytyy olla mp3 tai wav muodossa!")
        file = file.read()
        print(len(file))
        if len(file) > 10**8:
            return render_template("upload.html", error="Liian suuri äänitiedosto! Maksimi on 100MB!")
        
        if not title:
            return render_template("/upload.html", error="Syötä julkaisun nimi")

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
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    content = request.form["message"]
    if len(content) > 100000 or len(content) == 0:
        return render_template(f"/release/{id}", error="Arvostelun täytyy olla 1-99999 merkkiä pitkä!")
    data.review(content, id)
    return redirect(f"/release/{id}")

#adds new rating to the database
@app.route("/rate/<int:id>", methods = ["POST"])
def rating(id):
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
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

#redirects user to the correct page after search
@app.route("/search", methods = ["POST"])
def search():
    query = request.form["query"]
    if len(query) > 10000:
        return ("Liian pitkä hakutermi :(")
    return redirect(f"/releases/{query}/id")

#returns the result of the search
@app.route("/releases/<string:query>/<string:order>")
def search_releases(query, order):
    order = order.split("_")
    print(order)
    if len(order) < 2:
        order = [order[0], None]
    releases_data = data.search(query, order[0], order[1])
    return render_template("/search.html", data=releases_data, query=query)

#return a page with users own reviews
@app.route("/account/reviews/")
def reviews():
    reviews_data = None
    if "id" in session:
        user_id = session["id"]
        reviews_data = data.reviews2(user_id)
    return render_template("/reviews.html", reviews=reviews_data)

#delete review if user is privileged to do that
@app.route("/delete_review/", methods = ["POST"])
def delete_review():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    review_id = request.form["id"]
    path = request.form["path"]
    if not data.delete_review(review_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    return redirect(path)

#delete release if user is privileged to do that
@app.route("/delete_release/", methods = ["POST"])
def delete_release():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    release_id = request.form["id"]
    path = request.form["path"]
    if not data.delete_release(release_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    return redirect(path)

#delete account if user is privileged to do that
@app.route("/delete_account/", methods = ["POST"])
def delete_account():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    user_id = request.form["id"]
    if session["id"] != int(user_id):
        return "Sinulla ei ole oikeutta tehdä tätä!"
    users.delete_account(user_id)
    return redirect("/")

#like or unlike release
@app.route("/like", methods = ["POST"])
def like():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    release_id = request.form["id"]
    url = request.form["url"]
    data.like(release_id)
    return redirect(url)

#redirect
@app.route("/library/")
def library_null():
    return redirect("/library/L.id")

#show releases liked by user
@app.route("/library/<string:order>")
def library(order):
    if "id" not in session:
        return render_template("/library.html")
    order = order.split("_")
    if len(order) < 2:
        order = (order[0], None)
    likes = data.likes(999, order[0], order[1])
    return render_template("/library.html", likes=likes)

#redirect
@app.route("/own_releases/")
def own_releases_null():
    return redirect("/own_releases/id_desc")

#return a page with releases uploaded by the user
@app.route("/own_releases/<string:order>")
def own_releases(order):
    if "id" not in session:
        return render_template("/library.html")
    order = order.split("_")
    if len(order) < 2:
        order = (order[0], None)
    releases = data.own_releases(999, order[0], order[1])
    return render_template("/own_releases.html", releases=releases)