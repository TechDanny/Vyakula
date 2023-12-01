from app import app, db

with app.app_context():
    #Create the tables
    db.create_all()
