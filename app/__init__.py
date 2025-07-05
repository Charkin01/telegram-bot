from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Flask работает на Beget — бот в порядке!"