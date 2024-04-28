CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    data bytea
);

CREATE TABLE releases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users ON DELETE CASCADE,
    title TEXT,
    genre TEXT,
    uploaded_at TIMESTAMP,
    cover BYTEA,
    data BYTEA
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users ON DELETE CASCADE,
    release_id INTEGER REFERENCES releases ON DELETE CASCADE,
    content TEXT,
    sent_at TIMESTAMP
);

CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users ON DELETE CASCADE,
    release_id INTEGER REFERENCES releases ON DELETE CASCADE,
    rating INTEGER
);