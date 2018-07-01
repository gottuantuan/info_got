from . import passport_blue
from flask import request,jsonify,current_app,make_response
from info.utils.response_code import RET
from info.utils.captcha.captcha  import captcha
from info import redis_store,constants
import re,random
from info.libs.yuntongxun import sms


@passport_blue.route('/image_code')
def generate_image_code():
    image_code_id = request.args.get('image_code_id')
    if not image_code_id:
        return jsonify(erron=RET.PARAMERR, errmsg='参数缺失1')
    name,text,image = captcha.generate_captcha()
    try:
        redis_store.setex('ImageCode_'+image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR,errmsg='保存图片验证码失败')
    else:
        response = make_response(image)
        response.headers['content-Type'] = 'image/jpg'
        return response

@passport_blue.route('/sms_code',methods=['POST'])
def send_sms_code():
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失2')
    if not re.match(r'^1[3456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
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









