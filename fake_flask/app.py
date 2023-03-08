import typing as t
from collections import UserDict

from werkzeug.utils import import_string
from werkzeug.routing import Rule, Map

from cache import cached_property

T = t.TypeVar('T', bound='FakeFlask')

class Config(UserDict):
    def from_object(self, obj: t.Union[object, str]) -> None:
        if isinstance(obj, str):
            obj = import_string(obj)

        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)


class ConfigAttribute:
    """Makes an attribute forward to the config."""

    def __init__(self, get_converter: t.Optional[t.Callable] = None) -> None:
        self.get_converter = get_converter

    def __set_name__(self, owner: t.Type[T], name: str) -> None:
        self._name = name.upper()
    
    def __get__(self, instance: 'FakeFlask', owner: t.Optional[t.Type[T]] = None) -> t.Any:
        # invocation from a class
        if instance is None:
            return self
        
        try:
            rv = instance.config[self._name]
        except KeyError:
            message = f'{instance.__class__.__name__!r} object has no attribute {self._name.lower()!r}'
            raise AttributeError(message) from None
        if self.get_converter is not None:
            rv = self.get_converter(rv)
        
        return rv
    
    def __set__(self, instance: 'FakeFlask', value: t.Any) -> None:
        instance.config[self._name] = value

    def __delete__(self, instance: 'FakeFlask') -> None:
        del instance.config[self._name]


class FakeFlask:
    config_class = Config

    url_rule_class = Rule

    url_map_class = Map

    secret_key = ConfigAttribute()

    default_config = {
        'ENV': None,
        'SECRET_KEY': None
    }

    def __init__(self) -> None:
        self.config = self.config_class(self.default_config)
        self.url_map = self.url_map_class()
        self.view_functions: t.Dict[str, t.Callable] = {}

    @cached_property  # Requires an instance dict
    def pi(self):
        return 4 * sum((-1.0)**n / (2.0*n + 1.0)
                       for n in reversed(range(1000_0000)))

    def route(self,rule: str, **options) -> t.Callable:
        def decorator(func: t.Callable) -> t.Callable:
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(rule, endpoint, func, **options)
            return func

        return decorator
    
    def add_url_rule(
        self,
        rule: str,
        endpoint: t.Optional[str] = None,
        view_func: t.Optional[t.Callable] = None,
        **options
    ) -> None:
        if endpoint is None:
            assert view_func is not None, 'expected view func if endpoint is not provided.'
            endpoint = view_func.__name__
        options['endpoint'] = endpoint

        methods = options.pop('methods', None)
        if methods is None:
            methods = getattr(view_func, 'methods', None) or ('GET', 'OPTIONS')
        if isinstance(methods, str):
            raise TypeError(
                "Allowed methods must be a list of strings, for"
                ' example: @app.route(..., methods=["POST"])'
            )
        methods = {item.upper() for item in methods}

        rule = self.url_rule_class(rule, methods=methods, **options)
        self.url_map.add(rule)

        if view_func is not None:
            self.view_functions[endpoint] = view_func
