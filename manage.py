from flask_script import Manager
from info import create_app,db
from flask_migrate import MigrateCommand,Migrate
from info import models


app = create_app('develop')
manage = Manager(app)
Migrate(app,db)
manage.add_command('db', MigrateCommand)



if __name__ == '__main__':
    print(app.url_map)
    manage.run()