from boltons.timeutils import parse_timedelta
from datetime import datetime

_UNSET = object()
_INTCHARS = 'bcdoxXn'
_FLOATCHARS = 'eEfFgGn%'
_TYPE_MAP = dict([(x, int) for x in _INTCHARS] + [(x, float) for x in _FLOATCHARS])
_TYPE_MAP['s'] = str


class DeferredValue(object):

    def __init__(self, func, cache_expiry=None, cache_value=True, get_on_init=False):
        self.func = func
        self.cache_value = cache_value
        self.expiry_str = cache_expiry

        if self.expiry_str is not None:
            self.expiry_timedelta = parse_timedelta(self.expiry_str)
            self.expiry_time = datetime.now() + self.expiry_timedelta
        else:
            self.expiry_timedelta = None
            self.expiry_time = None
        self._value = _UNSET

        if get_on_init:
            self.get_value()

    def get_value(self):
        """Computes, optionally caches (with an optional expiry time), and returns the value of the *func*.
        If ``get_value()`` has been called before, a cached value may be returned depending on
        the *cache_value* and *cache_expiry* options passed to the constructor
        """
        if self._value is not _UNSET and self.cache_value:
            # We're here because this function has already been called at least once, and cache_value is set to True
            if self.expiry_str is None:
                # The cached value never expires
                return self._value
            else:
                # Check if the cached value has expired
                if datetime.now() >= self.expiry_time:
                    # The cached value has expired - get the new value
                    self._value = self.func()
                    # Set the new expiry time
                    self.expiry_time = datetime.now() + self.expiry_timedelta
                return self._value
        else:
            # We're here because either self.cache_value is False, so no caching is performed
            # Or because this is the first call to get_value()
            value = self.func()
            if self.cache_value:
                self._value = value
        return value

    def __int__(self):
        return int(self.get_value())

    def __float__(self):
        return float(self.get_value())

    def __str__(self):
        return str(self.get_value())

    def __repr__(self):
        return repr(self.get_value())

    def __format__(self, fmt):
        value = self.get_value()

        pt = fmt[-1:]  # presentation type
        type_conv = _TYPE_MAP.get(pt, str)

        try:
            return value.__format__(fmt)
        except (ValueError, TypeError):
            # TODO: this may be overkill
            return type_conv(value).__format__(fmt)
