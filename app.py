from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_required, LoginManager, logout_user, UserMixin, login_user
import os
from werkzeug.utils import secure_filename
import base64
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clients.db'
app.config['SECRET_KEY'] = 'your_secret_key'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)




class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image = db.Column(db.LargeBinary, nullable=True)

#User model for the Database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    second_name = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.Integer, nullable=False, unique=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    confirm_password = db.Column(db.String(60), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def base64_encode(data):
    return base64.b64encode(data).decode('utf-8')

app.jinja_env.filters['base64_encode'] = base64_encode

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        with open(filepath, "rb") as image_file:
            return image_file.read()
    return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/home')
@login_required
def index():
    user = current_user
    menu_items = MenuItem.query.all()

    if 'image' in request.files:
            menu_items.image = save_image(request.files['image'])

    return render_template("index.html", user=user, menu_items=menu_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.json.get('itemId')
    item = MenuItem.query.get_or_404(item_id)

    cart_items = session.get('cart_items', [])
    cart_items.append(item.name)
    session['cart_items'] = cart_items

    total_quantity = len(cart_items)
    return jsonify({'total_quantity': total_quantity})

@app.route('/cart')
def cart():
    cart_items = session.get('cart_items', [])
    menu_items = MenuItem.query.filter(MenuItem.name.in_(cart_items)).all()
    
    total_price = sum(item.price for item in menu_items)

    return render_template('cart.html', menu_items=menu_items, total_price=total_price)

@app.route('/checkout')
def checkout():
    cart_items = session.pop('cart_items', [])
    return render_template('checkout.html', cart_items=cart_items)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def landPage():
    return render_template("landing-page.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        second_name = request.form['second_name']
        phone_no = request.form['phone_no']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match. Please enter matching passwords.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username,
                        password=hashed_password,
                        first_name=first_name,
                        second_name=second_name,
                        phone_no=phone_no,
                        email=email,
                        confirm_password=confirm_password,
                        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            flash('Email address is already in use. Please try another one', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', user=user)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('landPage'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route('/admin')
def admin():
    menu_items = MenuItem.query.all()
    return render_template('admin.html', menu_items=menu_items)

@app.route('/admin/add', methods=['POST'])
def add_menu_item():
    name = request.form['name']
    price = float(request.form['price'])
    description = request.form['description']

    new_item = MenuItem(name=name, price=price, description=description)

    if 'image' in request.files:
        new_item.image = save_image(request.files['image'])

    db.session.add(new_item)
    db.session.commit()

    return redirect(url_for('admin'))


@app.route('/admin/delete/<int:item_id>')
def delete_menu_item(item_id):
    item_to_delete = MenuItem.query.get_or_404(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()

    return redirect(url_for('admin'))

@app.route('/admin/update/<int:item_id>', methods=['GET', 'POST'])
def update_menu_item(item_id):
    item_to_update = MenuItem.query.get_or_404(item_id)

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']

        item_to_update.name = name
        item_to_update.price = price
        item_to_update.description = description

        if 'image' in request.files:
            item_to_update.image = save_image(request.files['image'])

        db.session.commit()

        return redirect(url_for('admin'))

    return render_template('update.html', item=item_to_update)