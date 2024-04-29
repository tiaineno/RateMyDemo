from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv
import psycopg2
from dotenv import load_dotenv
load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://"
db = SQLAlchemy(app)