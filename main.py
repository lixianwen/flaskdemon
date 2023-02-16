from business.base import app as flask_app, init_app
from business.extensions import scheduler

app = init_app(flask_app)

scheduler.start()
print('scheduler start........')


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
