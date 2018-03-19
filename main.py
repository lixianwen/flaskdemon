#!/usr/bin/env python
#coding:utf8

import hashlib
from flask import Flask
from flask import render_template
from flask import session
from flask import abort
from flask import request
from flask import flash
from flask import url_for
from flask import redirect
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from verifycode import VeifyCode
from flask import make_response

app = Flask(__name__)
app.secret_key = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@192.168.0.20/blog'
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    title = db.Column(db.VARCHAR(64))
    text = db.Column(db.TEXT)
    pub_time = db.Column(db.DATETIME)


class User(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    username = db.Column(db.VARCHAR(32), nullable=False)
    password = db.Column(db.VARCHAR(100), nullable=False)
    email = db.Column(db.VARCHAR(32))

db.create_all()

@app.route('/')
def index():
    data = Article.query.order_by(Article.id.desc()).all()
    returns = [dict(title=row.title, text=row.text, pub_time=row.pub_time) for row in data]
    return render_template('show_article.html', returns=returns)

@app.route('/add', methods=['POST'])
def add_article():
    if not session.get('logged_in'):
        abort(401)
    data = Article(title=request.form['title'], text=request.form['text'], pub_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    db.session.add(data)
    db.session.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        _username = request.form['username']
        _password = request.form['passwd']
        _text = request.form['verifycode'].lower()
        print(session['code_text'], _text)
        if session['code_text'] != _text:
            error = '验证码错误，请重新输入'
            session.pop('code_text', None)
            return render_template('login.html', error=error)
        encrypt_password = hashlib.md5(_password.encode('utf8')).hexdigest()
        check = User.query.filter(User.username == _username).filter(User.password == encrypt_password).all()
        if check:
            session['logged_in'] = True
            session['username'] = _username
            flash('You were logged in')
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('code_text', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        pwdrepeat = request.form['pwdrepeat']
        email = request.form['email']
        _text = request.form['verifycode'].lower()
        print(session['code_text'], _text)
        if password != pwdrepeat:
            error = '两次输入密码不一致'
            return render_template('register.html', error=error)
        elif session['code_text'] != _text:
            error = '验证码错误，请重新输入'
            session.pop('code_text', None)
            return render_template('register.html', error=error)
        else:
            encrypt_password = hashlib.md5(password.encode('utf8')).hexdigest()
            data = User.query.filter(User.username == username).filter(User.password == encrypt_password).all()
            if data:
                error = 'You are already registered'
                return render_template('login.html', error=error)
            data_reg = User(username=username, password=encrypt_password, email=email)
            db.session.add(data_reg)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/image')
def image():
    verifyCode = VeifyCode()
    content, buf_str = verifyCode.getImage()
    session['code_text'] = content
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/png'
    return response



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)