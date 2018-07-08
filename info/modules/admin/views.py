
from flask import g, render_template, request, session, redirect, url_for, jsonify, current_app, abort
import time
from datetime import datetime,timedelta
from info import constants, db
from info.models import User, News, Category
from info.utils.commons import login_required
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue



@admin_blue.route('/index')
@login_required
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())

@admin_blue.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')
    user_name = request.form.get('username')
    password = request.form.get('password')
    if not all([user_name,password]):
        return render_template('admin/login.html',errmsg='参数缺失')
    try:
        user = User.query.filter(User.mobile == user_name,User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html',errmsg='数据库查询错误')
    if user is None or not user.check_password(password):
        return render_template('admin/login.html',errmsg='密码错误')
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['is_admin'] = user.is_admin
    return redirect(url_for('admin.index'))

@admin_blue.route('/user_count')
def user_count():
    '''
    后台页面数据展示
    :return:
    '''
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin ==False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询总人数异常')
    # 月新增人数
    mon_count = 0
    t = time.localtime()
    mon_begin_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    mon_begin_date = datetime.strptime(mon_begin_date_str,'%Y-%m-%d')
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询月人数异常')
    day_count = 0
    day_begin_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    day_begin_date = datetime.strptime(day_begin_date_str, '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin==False,User.create_time>day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='日新增查询异常')
    active_count = []
    active_time = []
    active_begin_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    active_begin_date = datetime.strptime(active_begin_date_str, '%Y-%m-%d')

    for x in range(0, 31):
        begin_date = active_begin_date - timedelta(days=(x))
        end_date = active_begin_date - timedelta(days=(x-1))
        try:
            count = User.query.filter(User.is_admin == False,User.last_login>=begin_date , User.last_login<end_date)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询活跃度失败')
        begin_date_str = datetime.strftime(begin_date, '%Y-%m-%d')
        active_count.append(count)
        active_time.append(begin_date_str)

    active_time.reverse()
    active_count.reverse()

    data = {
        'total_count':total_count,
        'mon_count':mon_count,
        'day_count':day_count,
        'active_count':active_count,
        'active_time':active_time
    }
    return render_template('admin/user_count.html', data=data)


