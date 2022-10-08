from business.base import app as flask_app, init_app

app = init_app(flask_app)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
