import typing as t
from functools import wraps
from threading import RLock

import typing_extensions as te

P = te.ParamSpec('P')
T = t.TypeVar('T')


def evaluated_once_simple(func: t.Callable[[], T]) -> t.Callable[[], T]:
    """A decorator cache function's return value"""
    value = None

    @wraps(func)
    def wrapper() -> T:
        """Wrap :func:`func` without arguments"""
        nonlocal value

        if value is None:
            print('setting......')
            value = func()

        print('getting......')
        return value
    return wrapper


def cache_with_arguments():
    """一个缓存带参数的函数的装饰器
    
    思路: 
    key = args
    for item in kwargs.items():
        key += item
    hash_key = hash(key)
    cache = {}
    value = cache.get(hash_key, None)
    if value is not None:
        hits += 1
        return value
    misses += 1
    result = func(*args, **kwargs)
    cache[hash_key] = result
    return result

    完整实现: https://github.com/python/cpython/blob/3.11/Lib/functools.py#L479
    """
    pass


class cached_property:
    """Same as :class:`functools.cached_property`, but would not check for boundary."""

    def __init__(
        self,
        fget: t.Callable,
        name: t.Optional[str] = None,
        doc: t.Optional[str] = None
    ) -> None:
        self.fget = fget
        self.func_name = name or fget.__name__
        self.doc = doc or fget.__doc__
        self.lock = RLock()
    
    def __get__(self, instance: object, owner: t.Optional[t.Type] = None) -> T:
        if instance is None:
            return self  # type: ignore
        
        null = object()
        value: T = vars(instance).get(self.func_name, null)
        if value is null:
            with self.lock:
                # check if another thread filled cache while we awaited lock
                value: T = vars(instance).get(self.func_name, null)  # type: ignore
                if value is null:
                    value = self.fget(instance)
                    instance.__dict__[self.func_name] = value

        return value
