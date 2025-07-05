import os
from flask import Flask
from app.server import setup_routes
from app.bot import run_bot

app = Flask(__name__)
setup_routes(app)     
run_bot()             

if __name__ == '__main__':
    app.run()
