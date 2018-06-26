from . import new_blue
from flask import session,render_template

@new_blue.route('/')
def index():
    session['name'] = '2018'
    return render_template('./news/index.html')