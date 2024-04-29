from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv
import psycopg2
from dotenv import load_dotenv
load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL").replace("://", "ql://", 1)
db = SQLAlchemy(app)