from . import new_blue
from flask import session,render_template,current_app

@new_blue.route('/')
def index():
    session['name'] = '2018'
    return render_template('./news/index.html')


@new_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')