from flask import Flask, render_template, request, redirect, url_for, flash, session
from function import verify_password, verify_name, verify_mail
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base_1.db'
db = SQLAlchemy(app)
geolocator = Nominatim(user_agent="geoapiExercises")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
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
    print(session)
    return render_template('index.html', users=users, companies=companies, businesses=businesses)


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
    m = folium.Map(location=[0, 0], zoom_start=2)
    folium.Marker([business.company.lat, business.company.lng], popup=business.company.name).add_to(m)
    m.save("templates/partiels/map.html")
    return render_template('user_info_business.html', business=business)


@app.route('/user.filter.business', methods=['POST', 'GET'])
def user_filter_business():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    filter_companies = []
    if request.method == 'POST':
        radius = request.form.get('radius')
        categories = request.form.getlist('categories')
        user_lat = request.form.get('userLat')
        user_lng = request.form.get('userLng')

        # VERIFICATION
        if not all([radius, categories, user_lat, user_lng]):
            flash('Error')
            return redirect(request.url)

        user_lat = float(user_lat)
        user_lng = float(user_lng)

        companies = Company.query.filter(Company.business_type.in_(categories)).all()

        for company in companies:
            distance = geodesic((company.lat, company.lng), (user_lat, user_lng)).kilometers
            if distance <= int(radius):
                filter_companies.append(company)

        session['filter_companies'] = [company.id for company in filter_companies]

        m = folium.Map(location=[0, 0], zoom_start=2)  # Create a Folium card

        for company in filter_companies:  # Add markers for each location
            folium.Marker([company.lat, company.lng], popup=company.name).add_to(m)

        m.save("templates/partiels/filter_map.html")  # Save the map with markers to an HTML file

        return redirect(url_for('business_filter_view'))

    return render_template('user_filter_business.html')


@app.route('/user.business_filter/filter.result', methods=['GET'])
def business_filter_view():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    company_ids = session.pop('filter_companies', [])
    if not company_ids:
        flash(category='error', message='')
        return redirect(url_for('user_filter_business'))
    companies = Company.query.filter(Company.id.in_(company_ids)).all()
    return render_template('user_business_filter_view.html', companies=companies)


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


@app.route('/user.logout')
def user_logout():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    session.pop('user_id', None)
    return redirect(url_for('user_login'))


@app.route('/user.delete')
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


# company function


@app.route('/company.register', methods=["POST", "GET"])
def company_register():
    if request.method == 'POST':
        name = request.form['name']
        mail = request.form['company_mail']
        business_type = request.form['business_type']
        lat = float(request.form['lat'])
        lng = float(request.form['lng'])
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        existing_company = Company.query.filter_by(name=name).first()
        existing_mail = Company.query.filter_by(email=mail).first()
        if verify_password(password, confirm_password) and verify_name(existing_company, name) and verify_mail(
                existing_mail):
            company = Company(
                name=name,
                email=mail,
                business_type=business_type,
                lat=lat,
                lng=lng,
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
        name = request.form['name']
        description = request.form['description']
        exiting_name = Business.query.filter_by(name=name).first()
        if verify_name(exiting_name):
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
            exiting_name = Business.query.filter_by(name=name).first()
            if verify_name(exiting_name):
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
        elif 'business_type' in request.form:
            business_type = request.form['business_type']
            try:
                company.business_type = business_type
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
        elif 'lat' and 'lng' in request.form:
            lat = float(request.form['lat'])
            lng = float(request.form['lng'])
            try:
                company.lat = lat
                company.lng = lng
                db.session.commit()
                return redirect(url_for('company_profile'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash(category='error', message='error while editing')
    return render_template('company_profile.html', company=company)


@app.route('/company.logout')
def company_logout():
    if 'company_id' not in session:
        return redirect(url_for('company_login'))
    session.pop('company_id', None)
    return redirect(url_for('company_login'))


@app.route('/company.delete')
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


# Handle invalid routes


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
