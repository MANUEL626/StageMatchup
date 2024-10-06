import requests
from flask import flash
import html
import toml


def escape_html_and_check(text):
    escaped_text = html.escape(text)

    if '&gt;' in escaped_text:
        return False
    else:
        return True


def verify_password(password, confirm_password):
    if password != confirm_password:
        flash(category='error', message='Passwords do not match')
        return False
    elif len(password) < 8:
        flash(category='error', message='The password is too short')
        return False
    elif not any(char.isalpha() for char in password):
        flash(category='error', message='The password must contain at least one letter')
        return False
    elif not any(char.isdigit() for char in password):
        flash(category='error', message='The password must contain at least one digit')
        return False
    elif not escape_html_and_check(password):
        flash(category='error', message='enter valid text')
        return False
    return True


def verify_name(existing_name, name=''):
    if existing_name:
        flash(category='error', message='this username is already taken')
        return False
    elif not escape_html_and_check(name):
        flash(category='error', message='enter valid text')
        return False
    return True


def verify_mail(existing_mail):
    if existing_mail:
        flash(category='error', message='this email is already taken')
        return False
    return True


def check_locality(locality):
    url = f"https://nominatim.openstreetmap.org/search?q={locality}&format=json"
    response = requests.get(url)
    data = response.json()
    if data and len(data) > 0:
        return True
    else:
        flash(category='error', message='locality not found')
        print('error')
        return False


def get_locations(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'format': 'json',
        'q': query
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        locations = [loc['display_name'] for loc in data]
        return locations
    except requests.exceptions.JSONDecodeError:
        return []


def load_config(file_path):
    with open(file_path, "r") as f:
        config = toml.load(f)
    return config


def get_secret_key():
    config = load_config("secrets.toml")
    return config["app"]["secret_key"]