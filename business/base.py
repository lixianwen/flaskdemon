from flask import Flask, request_tearing_down

from business.restful import api
from business.views import resource_list
from business.signal import when_request_tearing_down
from business.extensions import scheduler

app = Flask(__name__)

# Config flask application from a config file.
# Reference: https://flask.palletsprojects.com/en/2.2.x/api/#flask.Config.from_object
app.config.from_object('business.config')


def init_app(flask_app):
    api.init_app(flask_app)

    # fill routes
    print('resource_list....', resource_list)
    for resource in resource_list:
        api.add_resource(resource['class'], *resource['urls'], **resource['kwargs'])

    request_tearing_down.connect(when_request_tearing_down, flask_app)

    scheduler.init_app(flask_app)

    print('Flask application init completed.....')
    return flask_app
