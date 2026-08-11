import os
import requests
from main import makeThread
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<p>Flask app is running!</p>"


@app.route("/bairsbot")
def run_bairs_bot():

   return makeThread()