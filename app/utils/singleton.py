"""Singleton metaclass — ensures only one instance per class."""


class SingletonMeta(type):
    """Metaclass that implements the singleton pattern.

    Usage:
        class MyService(metaclass=SingletonMeta):
            def __init__(self):
                # __init__ called only once due to metaclass
                self.some_field = ...

    No __new__ or _initialized checks needed in the class body.
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
