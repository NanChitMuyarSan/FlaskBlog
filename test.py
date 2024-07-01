# app.py
import datetime
from flask import Flask, abort, render_template, redirect, url_for, request, flash ,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import DateField, StringField, PasswordField, SubmitField, validators,TextAreaField,EmailField,FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import UnmappedInstanceError
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired





#app config
app = Flask(__name__,static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = 'static/photo/user_profile'

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'miapn3071@gmail.com'
app.config['MAIL_PASSWORD'] = 'omhp jujn vcdc yqty'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
s = URLSafeTimedSerializer('Thisisasecret!')

#log in config
login_manager = LoginManager()
login_manager.init_app(app)

#db config
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine) 
session = Session() 
db = SQLAlchemy(app)
Base = declarative_base()

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
    tag = db.Column(db.Text())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_date = db.Column(db.DateTime,default=datetime.datetime.now)
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post',cascade="all, delete", lazy=True)
     
    def __repr__(self):
        return '<Post %r>' % self.title
#define a comment model  
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class ProfileForm(FlaskForm):
  profile_picture = FileField('Profile Picture', validators=[DataRequired()])
  submit = SubmitField('Upload')
# Define a form for user Post
class PostForm(FlaskForm):
  title = StringField('Title', validators=[DataRequired(), Length(min=3, max=50)])  
  content = TextAreaField('Content', validators=[DataRequired()])  
  tag = TextAreaField('Tag', validators=[DataRequired()])
  submit = SubmitField('Post')

# Define a form for user login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.InputRequired()])
    password = PasswordField('Password', validators=[validators.InputRequired()])
    submit = SubmitField('Login')

# Define a form for user signup
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[validators.InputRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

#confirm mail form
class commailForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset Link')

#reset form
class resetpwForm(FlaskForm):
    npass = PasswordField('Password', validators=[validators.InputRequired()])
    cpass = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')

#search form
class SearchForm(FlaskForm):
    search = StringField('Search ', validators=[DataRequired()])
    submit = SubmitField('Search')

#comment form
class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class DateFilterForm(FlaskForm):
    created_date = DateField('Created Date')
    submit = SubmitField('Filter')

# define a form for profile upload
class PictureUpdate(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[validators.InputRequired()])
    submit = SubmitField('Update')


#LOGIN MANAGER
@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)

#pagination
# Function to get paginated posts
def get_posts(page, per_page):
    return Post.query.paginate(page=page, per_page=per_page, error_out=False)

# Routes

#profile route
@app.route('/profile/user_?<int:user_id>')
def profile(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of posts per page
    user = User.query.get_or_404(user_id)
    user_posts = Post.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page)
    picture_url=get_profile_profile(user_id)
    return render_template('profile.html', user_id=user_id,user=user,picture_url=picture_url,user_posts=user_posts)


@app.route('/profile/upload', methods=['GET', 'POST'])
def profile_upload():
    form = ProfileForm()
    if form.validate_on_submit():
        # Get uploaded file
        uploaded_file = form.profile_picture.data
        if uploaded_file and allowed_file(uploaded_file.filename):
            # Secure filename and save to upload folder
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)
            # Update user profile picture in database
            current_user.profile_picture = filename
            db.session.commit()
            flash('Profile picture uploaded successfully!', 'success')
            return redirect(url_for('profile',user_id=current_user.id))
    return render_template('profile_upload.html', form=form)

def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_profile_profile(user_id):
    cwd = os.getcwd()
    
    
    user = User.query.get_or_404(user_id)
    if user:
        # Construct the URL to the profile picture
        
        picture_url = f"/photo/user_profile/{user.profile_picture}"
        return picture_url

    
    
#user profile for home page
def get_profile_home():
    post=Post()
    user = post.user_id
    cwd = os.getcwd()
    
    user = User.query.filter_by(id=user).first()
    if user:
        # Construct the URL to the profile picture
        
        picture_url = f"/photo/user_profile/{user.profile_picture}"
        u=user.profile_picture
        return u
    
def get_posts(page, per_page, tag=None):
    if tag:
        return Post.query.filter(Post.tag == tag).paginate(page=page, per_page=per_page, error_out=False)
    return Post.query.paginate(page=page, per_page=per_page, error_out=False)   
    
#home route
@app.route('/home',methods=['GET', 'POST'])

def home(limit=3):
    post=Post()
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of posts per page
    post = get_posts(page, per_page)  # Assuming you have a function to get paginated posts
    
    # #for update posts
    # date_form = DateFilterForm()
    
     # Query all unique tags associated with posts
    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))

     # get 5 popular post by like count
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()


    #for searching posts
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' ,post=post, search_results =search_results ,form = forms , tags=unique_tags ,popular_posts = popular_posts) # or what you wanto
    
    # elif date_form.validate_on_submit():
    #     created_date = date_form.created_date.data
    #     date_posts = Post.query.filter(db.func.date(Post.created_at) == created_date.date()).all()
    # else:
    #     date_posts = Post.query.all()
    
   

    return render_template("home.html", post=post ,form=forms , tags=unique_tags ,popular_posts = popular_posts)

@app.route('/home/<string:tag>', methods=['GET', 'POST'])
def home_tag(tag,limit=3):
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Number of posts per page
    
    posts_with_tag = get_posts(page, per_page, tag=tag)
    
     # Query all unique tags associated with posts
    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    return render_template('home.html', post=posts_with_tag, tags=unique_tags , form = form ,popular_posts=popular_posts)


#search_result route
@app.route('/search_result',methods=['GET', 'POST'])

def search_result(limit=3):
     forms=SearchForm()
     query = forms.search.data
     unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))

     # get 5 popular post by like count
     popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

     if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' , search_results =search_results , tags=unique_tags ,popular_posts = popular_posts) # or what you wanto
     
    


     return render_template("search_results.html", post=post ,form=forms, tags=unique_tags ,popular_posts = popular_posts)




#index route                                         
@app.route('/')
def index():
    return render_template('index.html')


#nav route
@app.route('/nav',methods=['GET', 'POST'])
def nav():

    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
        search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
        return render_template('search_results.html' , search_results =search_results, form = forms) # or what you wanto
    return render_template('nav.html',form=forms)


@app.route('/post',methods=['GET', 'POST'])
def post():
      if request.method == 'POST':
        author=current_user
        title = request.form.get('title')
        content = request.form.get('content')
        tag = ','.join(request.form.getlist('dynamicFields[]'))
        new_post = Post(title=title,content=content,tag=tag,author=author)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
      return render_template('post.html')

@app.route('/post/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    flash('Post liked!', 'success')
    return redirect(request.referrer)

@app.route('/post/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'success')
    return redirect(url_for('home'))

#login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            login_flag=True
            return redirect(url_for('nav'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html', form=form)

#logout route
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

#comfirmationemail route
@app.route('/commail',methods=['GET', 'POST'])
def commail():
    form = commailForm()
    if  form.validate_on_submit():
        email = form.email.data
        token = s.dumps(email, salt='email-confirm')
        msg = Message('Confirm Email', sender='miapn3071@gmail.com', recipients=[email])
        link = url_for('confirm_email', token=token, _external=True)
        msg.body = 'Your link is {}'.format(link)
        mail.send(msg)
       # return '<h1>Successful</h1>'.format(email, token)
    return render_template('commail.html',form=form)

#rest password route
@app.route('/resetpw/<token>',methods=['GET', 'POST'])
def confirm_email(token):
    reset_form = resetpwForm()
    email = s.loads(token, salt='email-confirm', max_age=3600)
    # existing_user = User.query.filter_by(email=email).first()
    if reset_form.validate_on_submit():
        npass = reset_form.npass.data
        cpass = reset_form.cpass.data
        if npass==cpass:
            existing_user = User.query.filter_by(email=email).first()
            existing_user.password = npass
            db.session.commit()
            # return render_template('test.html',existing_user = existing_user)
            return redirect(url_for('login'))
    return render_template('resetpw.html',reset_form = reset_form)




#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, email=email,password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

#full_post route
@app.route("/full_post/<int:post_id>",methods=['GET', 'POST'])
def full_post(post_id,limit=3):
    post = Post.query.get_or_404(post_id)

     # Query all unique tags associated with posts
    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))

     # get 5 popular post by like count
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    comment_form = CommentForm()
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' , form=forms,search_results =search_results, tags=unique_tags ,popular_posts = popular_posts)
    elif comment_form.validate_on_submit():
        comment = Comment(content=comment_form.content.data, post=post, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added!', 'success')
        return render_template('full_post.html', post=post ,comment_form = comment_form , form = forms, tags=unique_tags ,popular_posts = popular_posts)
    
    return render_template('full_post.html', post=post ,comment_form = comment_form , form = forms, tags=unique_tags ,popular_posts = popular_posts )
    
@app.route("/edit_post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('home', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit_post.html', form=form, post=post)


@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    picture_url = get_profile_profile(current_user.id)
    user=current_user
    form = PictureUpdate()
    bio = current_user.bio
    if request.method == 'POST':
        bio  = request.form.get('bio')
        uploaded_file = request.files['file']
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)
            user.profile_picture = filename
        else:
            user.profile_picture = current_user.profile_picture
        user.bio = bio
        db.session.commit()
        return redirect(url_for('home',user=user))
    
    
    return render_template('profile_edit.html',form=form,user=user,picture_url=picture_url)


def create_db():
    with app.app_context():
        db.create_all()
        
if __name__ == '__main__':
    
    create_db()
    app.run(debug=True)




