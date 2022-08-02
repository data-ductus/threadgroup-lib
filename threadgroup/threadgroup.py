import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor, Future
from threading import ThreadError

from typing import Callable, Dict, Any, List


from .structs import Function, ResultStruct, ResultList


class ThreadGroup:

    def __init__(self, max_workers: int = None):
        """
        Defines a thread group that functions can be registered to using a decorator.
        :param max_workers: An optional integer that says how many workers should be permitted to run at any time. Default: None (unlimited)
        """
        self.functions: Dict[str, Function] = dict()
        self.results: ResultList[ResultStruct] = ResultList()

        self.max_workers = max_workers

        self._executed = False

    def __call__(self, *args, **kwargs):
        return self.execute()

    @property
    def executed(self):
        return self._executed

    def register(self, *fn_args, **fn_kwargs) -> Callable:
        """
        Decorator that registers a function to be part of a thread group.

        :param fn_args: An optional tuple of args for the decorated function
        :param fn_kwargs: An optional dict of kwargs for the decorated function
        :return:

        Example:

        @Init.register()
        def get():
            return 0
        """
        def outer(fun: Callable):

            @functools.wraps(fun)
            def caller(*args, **kwargs):
                r = fun(*args, **kwargs)
                return r
            self.functions[fun.__name__] = create_function(caller, *fn_args, **fn_kwargs)
            return caller
        return outer

    def update_fn_args(self, fn: Callable, *fn_args, **fn_kwargs):
        fn: Function = self.functions[fn.__name__]
        fn.fn_args = fn_args
        fn.fn_kwargs = fn_kwargs

    def execute(self):
        self.results = threaded_execution(list(self.functions.values()), max_workers=self.max_workers)
        self._executed = True
        return self.get_results()

    def get_results(self):
        return self.results


def create_function(fn: Callable, *fn_args, **fn_kwargs) -> Function:
    return Function(fn, *fn_args, **fn_kwargs)


def threaded_execution(functions: List[Function], max_workers: int = None):
    f"""
    Executes a list of {Function} objects using a {ThreadPoolExecutor} object.
    :param functions: An iterable of {Function} objects to run in a threaded manner. 
    :param max_workers: An integer that says how many workers should be used. Default: None (unlimited) 
    :return: The results of the functions executed in a list .
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Constructing some future objects
        futures = [construct_future(executor, f.fn, *f.fn_args, **f.fn_kwargs) for f in functions]
        try:
            # Running the future objects and getting the results
            results = run_futures(futures)
        except Exception as e:
            raise ThreadError(f"Failed to run at least one thread: {e}", e)
    # Returning the results by compiling it in a list where the function and the results of that function are grouped together.
    return compile_results(functions, results)


def construct_future(executor: ThreadPoolExecutor, fn: Callable, *fn_args: Any, **fn_kwargs: Dict[str, Any]) -> Future:
    f"""
    Constructing a Future-object by submitting an arbitrary function with args and kwargs to an executor

    :param executor: A {ThreadPoolExecutor} object that will execute the {Future} object that we submit to it.
    :param fn: A callable to submit to the {executor}.
    :param fn_args: A tuple of args for callable {fn}. 
    :return Returns a {Future}-object that can be added to an iterable.
    """
    assert not asyncio.iscoroutinefunction(fn), f"{fn.__name__} appears to be a coroutine functions. This is not supported"
    return executor.submit(fn, *fn_args, **fn_kwargs)


def run_futures(futures: List[Future]):
    f"""
    Executes a list of {Future}-objects that have been created already. Note that an open {ThreadPoolExecutor} object is required for running this.
    Must be the same executor that the {Future}-objects were created with.

    :param futures: List of {Future}-objects.
    :return Returns the result in a list with the same order as the functions that the {Future}-objects were created using.
    """
    return [future.result() for future in futures]


def compile_results(functions: List[Function], results: List[Any]):
    """
    Compiles the results from a threaded execution of a bunch of functions into something where the result from a function is mapped to the name of the function
    :param functions: The list of functions.
    :param results: A list of the results from functions that ran
    :return: Returns a dict where the result from a function is mapped to the name of that function.
    """
    assert len(functions) == len(results), "The number of results is not the same as the number of functions. This should not be possible"
    zipped = zip(functions, results)
    compiled_results = ResultList()
    for z in zipped:
        f = z[0]
        r = z[1]
        result = ResultStruct(f, r)
        compiled_results.append(result)

    return compiled_results
