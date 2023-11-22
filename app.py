from flask import Flask, render_template
from flask import redirect, url_for, abort

app = Flask(__name__)
@app.route('/')
def index():
    #abort(500)
    return render_template("index.html")

@app.route('/about')
def about_page():
    return redirect(url_for('index') + '#about')

@app.route('/menu')
def menu_page():
    return redirect(url_for('index') + '#menu')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500