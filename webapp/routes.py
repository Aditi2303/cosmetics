import os
import secrets
from PIL import Image
import cv2
from skimage.measure import compare_ssim
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from werkzeug import secure_filename 
from webapp import app, db, bcrypt
from webapp.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from webapp.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

    

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static',filename='profile_pics/'+current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form = form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
##    image1_file = url_for('static',filename='uploaded_pics/'+current_user.image1_file)
##    flash('Your picture is uploaded')
##    return redirect(url_for('home'))
##    return render_template('trial.html', title='New Post', image1_file = image1_file, form = form, legend='Authentify Product')
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture1_file = save_picture(form.picture1.data)
            post.image1_file = picture1_file
            db.session.add(picture1_file)   
        db.session.commit()
        flash('Your picture is uploaded')
        return redirect(url_for('home'))
    image_file = url_for('static',filename='profile_pics/'+post.image1_file)
    return render_template('trial.html', title='New Post', form = form, legend='Authentify Product')

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form = form, legend='Update Post')

    
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))



def mid(A, B):
	return ((A[0] + B[0]) * 0.5, (A[1] + B[1]) * 0.5)
def DiffDetect(image1,image2):
    (hO,wO,cO) = image1.shape
    image_2 = cv2.resize(image2,(wO,hO))
    cv2.imwrite("newFake.jpg",image_2)
    img1gr = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    img2gr = cv2.cvtColor(image_2, cv2.COLOR_BGR2GRAY)
    (x, y) = compare_ssim(img1gr, img2gr, full=True)
    difference = (y * 255).astype("uint8")
    return difference, x
def dimension(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bound = cv2.Canny(gray, 50, 100)
    bound = cv2.dilate(bound, None, iterations=1)
    bound = cv2.erode(bound, None, iterations=1)
    num = cv2.findContours(bound.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    num = imutils.grab_contours(num)
    (num, _) = contours.sort_contours(num)
    ppm = None
    for n in num:
            if cv2.contourArea(n) < 100:
                    continue
            dim = image.copy()
            m = cv2.minAreaRect(n)
            m = cv2.cv.BoxPoints(m) if imutils.is_cv2() else cv2.boxPoints(m)
            m = np.array(m, dtype="int")
            m = perspective.order_points(m)
            cv2.drawContours(dim, [m.astype("int")], -1, (0, 255, 0), 2)
            for (x, y) in m:
                    cv2.circle(dim, (int(x), int(y)), 5, (0, 0, 255), -1)
            (a, b, c, d) = m
            (topX, topY) = mid(a, b)
            (bottomX, bottomY) = mid(d, c)
            (leftX, leftY) = mid(a, d)
            (rightX, rightY) = mid(b, c)
            cv2.circle(dim, (int(topX), int(topY)), 5, (255, 0, 0), -1)
            cv2.circle(dim, (int(bottomX), int(bottomY)), 5, (255, 0, 0), -1)
            cv2.circle(dim, (int(leftX), int(leftY)), 5, (255, 0, 0), -1)
            cv2.circle(dim, (int(rightX), int(rightY)), 5, (255, 0, 0), -1)
            cv2.line(dim, (int(topX), int(topY)), (int(bottomX), int(bottomY)),
                    (255, 0, 255), 2)
            cv2.line(dim, (int(leftX), int(leftY)), (int(rightX), int(rightY)),
                    (255, 0, 255), 2)
            h1 = dist.euclidean((topX, topY), (bottomX, bottomY))
            w1 = dist.euclidean((leftX, leftY), (rightX, rightY))
            if ppm is None:
                    ppm = w1 / 0.9
            height = h1 / ppm
            width = w1 / ppm
            cv2.putText(dim, "{:.1f}in".format(height),(int(topX - 15), int(topY - 10)), cv2.FONT_HERSHEY_SIMPLEX,0.65, (255, 255, 255), 2)
            cv2.putText(dim, "{:.1f}in".format(width),(int(rightX + 10), int(rightY)), cv2.FONT_HERSHEY_SIMPLEX,0.65, (255, 255, 255), 2)
            cv2.imshow("dimensions of original product", dim)
            cv2.waitKey(0)  



    
@app.route('/upload')
def upload_file():
    return render_template('upload1.html')

@app.route('/uploader1', methods = ['GET', 'POST'])
def uploader_file():
    #if request.method() == 'POST':
    f = request.files['file']
    f.save(secure_filename(f.filename))
    pil_image = Image.open(f) 
    open_cv_image = np.array(pil_image) 
    # Convert RGB to BGR 
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    OrgFr = cv2.imread('orginal_front.jpg')
    [diff_front, ssim] = DiffDetect(open_cv_image,OrgFr)
    ssim = 1-ssim
    ssim = ssim*100
    ssim = str(ssim)
    cv2.imshow("Difference shown by front part", diff_front)
    cv2.waitKey(0)
    #pimg.show()
    flash('The difference in the frontview of packaging ' + ssim + '%','success')
    return render_template('home.html')


@app.route('/uploadBack')
def upload_file1():
    return render_template('upload2.html')

@app.route('/uploader2', methods = ['GET', 'POST'])
def uploader_file1():
    #if request.method() == 'POST':
    f1 = request.files['file']
    f1.save(secure_filename(f1.filename))
    pil_image1 = Image.open(f1) 
    open_cv_image1 = np.array(pil_image1) 
    # Convert RGB to BGR 
    open_cv_image1 = open_cv_image1[:, :, ::-1].copy()
    OrgBack = cv2.imread('original_back.jpg')
    [diff_front1, ssim1] = DiffDetect(open_cv_image1,OrgBack)
    ssim1 = ssim1*100
    ssim1 = str(ssim1)
    cv2.imshow("Difference shown by front part", diff_front1)
    cv2.waitKey(0)
    #pimg.show()
    flash('The difference in the backview of packaging ' + ssim1 + '%','success')
    return render_template('home.html')


@app.route('/uploadDim')
def upload_file2():
    return render_template('upload3.html')

@app.route('/uploader3', methods = ['GET', 'POST'])
def uploader_file2():
    #if request.method() == 'POST':
    f2 = request.files['file']
    f2.save(secure_filename(f2.filename))
    pil_image2 = Image.open(f2) 
    open_cv_image2 = np.array(pil_image2) 
    # Convert RGB to BGR 
    open_cv_image2 = open_cv_image2[:, :, ::-1].copy()
    dimension(open_cv_image2)
    return render_template('home.html')

