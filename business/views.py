from flask_restx import Resource
from flask import current_app

from business.signal import model_saved


resource_list = []

def my_route(*urls, **kwargs):
    """A decorator to route resources."""

    def wrapper(cls):
        resource_list.append({'class': cls, 'urls': urls, 'kwargs': kwargs})
        return cls

    return wrapper


@my_route('/hello')
class HelloWorld(Resource):
    def get(self):
        model_saved.send(current_app._get_current_object().name, custom='value')
        return {'hello': 'world'}
