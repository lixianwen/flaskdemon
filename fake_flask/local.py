import typing as t
from threading import get_ident

class Local:
    __slots__ = ('_storage', 'get_ident_func')

    def __init__(self) -> None:
        super().__setattr__('_storage', {})
        super().__setattr__('get_ident_func', get_ident)

    def __getattr__(self, name: t.Hashable) -> t.Any:
        print('self._storage', self._storage)
        try:
            return self._storage[self.get_ident_func()][name]
        except KeyError:
            raise AttributeError(f'{type(self)!r} object has no attribute {name!r}') from None
        
    def __setattr__(self, name: t.Hashable, value: t.Any) -> None:
        ident = self.get_ident_func()
        try:
            self._storage[ident][name] = value
        except KeyError:
            self._storage[ident] = {name: value}
    
    def __delattr__(self, name: t.Hashable) -> None:
        try:
            del self._storage[self.get_ident_func()][name]
        except KeyError:
            raise AttributeError(f'{type(self)!r} object has no attribute {name!r}') from None
        
    def _release_local(self) ->None:
        self._storage.pop(self.get_ident_func(), None)


class LocalStack:
    def __init__(self) -> None:
        self._local = Local()
    
    def _release_local(self) -> None:
        self._local._release_local()

    def push(self, obj: t.Any) -> t.List[t.Any]:
        # 每次都操作并返回一个新的列表
        # rv = getattr(self._local, 'stack', []).copy()
        # rv.append(obj)
        # self._local.stack = rv
        # return rv

        # 每次都操作并返回同一个列表
        rv = getattr(self._local, "stack", None)
        if rv is None:
            self._local.stack = rv = []
        rv.append(obj)
        return rv
    
    def pop(self) -> t.Any:
        stack = getattr(self._local, 'stack', None)
        if stack is None:
            return
        if len(stack) == 1:
            self._release_local()
        return stack.pop()
    
    @property
    def top(self) -> t.Any:
        try:
            return self._local.stack[-1]
        except (AttributeError, IndexError):
            return None