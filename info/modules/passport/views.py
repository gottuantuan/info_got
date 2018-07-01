from datetime import datetime

from flask import session

from info.models import User
from . import passport_blue
from flask import request, jsonify, current_app, make_response
from info.utils.response_code import RET
from info.utils.captcha.captcha import captcha
from info import redis_store, constants, db
import re, random
from info.libs.yuntongxun import sms


@passport_blue.route('/image_code')
def generate_image_code():
    image_code_id = request.args.get('image_code_id')
    if not image_code_id:
        return jsonify(erron=RET.PARAMERR, errmsg='参数缺失1')
    name, text, image = captcha.generate_captcha()
    try:
        redis_store.setex('ImageCode_'+image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR, errmsg='保存图片验证码失败')
    else:
        response = make_response(image)
        response.headers['Content-Type'] = 'image/jpg'
        return response

@passport_blue.route('/sms_code',methods=['POST'])
def send_sms_code():
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失2')
    if not re.match(r'^1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取图片验证码异常')
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')
        # 因为图片验证码只能让用户比较一次，redis只能get一次，所以要立即删除
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # 比较图片验证码是否正确
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
        # 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(enrro=RET.DATAERR, errmsg='查询数据库异常')
    else:
        if user is not None:
            return jsonify(enrro=RET.DATAEXIST,errmsg='手机号已经注册过')

        # 构造短信随机码,format()
    sms_code = '%06d' % random.randint(0, 999999)
    # 把短信随机数保存到redis数据库中
    try:
        redis_store.setex('SMSCode_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')
    # 调用云通讯，发送短信随机数
    try:
        ccp = sms.CCP()
        # 调用云通讯的模板方法，发送短信，需要保存发送结果
        result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信异常')
    # 判断发送结果
    if result == 0:
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')


@passport_blue.route('/register',methods=['POST'])
def register():
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='信息获取不全')
    if not re.match(r'^1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR,errmsg= '手机号不正确')
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取短信验证码异常')
    if not real_sms_code:
        return jsonify(errno=RET,errmsg='短信验证码过期')
    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
    try:
        redis_store.delete('SMSCode'+mobile)
    except Exception as e:
        current_app.logger.error(e)
    try:
        user = User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    else:
        if user is not None:
            return jsonify(errno=RET.DATAEXIST,errmsg='手机号已注册')

    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存失败')
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name']=mobile
    return jsonify(errno=RET.OK, errmsg='注册成功')

@passport_blue.route('/login',methods=['POST'])
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

@passport_blue.route('/logout')
def logout():
    session.pop('user_id',None)
    session.pop('mobile',None)
    session.pop('nick_name',None)
    return jsonify(errno=RET.OK,errmsg='Ok')


