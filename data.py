from sqlalchemy.sql import text
from db import db
from flask import make_response, session

def releases(limit, order, order2=""):
    if order not in ("id", "rating", "title"):
        order = "id"
    if order2 not in ("ASC", "DESC", "asc", "desc"):
        order2 = ""
    
    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               GROUP BY R.id, U.username, R.title ORDER BY {order} {order2} NULLS LAST LIMIT :limit""")
    releases_data = db.session.execute(sql, {"limit":limit})
    return releases_data

def own_releases(id, limit=999999, order="id", order2=""):
    sql = text(f"""SELECT AVG(RA.rating) as rating, R.id as id, R.title as title
               FROM releases R LEFT JOIN ratings RA ON RA.release_id=R.id WHERE R.user_id = :id
               GROUP BY R.id, R.title ORDER BY {order} {order2} NULLS LAST LIMIT :limit""")
    releases_data = db.session.execute(sql, {"id":id, "limit":limit})
    return releases_data

def release(id):
    sql = text("""SELECT R.user_id AS user_id, R.title AS title, R.genre AS genre, U.username AS username
               FROM releases R, users U WHERE R.id = :id AND R.user_id = U.id""")
    release_data = db.session.execute(sql, {"id":id})
    release_data = release_data.fetchone()
    return release_data

def ratings(id):
    sql = text(f"SELECT AVG(rating) FROM ratings WHERE release_id = {id}")
    ratings = db.session.execute(sql)
    try:
        ratings = int(ratings.fetchone()[0])
    except TypeError:
        ratings = "Ei pisteytyksiä"
    return ratings

def reviews(release_id, user_id = None):
    sql = text(f"""SELECT R.content as content, R.sent_at as sent_at, R.user_id as id, U.username as username
               FROM reviews R, users U WHERE R.release_id = :id AND R.user_id = U.id AND R.user_id <> :user_id""")
    reviews = db.session.execute(sql, {"id":release_id, "user_id":user_id})
    reviews = reviews.fetchall()

    review = None
    if user_id:
        sql = text(f"""SELECT R.content as content, R.sent_at as sent_at
                FROM reviews R WHERE R.user_id = :user_id AND R.release_id = :release_id""")
        review = db.session.execute(sql, {"user_id":user_id, "release_id":release_id})
        review = review.fetchone()
    return (reviews,review)

def reviews2(id):
    sql = text(f"""SELECT R.content as content, R.sent_at as sent_at, R.id as review_id, R.release_id as id, Re.title as title
               FROM reviews R, releases Re WHERE R.user_id = :id AND R.release_id = Re.id""")
    reviews = db.session.execute(sql, {"id":id})
    reviews = reviews.fetchall()
    return reviews

def pic(source, id):
    if source == "pfp":
        sql = text("SELECT data FROM users WHERE id = :id")
    elif source == "cover":
        sql = text("SELECT cover FROM releases WHERE id = :id")
    result = db.session.execute(sql, {"id":id})
    data = result.fetchone()[0]
    response = make_response(bytes(data))
    response.headers.set("Content-Type", "image/jpeg")
    return response

def audio(id):
    sql = text("SELECT data FROM releases WHERE id = :id")
    result = db.session.execute(sql, {"id":id})
    data = result.fetchone()[0]
    response = make_response(bytes(data))
    response.headers.set("Content-Type", "audio/mp3")
    return response

def change_pfp(file):
    data = file.read()
    user_id = session["id"]
    sql = text("UPDATE users SET data = :data WHERE id = :user_id")
    db.session.execute(sql, {"data": data, "user_id": user_id})
    db.session.commit()

def upload(file, cover, title, genre):
    data = file.read()
    cover = cover.read()
    user_id = session["id"]
    sql = text("""INSERT INTO releases(user_id, title, genre, data, cover)
               VALUES (:user_id, :title, :genre, :data, :cover) RETURNING id""")
    result = db.session.execute(sql, {"user_id": user_id, "title": title, "genre": genre, "data": data, "cover":cover})
    db.session.commit()
    return result

def review(content, id):
    sql = text("SELECT id FROM reviews WHERE user_id = :user_id AND release_id = :id")
    check = db.session.execute(sql, {"user_id":session["id"], "id":id})
    if check.fetchone():
        #deletes the old review
        sql = text("DELETE FROM reviews WHERE user_id = :user_id AND release_id = :id")
        db.session.execute(sql, {"user_id":session["id"], "id":id})
    sql = text("INSERT INTO reviews (content, user_id, release_id) VALUES (:content, :user_id, :release_id)")
    db.session.execute(sql, {"content":content, "user_id":session["id"], "release_id":id})
    db.session.commit()

def delete_review(id):
    sql = text("DELETE FROM reviews WHERE id = :id")
    db.session.execute(sql, {"id": id})
    db.session.commit()

def rate(id, rating):
    sql = text("SELECT id FROM ratings WHERE user_id = :user_id AND release_id = :id")
    check = db.session.execute(sql, {"user_id":session["id"], "id":id})
    if check.fetchone():
        sql = text("UPDATE ratings SET rating = :rating WHERE user_id = :user_id AND release_id = :release_id")
    else:
        sql = text("INSERT INTO ratings (rating, user_id, release_id) VALUES (:rating, :user_id, :release_id)")
    db.session.execute(sql, {"rating":rating, "user_id":session["id"], "release_id":id})
    db.session.commit()

def search(query, order="id"):
    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               WHERE RA.rating IS NOT NULL AND (title ILIKE :q OR username ILIKE :q) GROUP BY R.id, U.username, R.title ORDER BY {order}""")
    query = f"%{query}%"
    release_data = db.session.execute(sql, {"q":query})
    return release_data