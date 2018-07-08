from flask import Blueprint, request, session, url_for
from flask import redirect

admin_blue = Blueprint('admin',__name__,url_prefix='/admin')


from . import views

@admin_blue.before_request
def check_admin():
    is_admin = session.get('is_admin',False)
    if not is_admin and not request.url.endswith(url_for('admin.login')):
        return redirect('/')
