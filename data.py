from sqlalchemy.sql import text
from db import db
from flask import make_response, session

def releases(limit, order, order2=""):
    if order not in ("id", "rating", "title"):
        order = "id"
    if order2 not in ("ASC", "DESC", "asc", "desc"):
        order2 = ""
    
    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title, R.uploaded_at as date
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               GROUP BY R.id, U.username, R.title ORDER BY {order} {order2} NULLS LAST LIMIT :limit""")
    releases_data = db.session.execute(sql, {"limit":limit})
    return releases_data

def own_releases(limit, order, order2=""):
    if order not in ("id", "rating", "title"):
        order = "id"
    if order2 not in ("ASC", "DESC", "asc", "desc"):
        order2 = ""

    sql = text(f"""SELECT AVG(RA.rating) as rating, R.id as id, R.title as title, R.uploaded_at as date
               FROM releases R LEFT JOIN ratings RA ON RA.release_id=R.id WHERE R.user_id = :id
               GROUP BY R.id, R.title ORDER BY {order} {order2} NULLS LAST LIMIT :limit""")
    releases_data = db.session.execute(sql, {"id":session["id"], "limit":limit})
    return releases_data.fetchall()

def release(id):
    sql = text("""SELECT R.user_id AS user_id, R.title AS title, R.genre AS genre, R.uploaded_at AS date, U.username AS username
               FROM releases R, users U WHERE R.id = :id AND R.user_id = U.id""")
    release_data = db.session.execute(sql, {"id":id})
    release_data = release_data.fetchone()
    return release_data

def ratings(id):
    sql = text(f"SELECT AVG(rating) FROM ratings WHERE release_id = :id")
    ratings = db.session.execute(sql, {"id": id})
    try:
        return ratings.fetchone()[0]
    except TypeError:
        return None

def own_rating(id):
    if "id" not in session:
        return None
    sql = text("SELECT rating FROM ratings WHERE release_id = :id AND user_id = :user_id")
    try:
        return db.session.execute(sql, {"id": id, "user_id": session["id"]}).fetchone()[0]
    except TypeError:
        return None

def reviews(release_id, user_id):
    sql = text(f"""SELECT R.content as content, R.sent_at as sent_at, R.user_id as id, U.username as username
               FROM reviews R, users U WHERE R.release_id = :id AND R.user_id = U.id AND R.user_id <> :user_id""")
    reviews = db.session.execute(sql, {"id":release_id, "user_id":user_id})
    reviews = reviews.fetchall()
    review = None
    if user_id:
        sql = text(f"""SELECT R.content as content, R.sent_at as sent_at, R.id as id
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
    user_id = session["id"]
    sql = text("UPDATE users SET data = :data WHERE id = :user_id")
    db.session.execute(sql, {"data": file, "user_id": user_id})
    db.session.commit()

def upload(file, cover, title, genre):
    data = file.read()
    user_id = session["id"]
    sql = text("""INSERT INTO releases(user_id, title, genre, data, cover, uploaded_at)
               VALUES (:user_id, :title, :genre, :data, :cover, NOW()) RETURNING id""")
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
    sql = text("INSERT INTO reviews (content, user_id, release_id, sent_at) VALUES (:content, :user_id, :release_id, NOW())")
    db.session.execute(sql, {"content":content, "user_id":session["id"], "release_id":id})
    db.session.commit()

def delete_review(id):
    sql = text("SELECT user_id FROM reviews WHERE id = :id")
    user_id = db.session.execute(sql, {"id": id}).fetchone()[0]
    if user_id != session["id"]:
        return False
    sql = text("DELETE FROM reviews WHERE id = :id")
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return True

def rate(id, rating):
    sql = text("SELECT id FROM ratings WHERE user_id = :user_id AND release_id = :id")
    check = db.session.execute(sql, {"user_id":session["id"], "id":id})
    if check.fetchone():
        sql = text("UPDATE ratings SET rating = :rating WHERE user_id = :user_id AND release_id = :release_id")
    else:
        sql = text("INSERT INTO ratings (rating, user_id, release_id) VALUES (:rating, :user_id, :release_id)")
    db.session.execute(sql, {"rating":rating, "user_id":session["id"], "release_id":id})
    db.session.commit()

def search(query, order="id", order2=""):
    if order not in ("id", "rating", "title"):
        order = "id"
    if order2 not in ("ASC", "DESC", "asc", "desc"):
        order2 = ""
    print(order, order2)
    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title
               FROM releases R LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id
               WHERE (title ILIKE :q OR username ILIKE :q) GROUP BY R.id, U.username, R.title ORDER BY {order} {order2}""")
    query = f"%{query}%"
    release_data = db.session.execute(sql, {"q":query})
    return release_data

def delete_release(id):
    sql = text("SELECT user_id FROM releases WHERE id = :id")
    user_id = db.session.execute(sql, {"id": id}).fetchone()[0]
    if user_id != session["id"]:
        return False
    sql = text(f"""DELETE FROM releases WHERE id = :id""")
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return True

def delete_account(id):
    sql = text("DELETE FROM users WHERE id = :id")
    db.session.execute(sql, {"id": id})
    del session["username"]
    del session["id"]
    db.session.commit()

def likes_count(id):
    sql = text("SELECT COUNT(id) FROM likes WHERE release_id = :id")
    result = db.session.execute(sql, {"id": id})
    return result.fetchone()[0]

def like(id):
    sql = text("SELECT COUNT(id) FROM likes WHERE release_id = :id AND user_id = :user_id")
    result = db.session.execute(sql, {"id": id, "user_id": session["id"]}).fetchone()[0]
    if result:
        sql = text("DELETE FROM likes WHERE user_id = :user_id AND release_id = :id")
    else:
        sql = text("INSERT INTO likes (user_id, release_id) VALUES (:user_id, :id)")
    db.session.execute(sql, {"user_id": session["id"], "id": id})
    db.session.commit()

def likes(limit=3, order="L.id", order2="DESC"):
    if order not in ("id", "rating", "title", "L.id"):
        order = "id"
    if order2 not in ("ASC", "DESC", "asc", "desc"):
        order2 = ""

    sql = text(f"""SELECT AVG(RA.rating) as rating, U.username as username, R.id as id, R.title as title,
               R.uploaded_at as date FROM likes L LEFT JOIN releases R ON L.release_id = R.id
               LEFT JOIN users U ON R.user_id = U.id LEFT JOIN ratings RA ON RA.release_id=R.id WHERE L.user_id = :user_id
               GROUP BY R.id, U.username, R.title, L.id ORDER BY {order} {order2} NULLS LAST LIMIT :limit""")
    result = db.session.execute(sql, {"user_id":session["id"], "limit": limit})
    return result.fetchall()

def liked(id):
    sql = text("SELECT COUNT(*) FROM likes WHERE release_id = :id AND user_id = :user_id")
    result = db.session.execute(sql, {"id": id, "user_id": session["id"]})
    if result.fetchone()[0]:
        return True
    return False