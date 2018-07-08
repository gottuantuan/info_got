from flask_script import Manager
from info import create_app,db
from flask_migrate import MigrateCommand,Migrate
from info import models
from info.models import User

app = create_app('develop')
manage = Manager(app)
Migrate(app,db)
manage.add_command('db', MigrateCommand)




@manage.option('-n','-name', dest = 'name')
@manage.option('-p' ,'-password',dest = 'password')
def create_Supperuser(name,password):
    if not all([name,password]):
        print('参数缺失')
    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
    print('创建成功')




if __name__ == '__main__':
    print(app.url_map)
    manage.run()