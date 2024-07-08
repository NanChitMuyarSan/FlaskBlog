# routes.py
from itertools import chain
import re
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from flask import Flask, session
from models import db
from forms import *
from models import *
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_login import LoginManager
from flask import abort
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import timedelta



s = URLSafeTimedSerializer('Thisisasecret!')

#app config
app = Flask(__name__,static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie_name'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = 'static/photo/user_profile'

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'miapn3071@gmail.com'
app.config['MAIL_PASSWORD'] = 'omhp jujn vcdc yqty'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = sessionmaker(bind=engine) 
session = session() 
#log in config
login_manager = LoginManager()
login_manager.init_app(app)
# Initialize database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)


mail = Mail(app)
# Routes

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
@app.route('/profile/user_?<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id,limit=2):
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of posts per page
    post = get_posts(page, per_page) 
    user = User.query.get_or_404(user_id)
    user_posts = Post.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page)
    picture_url=get_profile_profile(user_id)

    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))

     # get 5 popular post by like count
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    #for searching posts
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' ,post=post, search_results =search_results ,
                                form = forms ,tags=unique_tags,popular_posts=popular_posts)
    
    

  

    return render_template('profile.html', user_id=user_id,user=user,picture_url=picture_url,user_posts=user_posts,form=forms,post=post,tags=unique_tags,popular_posts=popular_posts)


@app.route('/profile/upload', methods=['GET', 'POST'])
@login_required
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
        return Post.query.filter(Post.tag.in_([tag])).paginate(page=page, per_page=per_page, error_out=False)
    return Post.query.order_by(Post.created_date.desc()).paginate(page=page, per_page=per_page, error_out=False)   
    
#home route
@app.route('/home',methods=['GET', 'POST'])
@login_required
def home(limit=2):
    # post=Post()
    # tags = post.tag
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of posts per page
    post = get_posts(page, per_page)  # Assuming you have a function to get paginated posts
    
    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct().limit(15)))

     # get 5 popular post by like count
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    #for searching posts
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' ,post=post, search_results =search_results ,
                                form = forms ,popular_posts = popular_posts,tags=unique_tags)
    
    return render_template("home.html", post=post ,form=forms  ,popular_posts = popular_posts,tags=unique_tags)

@app.route('/home/<string:tag>', methods=['GET', 'POST'])
@login_required
def home_tag(tag,limit=2):
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of posts per page
    
    posts_with_tag = get_posts(page, per_page, tag=tag)

    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct()))
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
        search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
        return render_template('search_results.html' ,tags=unique_tags, search_results =search_results, form = forms)

    return render_template('home.html',tags=unique_tags, post=posts_with_tag, form = forms ,popular_posts=popular_posts)


#search_result route
@app.route('/search_result',methods=['GET', 'POST'])
@login_required
def search_result(limit=2):
     forms=SearchForm()
     query = forms.search.data
    

     # get 5 popular post by like count
     popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

     if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' , search_results =search_results ,popular_posts = popular_posts) # or what you wanto
     
    


     return render_template("search_results.html", post=post ,form=forms,popular_posts = popular_posts)




#index route                                         
@app.route('/')
def frontpage():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('frontpage.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post',methods=['GET', 'POST'])
@login_required
def post():

      if request.method == 'POST':
        author=current_user
        title = request.form.get('title')
        content = request.form.get('content')
        meta_data = ' '.join(content.split()[:10])
        
    
        tag = request.form.get('dynamicFields[]')
        new_post = Post(title=title,content=content,tag=tag,author=author, meta=meta_data)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
      forms=SearchForm()
      query = forms.search.data
      if forms.validate_on_submit():
        search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
        return render_template('search_results.html' , search_results =search_results, form = forms)
      
      

      return render_template('post.html',form=forms)

@app.route('/post/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    #flash('Post liked!', 'success')
    return redirect(request.referrer)

@app.route('/post/delete/<int:post_id>', methods=['GET','POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    #flash('Post deleted!', 'success')
    return redirect(url_for('profile',user_id=current_user.id))

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
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html', form=form)

#logout route
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("frontpage"))

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
    form = resetpwForm()
    email = s.loads(token, salt='email-confirm', max_age=3600)
    # existing_user = User.query.filter_by(email=email).first()
    if form.validate_on_submit():
        npass = form.npass.data
        cpass = form.cpass.data
        if npass==cpass:
            existing_user = User.query.filter_by(email=email).first()
            existing_user.password = npass
            db.session.commit()
            # return render_template('test.html',existing_user = existing_user)
            return redirect(url_for('login'))
    return render_template('reset.html',form = form)




#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        bio ='                        '
        profile_picture = 'default_pf.png'
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, email=email,password=password,bio=bio, profile_picture=profile_picture)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

#full_post route
@app.route("/full_post/<int:post_id>",methods=['GET', 'POST'])
@login_required
def full_post(post_id,limit=2):
    post = Post.query.get_or_404(post_id)
    unique_tags = list(set(tag for tag, in Post.query.with_entities(Post.tag).distinct().limit(15)))

     # get 5 popular post by like count
    popular_posts = Post.query.order_by(Post.likes.desc()).limit(limit).all()

    comment_form = CommentForm()
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
         search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
         return render_template('search_results.html' , form=forms,search_results =search_results,popular_posts = popular_posts)
    elif comment_form.validate_on_submit():
        comment = Comment(content=comment_form.content.data, post=post, author=current_user)
        db.session.add(comment)
        db.session.commit()
        comment_form.content.data=''
        #flash('Comment added!', 'success')
        return render_template('full_post.html',tags=unique_tags, post=post ,comment_form = comment_form , form = forms,popular_posts = popular_posts)
    
    return render_template('full_post.html', tags=unique_tags,post=post ,comment_form = comment_form , form = forms,popular_posts = popular_posts )
    
@app.route("/edit_post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        meta_data = ' '.join(content.split()[:10])
        tag = request.form.get('dynamicFields[]')
        post.title=title
        post.content=content
        post.meta=meta_data
        post.tag=tag
        db.session.commit()
        return redirect(url_for('profile', user_id= current_user.id))
    forms=SearchForm()
    query = forms.search.data
    if forms.validate_on_submit():
        search_results = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
        return render_template('search_results.html' , search_results =search_results, form = forms)
    
    return render_template('edit_post.html',post=post, form = forms)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    picture_url = get_profile_profile(current_user.id)
    user=current_user
    form = PictureUpdate()
    bio = current_user.bio
    if request.method == 'POST':
        username=request.form.get('username')
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
        user.username=username
        db.session.commit()
        return redirect(url_for('profile',user_id=current_user.id))
    return render_template('profile_edit.html',form=form,user=user,picture_url=picture_url)
