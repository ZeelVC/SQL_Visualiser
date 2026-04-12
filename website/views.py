from flask import Blueprint, redirect, url_for

views = Blueprint('views', __name__)


@views.route('/')
def home():
    return redirect(url_for('auth.SQLViz'))

