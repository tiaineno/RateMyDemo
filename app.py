#import all requires libraries
from os import getenv
from flask import Flask
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = getenv("SECRET_KEY")

import routes