from collections import namedtuple

OPERATION_REGISTRY = {}

OperationItem = namedtuple('OperationItem', ['icon', 'cls', 'func', 'fields'])


def register_operation(name, icon, execute_func, fields=None):
    def decorator(cls):
        cls.key = name
        cls.icon = icon
        cls.func = staticmethod(execute_func)
        OPERATION_REGISTRY[name] = OperationItem(
            icon=icon,
            cls=cls,
            func=execute_func,
            fields=fields or []
        )
        return cls
    return decorator