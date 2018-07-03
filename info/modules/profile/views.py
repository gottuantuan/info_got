from flask import current_app
from flask import g, redirect, render_template, jsonify
from flask import request
from flask import session

from info import constants
from info import db
from info.utils.commons import login_required
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import profile_blue
from info.models import Category, News


@profile_blue.route('/info')
@login_required
def user_info():
    '''
    用户基本信息
    1、try  获取用户信息
    2、如果用户未登陆 ，重定向到首页
    3、如果已登陆，调用模型类中to——dict 方法
    4、使用模板，返回用户基本信息
    :return:
    '''

    user = g.user

    if not user:
        return redirect('/')

    data = {
        'user': user.to_dict()
    }
    return render_template('news/user.html', data=data)


@profile_blue.route('/base_info',methods=['GET','POST'])
@login_required
def base_info():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='请登录')
    if request.method=='GET':
        data={
            'user': user.to_dict()
        }
        return render_template('news/user_base_info.html', data=data)
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if gender not in ['MAN', 'WOMEN']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数不正确')

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='参数保存失败')
    session['nick_name'] = user.nick_name
    return jsonify(errno=RET.OK,errmsg='OK')


@profile_blue.route('/pic_info',methods=['GET','POST'])
@login_required
def pic_info():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_pic_info.html', data=data)
    avatar = request.files.get('avatar')

    if not avatar:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        image = avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    # 调用七牛云，上传图片,需要保持七牛云返回的图片名称
    try:
        image_name = storage(image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片异常')

    user.avatar_url = image_name

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保持数据失败')

    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    # 返回图片
    return jsonify(errno=RET.OK, errmsg='OK', data={'avatar_url': image_url})


@profile_blue.route('/pass_info',methods=['GET', 'POST'])
@login_required
def pass_info():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='请登录')
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not all([old_password,new_password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR,errmsg="密码错误")
    user.password = new_password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='参数保存失败')
    return jsonify(errno=RET.OK,errmsg='OK')

@profile_blue.route('/news_release',methods=['GET','POST'])
@login_required
def news_release():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='请登录')
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询分类数据异常')
        if not categories:
            return jsonify(errno=RET.NODATA, errmsg='无分类数据')
        category_list =[]
        for category in categories:
            category_list.append(category.to_dict())

        category_list.pop(0)
        data ={
            'categories':category_list
        }
        return render_template('news/user_news_release.html',data=data)
    title = request.form.get('title')
    digest = request.form.get('digest')
    category_id = request.form.get('category_id')
    content = request.form.get('content')
    index_image = request.files.get('index_image')
    if not all([title, digest, category_id, content, index_image]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    try:
        image_data= index_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='图片读取错误')
    try:
        image_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片异常')
    news = News()
    news.title = title
    news.digest = digest
    news.category_id = category_id
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.source = '个人发布'
    news.status = 1
    news.user_id = user.id
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    return jsonify(errno=RET.OK,errmsg='OK')