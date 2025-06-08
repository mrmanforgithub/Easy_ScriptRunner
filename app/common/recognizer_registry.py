from collections import namedtuple

RECOGNIZER_REGISTRY = {}

RecognizerItem = namedtuple('RecognizerItem', ['icon', 'cls', 'func', 'fields'])

def register_recognizer(key, icon, recognize_func, fields=None):
    def decorator(cls):
        cls.key = key
        cls.icon = icon
        cls.func = staticmethod(recognize_func)
        RECOGNIZER_REGISTRY[key] = RecognizerItem(
            icon=icon,
            cls=cls,
            func=recognize_func,
            fields=fields or []
        )
        return cls
    return decorator