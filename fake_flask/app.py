import sys
import typing as t
from collections import UserDict, defaultdict
from flask import Flask

from werkzeug.utils import import_string
from werkzeug.routing import Rule, Map, MapAdapter
from flask.wrappers import Request, Response
from flask.sessions import SecureCookieSessionInterface

from cache import cached_property
from ctx import RequestContext
from globals import _sentinel

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

    request_class = Request

    secret_key = ConfigAttribute()

    default_config = {
        'ENV': None,
        'SECRET_KEY': None,
        'SERVER_NAME': None,
    }

    session_interface = SecureCookieSessionInterface()

    def __init__(self) -> None:
        self.config = self.config_class(self.default_config)
        self.url_map = self.url_map_class()
        self.view_functions: t.Dict[str, t.Callable] = {}
        self.teardown_request_funcs: t.Dict[
            str, t.List[t.Callable[[Exception], None]]
        ] = defaultdict(list)
        self.teardown_appcontext_funcs: t.List[t.Callable[[Exception], None]] = []

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

    def run(self, host: str, port: int, debug: bool, **options) -> None:
        options.setdefault('use_reloader', debug)
        options.setdefault('use_debugger', debug)
        options.setdefault('threaded', True)

        from werkzeug.serving import run_simple

        run_simple(host, port, self, **options)

    def __call__(self, environ: t.Dict, start_response: t.Callable):
        return self.wsgi_app(environ, start_response)
    
    def wsgi_app(self, environ: t.Dict, start_response: t.Callable):
        ctx = RequestContext(self, environ)
        error: t.Optional[Exception] = None
        try:
            try:
                ctx.push()
                response = self.full_dispatch_request()
            except Exception as e:
                error = e
                response = self.handle_exception(e)
            return response(environ, start_response)
        finally:
            ctx.pop(error)

    def create_url_adapter(self, request: Request) -> MapAdapter:
        subdomain = self.url_map.default_subdomain or None
        return self.url_map.bind_to_environ(
            request.environ,
            server_name=self.config['SERVER_NAME'],
            subdomain=subdomain
        )

    def do_teardown_request(self, exc: t.Optional[Exception] = _sentinel) -> None:
        if exc is _sentinel:
            exc = sys.exc_info()[1]

        for name in self.teardown_request_funcs:
            for func in reversed(self.teardown_request_funcs[name]):
                # TODO: need to be a async execution
                func(exc)

    def do_teardown_appcontext(self, exc: t.Optional[Exception] = _sentinel) -> None:
        if exc is _sentinel:
            exc = sys.exc_info()[1]

        for func in reversed(self.do_teardown_appcontext):
            # TODO: need to be a async execution
            func(exc)

    def full_dispatch_request(self) -> Response:
        pass