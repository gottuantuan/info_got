import datetime
import re

from flask import g
from flask import request

from info import db
from info.models import User, News,Category
from info.utils.commons import login_required

from . import new_blue
from flask import session,render_template,current_app, jsonify
from info.utils.response_code import RET


@new_blue.route('/')
@login_required
def index():
    user = g.user
    # 点击排行由大到小
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='无查询结果')
    if not news_list:
        return jsonify(errno=RET.NODATA,errmsg='新闻数据不存在')
    # 遍历查询结果
    news_dict_list = []
    for news in news_list:
        # to_dict（）方法返回字典，放入列表中保存
        news_dict_list.append(news.to_dict())

    # 首页新闻分类数据展示
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询不到新闻')
    if not categories:
        return jsonify(errno=RET.NODATA, errmsg='无新闻数据')
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())




    data = {
        'user_info': user.to_dict() if user else None,
        'news_dict_list': news_dict_list,
        'category_list': category_list
    }
    return render_template('./news/index.html', data=data)




@new_blue.route('/news_list')
def get_news_list():
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '10')
    try:
        cid, page, per_page = int(cid), int(page), int(per_page)

    except Exception as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    filters = []
    if cid > 1:
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询分页数据失败')

    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page
    # 定义容器，遍历分页后的新闻数据
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_dict())
    data ={
        'news_dict_list':news_dict_list,
        'total_page':total_page,
        'current_page':current_page
    }
    return jsonify(errno=RET.OK,errmsg='OK',data=data)


@new_blue.route('/<int:news_id>')
@login_required
def get_new_detail(news_id):
    user =g.user
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(RET.DBERR, errmsg='数据查询异常')
    if not news:
        return jsonify(RET.NODATA, errmsg='无新闻数据')
    news.clicks += 1
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg = '保存数据失败')

    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='无查询结果')
    if not news_list:
        return jsonify(errno=RET.NODATA, errmsg='新闻数据不存在')
        # 遍历查询结果
    news_dict_list = []
    for index in news_list:
        # to_dict（）方法返回字典，放入列表中保存
        news_dict_list.append(index.to_dict())



    data={

        'user_info': user.to_dict()if user else None,
        'news_detail': news.to_dict(),
        'news_dict_list': news_dict_list
    }

    return render_template('news/detail.html',data=data)


@new_blue.route('/news_collect',methods=['POST'])
@login_required
def new_collect():
    user=g.user
    if not user:
        return jsonify(erron=RET.SERVERERR,errmsg='用户未登录')
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    if action not  in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据查询失败')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='新闻数据不存在')
    if action=='collect':
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据保存失败')
    return jsonify(errno=RET.OK, errmsg='OK')

@new_blue.route('/login',methods=['POST'])
def login():
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if not re.match(r'^1[456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式问题')
    try:
        user= User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库异常')
    if user is None or not user.check_password(password):
        return jsonify(errno=RET.PWDERR,errmsg='用户名或密码错误')
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = user.nick_name
    return jsonify(errno=RET.OK,errmsg='登陆成功')





@new_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


