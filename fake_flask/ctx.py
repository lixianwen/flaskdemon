import sys
import typing as t

if t.TYPE_CHECKING:
    from flask import Flask
    from flask.sessions import SessionMixin
    from flask.wrappers import Request

from globals import _request_ctx_stack, _app_ctx_stack, _sentinel

class AppContext:
    def __init__(self, app: 'Flask') -> None:
        self.app = app

    def push(self) -> None:
        _app_ctx_stack.push(self)
    
    def pop(self, exc: t.Optional[Exception] = _sentinel) -> None:
        try:
            self.app.do_teardown_appcontext(exc)
        finally:
            rv = _app_ctx_stack.pop()
        assert rv is self, f'Popped wrong app context. ({rv!r} instead of {self!r})'


class RequestContext:
    def __init__(
        self,
        app: 'Flask',
        environ: t.Dict,
        request: t.Optional['Request'] = None,
        session: t.Optional['SessionMixin'] = None
    ) -> None:
        self.app = app
        if request is None:
            request = app.request_class(environ)
        self.request = request
        self.url_adapter = app.create_url_adapter(self.request)
        self.session = session

        self._implicit_app_ctx_stack: t.List[t.Optional["AppContext"]] = []

    def push(self) -> None:
        # Before we push the request context we have to ensure that there
        # is an application context.
        app_ctx = _app_ctx_stack.top
        if app_ctx is None or app_ctx.app != self.app:
            app_ctx = AppContext(self.app)
            app_ctx.push()

        _request_ctx_stack.push(self)

        if self.session is None:
            session_interface = self.app.session_interface
            self.session = session_interface.open_session(self.app, self.request)

        # Match the request URL after loading the session, so that the
        # session is available in custom URL converters.
        if self.url_adapter is not None:
            self.match_request()

    def match_request(self) -> None:
        result = self.url_adapter.match(return_rule=True)
        self.request.url_rule, self.request.view_args = result

    def pop(self, exc: t.Optional[Exception] = None) -> None:
        app_ctx = self._implicit_app_ctx_stack.pop()
        clear_request = False

        try:
            if not self._implicit_app_ctx_stack:
                if exc is None:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_appcontext(exc)

                request_close = getattr(self.request, 'close', None)
                if request_close is not None:
                    request_close()
                clear_request = True
        finally:
            rv = _request_ctx_stack.pop()

            if app_ctx is not None:
                app_ctx.pop(exc)

            assert rv is self, f'Popped wrong request context. ({rv!r} instead of {self!r})'