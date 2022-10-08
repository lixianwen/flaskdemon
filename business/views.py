from flask_restx import Resource

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
        return {'hello': 'world'}
