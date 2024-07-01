# model.py
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

db = SQLAlchemy()

# Define a User model
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email =db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    bio = db.Column(db.String(50))
    profile_picture = db.Column(db.String(250))
    posts = db.relationship('Post', backref='author', lazy=True)
    
    comments = db.relationship('Comment', backref='author', lazy=True)
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.is_active
    
    def __repr__(self):
        return '<User %r>' % self.username



# Define a Post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text())
    content = db.Column(db.Text())
    tag = db.Column(db.Text(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_date = db.Column(db.DateTime,default=datetime.datetime.now)
    likes = db.Column(db.Integer, default=0)
    meta = db.Column(db.Text, nullable=True) 
    comments = db.relationship('Comment', backref='post',cascade="all, delete", lazy=True)
     
    def __repr__(self):
        return f"Post(title='{self.title}', meta='{self.meta}')"
    
    @property
    def formatted_month_and_year(self):
        return self.created_date.strftime("%d/%m/%Y")
    
#define a comment model  
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    