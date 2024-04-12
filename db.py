from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from dotenv import load_dotenv
load_dotenv()
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://"
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)