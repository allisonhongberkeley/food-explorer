import os
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
import pymongo
import bcrypt 
from helper import login_required, find
import json 

load_dotenv() 
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


client = pymongo.MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@travel-app.kfdzca6.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('users')
users = db.authentication

@app.route('/')
def index(): 
    if 'username' in session:
        return render_template("index.html", message=session["username"])
    return render_template("/login.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_user = users.find_one({'name' : request.form['username']})
        if login_user:
            if bcrypt.hashpw(request.form['password'].encode("utf-8"), login_user['password']) == login_user["password"]:
                session["username"] = request.form["username"]
                return render_template("index.html", message=session["username"])
            return 'Invalid password'
        else:
            return 'Invalid username'

    return render_template("/login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashed = bcrypt.hashpw(request.form["password"].encode("utf-8"), bcrypt.gensalt())
            users.insert_one({'name': request.form["username"], 'password': hashed, 'wishlist': [], 'favorites': []})
            return redirect(url_for('login'))
        return 'Username is already is database'
    return render_template("/register.html")

@app.route('/wishlist', methods=["GET", "POST"])
@login_required
def wishlist():
    if request.method == "POST":
        added = request.form['added']
        new_item = parse_req(added)
        users.find_one_and_update({'name': session['username']}, {'$addToSet': {'wishlist': new_item}})
    wishlist_array = users.find_one({'name' : session['username']})['wishlist']
    return render_template('/wishlist.html', wishlist_array=wishlist_array)

@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    #idea: change categories to be a scrollable dropdown select menu
    if request.method == "POST":
        location = request.form.get("location")
        categories = request.form.get("categories")
        categories = categories.split("✘ ")
        categories = "✘ ".join(categories).replace(" ", "").lower()
        category_file = open("restaurant-categories.json")
        category_file = json.load(category_file)
        #for category in categories:
            #find_alias = data[]
        price = request.form.get("price") 
        p_range = range(1, int(price) + 1)
        p_range = [str(i) for i in p_range]
        price_range = ", ".join(p_range)
        results = find(location, categories, price_range)
        return render_template("/search_results.html", location=location, categories=categories, results=results)
    return render_template('/search.html')

@app.route('/remove_wish', methods=["GET", "POST"])
@login_required
def remove():
    if request.method == "POST": 
        removed = request.form['removed']
        new_item = parse_req(removed)
        users.find_one_and_update({'name': session['username']}, {'$pull': {'wishlist': new_item}})
    return redirect('/wishlist')

@app.route('/remove_fav', methods=["GET", "POST"])
@login_required
def remove_fav():
    if request.method == "POST": 
        removed = request.form['removed']
        new_item = parse_req(removed)
        users.find_one_and_update({'name': session['username']}, {'$pull': {'favorites': new_item}})
    return redirect('/favorite')

@app.route('/favorite', methods=["GET", "POST"])
@login_required
def favorite():
    if request.method == "POST":
        liked = request.form['liked']
        new_item = parse_req(liked)
        users.find_one_and_update({'name': session['username']}, {'$addToSet': {'favorites': new_item}})
    favorites_array = users.find_one({'name' : session['username']})['favorites']
    return render_template('/favorites.html', favorites=favorites_array)

def parse_req(input):
    input = input.split("✘ ")
    keys = ["name", "rating", "price", "category", "website", "image", "address"]
    new_item = dict(zip(keys, input))
    return new_item

@app.route('/logout')
def logout():
    session.clear()
    return render_template("/login.html")

if __name__ == "__main__":
    app.run(debug=True)