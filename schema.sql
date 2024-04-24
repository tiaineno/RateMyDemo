CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    data bytea
);

CREATE TABLE releases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    title TEXT,
    genre TEXT,
    cover BYTEA,
    data BYTEA
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    release_id INTEGER REFERENCES releases,
    content TEXT,
    sent_at TIMESTAMP
);

CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    release_id INTEGER REFERENCES releases,
    rating INTEGER
);