# Forked from cpython/Lib/functools.py
# This file follows PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2 as CPython
# does.

from threading import RLock

try:
    from functools import _CacheInfo
except ImportError:
    from collections import namedtuple
    _CacheInfo = namedtuple(
        "CacheInfo", ["hits", "misses", "maxsize", "currsize"])

SENTINEL = object()  # unique object used to signal cache misses
PREV, NEXT, KEY, RESULT = 0, 1, 2, 3  # names for the link fields
FULL, HITS, MISSES = 0, 1, 2  # names for stat


class LruCache(object):
    """Created by breaking down functools.lru_cache."""

    def __init__(self, maxsize):
        cache = {}
        cache_get = cache.get  # bound method to lookup a key or return None
        cache_len = cache.__len__  # get cache size without calling len()
        lock = RLock()     # because linkedlist updates aren't threadsafe
        self.root = []   # root of the circular doubly linked list
        # initialize by pointing to self
        self.root[:] = [self.root, self.root, None, None]
        stat = [False, 0, 0]

        def get(key):
            with lock:
                link = cache_get(key)
                if link is not None:
                    root = self.root
                    # Move the link to the front of the circular queue
                    link_prev, link_next, _key, result = link
                    link_prev[NEXT] = link_next
                    link_next[PREV] = link_prev
                    last = root[PREV]
                    last[NEXT] = root[PREV] = link
                    link[PREV] = last
                    link[NEXT] = root
                    stat[HITS] += 1
                    return result
                else:
                    stat[MISSES] += 1
            return SENTINEL

        def delete(key):
            with lock:
                oldresult = self.root[RESULT]  # noqa
                del cache[key]
                stat[FULL] = False

        def set(key, result):
            with lock:
                link = cache_get(key)
                if link is not None:
                    # Update link to store the new result
                    link[-1] = result
                elif stat[FULL]:
                    # Use the old root to store the new key and result.
                    oldroot = self.root
                    oldroot[KEY] = key
                    oldroot[RESULT] = result
                    # Empty the oldest link and make it the new root.
                    # Keep a reference to the old key and old result to
                    # prevent their ref counts from going to zero during the
                    # update. That will prevent potentially arbitrary object
                    # clean-up code (i.e. __del__) from running while we're
                    # still adjusting the links.
                    root = self.root = oldroot[NEXT]
                    oldkey = root[KEY]
                    oldresult = root[RESULT]  # noqa
                    root[KEY] = root[RESULT] = None
                    # Now update the cache dictionary.
                    del cache[oldkey]
                    # Save the potentially reentrant cache[key] assignment
                    # for last, after the root and links have been put in
                    # a consistent state.
                    cache[key] = oldroot
                else:
                    root = self.root
                    # Put result in a new link at the front of the queue.
                    last = root[PREV]
                    link = [last, root, key, result]
                    last[NEXT] = root[PREV] = cache[key] = link
                    # Use the cache_len bound method instead of the len() function
                    # which could potentially be wrapped in an lru_cache itself.
                    stat[FULL] = (cache_len() >= maxsize)

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stat[HITS], stat[MISSES], maxsize, cache_len())

        def clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = self.root
                root[:] = [root, root, None, None]
                stat[:] = False, 0, 0

        self.get = get
        self.delete = delete
        self.set = set
        self.cache_info = cache_info
        self.clear = clear
