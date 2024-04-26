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
    result = data.own_releases(id, 3)
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
    user_id = None
    if "id" in session:
        user_id = session["id"]
    reviews = data.reviews(id, user_id)
    review = reviews[1]
    print(review)
    reviews = reviews[0]
    ratings = data.ratings(id)
    return render_template("/release.html", id=id, title=release_data.title, genre=release_data.genre, user=release_data.username, reviews=reviews, ratings=ratings, review=review)

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
    data.delete_review(review_id)
    return redirect("/account/reviews/")