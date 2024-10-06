from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from function import verify_password, verify_name, verify_mail, check_locality, get_secret_key, get_locations
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = get_secret_key()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base_1.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    locality = db.Column(db.String, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    businesses = db.relationship('Business', backref='company')


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    users = User.query.all()
    companies = Company.query.all()
    businesses = Business.query.all()
    session.clear()
    return render_template('index.html', users=users, companies=companies, businesses=businesses)


# company function


@app.route('/company.register', methods=["POST", "GET"])
def company_register():
    if request.method == 'POST':
        name = request.form['name']
        mail = request.form['company_mail']
        locality = request.form['locality']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        existing_company = Company.query.filter_by(name=name).first()
        existing_mail = Company.query.filter_by(email=mail).first()
        if verify_password(password, confirm_password) and verify_name(existing_company, name) and verify_mail(
                existing_mail) and check_locality(locality):

            company = Company(
                name=name,
                email=mail,
                locality=locality,
                password=password
            )
            try:
                db.session.add(company)
                db.session.commit()
                flash(category='success', message='account created successfully')
                return redirect(url_for('company_login'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash(category='error', message='account creation was not successful')
    return render_template('company_register.html')


@app.route('/suggestion', methods=['GET'])
def suggestion():
    query = request.args.get('query')
    if query:
        suggestions = get_locations(query)
        return jsonify(suggestions)
    return jsonify([])


@app.route('/company.login', methods=['POST', 'GET'])
def company_login():
    if 'company_id' in session:
        return redirect(url_for('company_home'))
    if request.method == 'POST':
        mail = request.form['company_mail']
        password = request.form['password']
        query = Company.query.filter_by(email=mail, password=password).first()
        if query:
            session["company_id"] = query.id
            session["logged"] = True
            return redirect(url_for('company_home'))
        else:
            flash(category='error', message='incorrect identifiers')
    return render_template('company_login.html')


@app.route('/company.home')
def company_home():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    posts = Business.query.filter_by(company_id=session['company_id'])
    return render_template('company_home.html', posts=posts)


@app.route('/company.post', methods=['POST', 'GET'])
def company_post():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    if request.method == 'POST':
        name = request.form['business_type']
        description = request.form['description']
        post = Business(name=name, company_id=session['company_id'], description=description)
        try:
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('company_home'))
        except Exception as e:
            db.session.rollback()
            print(e)
            flash(category='error', message='Post creation was not successfully')
    return render_template('company_post.html')


@app.route('/company.post/info.post/<int:post_id>', methods=['POST', 'GET'])
def info_post(post_id):
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    post = Business.query.get_or_404(post_id)
    if request.method == 'POST':
        if 'name' in request.form:
            name = request.form['name']
            try:
                post.name = name
                db.session.commit()
                return redirect(url_for('info_post', post_id=post.id))
            except Exception as e:
                print(e)
                db.session.rollback()
                flash(category='error', message='error while editing')
        elif 'description' in request.form:
            description = request.form['description']
            try:
                post.description = description
                db.session.commit()
                return redirect(url_for('info_post', post_id=post.id))
            except Exception as e:
                print(e)
                db.session.rollback()
                flash(category='error', message='error while editing')
    return render_template('company_info_post.html', post=post)


@app.route('/company.post/delete.post/<int:post_id>', methods=['POST', 'GET'])
def delete_post(post_id):
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    try:
        post = Business.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(category='error', message='error while deleting')
    return redirect(url_for('company_home'))


@app.route('/company.profile', methods=['POST', 'GET'])
def company_profile():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    company = Company.query.get_or_404(session['company_id'])
    if request.method == 'POST':
        if 'name' in request.form:
            name = request.form['name']
            exiting_name = Company.query.filter_by(name=name).first()
            if verify_name(exiting_name, name):
                try:
                    company.name = name
                    db.session.commit()
                    return redirect(url_for('company_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
        elif 'company_mail' in request.form:
            company_mail = request.form['company_mail']
            existing_mail = Company.query.filter_by(email=company_mail).first()
            if verify_mail(existing_mail):
                try:
                    company.email = company_mail
                    db.session.commit()
                    return redirect(url_for('company_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
        elif 'password' and 'confirm_password' in request.form:
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            if verify_password(password, confirm_password):
                try:
                    company.password = password
                    db.session.commit()
                    return redirect(url_for('company_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
        elif 'locality' in request.form:
            locality = request.form['locality']
            try:
                company.locality = locality
                db.session.commit()
                return redirect(url_for('company_profile'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash(category='error', message='error while editing')
    return render_template('company_profile.html', company=company)


@app.route('/company.logout', methods=['POST', 'GET'])
def company_logout():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    session.pop('company_id', None)
    return redirect(url_for('company_login'))


@app.route('/company.delete',methods=['POST', 'GET'])
def company_delete():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    if 'company_id' in session:
        company = User.query.get(session['company_id'])
        if company:
            db.session.delete(company)
            db.session.commit()
            session.pop('company_id')
            return redirect(url_for('company_login'))
    return redirect(url_for('company_login'))


# user function


@app.route('/user.register', methods=['POST', 'GET'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        mail = request.form['user_mail']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        existing_user = User.query.filter_by(username=username).first()
        existing_mail = User.query.filter_by(email=mail).first()

        if verify_password(password, confirm_password) and verify_name(existing_user and verify_mail(existing_mail)):
            user = User(
                username=username,
                email=mail,
                password=password
            )
            try:
                db.session.add(user)
                db.session.commit()
                flash(category='success', message='account create successfully')
                return redirect(url_for('user_login'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash(category='error', message='account creation was not successful')
    return render_template('user_register.html')


@app.route('/user.login', methods=['POST', 'GET'])
def user_login():
    if 'user_id' in session:
        return redirect(url_for('user_home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        query = User.query.filter_by(username=username, password=password).first()
        if query:
            session["user_id"] = query.id
            session["logged"] = True
            return redirect(url_for('user_home'))
        else:
            flash(category='error', message='incorrect identifiers')
    return render_template('user_login.html')


@app.route('/user.home')
def user_home():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    businesses = Business.query.all()
    return render_template('user_home.html', businesses=businesses)


@app.route('/user.info/<string:company_name>/<string:business_name>')
def user_info_business(company_name, business_name):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    business = Business.query.filter_by(name=business_name).first()
    return render_template('user_info_business.html', business=business)


@app.route('/user.filter.business', methods=['POST', 'GET'])
def user_filter_business():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    businesses = []
    if request.method == 'POST':
        categories = request.form.getlist('categories')
        locality = request.form['locality']
        if categories and locality:
            businesses = Business.query.filter(Business.name.in_(categories), Company.locality == locality).all()
            if businesses:
                session['businesses'] = [business.id for business in businesses]
                return redirect(url_for('business_filter_view'))
            else:
                flash(message='empty', category='info')

        elif locality and categories == []:
            businesses = Business.query.filter(Company.locality == locality).all()
            if businesses:
                session['businesses'] = [business.id for business in businesses]
                return redirect(url_for('business_filter_view'))
            else:
                flash(message='empty', category='info')

        elif categories and locality == '':
            businesses = Business.query.filter(Business.name.in_(categories)).all()
            if businesses:
                session['businesses'] = [business.id for business in businesses]
                return redirect(url_for('business_filter_view'))
            else:
                flash(message='empty', category='info')

        else:
            flash(message='not found', category='error')
    return render_template('user_filter_business.html')


@app.route('/user.business_filter/filter.result', methods=['GET'])
def business_filter_view():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    business_ids = session.pop('businesses', [])
    businesses = Business.query.filter(Business.id.in_(business_ids)).all()
    return render_template('user_business_filter_view.html', businesses=businesses)


@app.route('/user.company_info/<string:company_name>', methods=['GET'])
def company_info(company_name):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    company = Company.query.filter_by(name=company_name).first()
    return render_template('company_info.html', company=company)


@app.route('/user.profile', methods=['POST', 'GET'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    user = User.query.get_or_404(session['user_id'])
    if request.method == 'POST':
        if 'username' in request.form:
            username = request.form['username']
            exiting_name = User.query.filter_by(username=username).first()
            if verify_name(exiting_name, username):
                try:
                    user.username = username
                    db.session.commit()
                    return redirect(url_for('user_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
        elif 'user_mail' in request.form:
            mail = request.form['user_mail']
            exiting_mail = User.query.filter_by(email=mail).first()
            if verify_mail(exiting_mail):
                try:
                    user.email = mail
                    db.session.commit()
                    return redirect(url_for('user_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
        elif 'password' and 'confirm_password' in request.form:
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            if verify_password(password, confirm_password):
                try:
                    user.password = password
                    db.session.commit()
                    return redirect(url_for('user_profile'))
                except Exception as e:
                    db.session.rollback()
                    print(e)
                    flash(category='error', message='error while editing')
    return render_template('user_profile.html', user=user)


@app.route('/user.logout', methods=['POST', 'GET'])
def user_logout():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    session.pop('user_id', None)
    return redirect(url_for('user_login'))


@app.route('/user.delete', methods=['POST', 'GET'])
def user_delete():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            db.session.delete(user)
            db.session.commit()
            session.pop('user_id')
            return redirect(url_for('user_login'))
    return redirect(url_for('user_login'))


# Handle invalid routes


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.route('/clear_flash')
def clear_flash():
    session.pop('_flashes', None)
    return {"success": True}


if __name__ == '__main__':
    app.run(debug=True)
