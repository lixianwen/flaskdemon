from flask_restx import Resource

from business.signal import model_saved
from business.config import MY_SENDER


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
        model_saved.send(MY_SENDER, custom='value')
        return {'hello': 'world'}
