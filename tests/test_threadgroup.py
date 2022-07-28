import time

from commons import *


class TestThreadGroup:
    def test_thread_group(self):
        test = threadgroup.ThreadGroup()

        @test.register()
        def f1():
            time.sleep(0.1)
            pass

        @test.register()
        def f2():
            time.sleep(0.1)
            pass

        @test.register()
        def f3():
            time.sleep(0.1)
            pass

        @test.register()
        def f4():
            time.sleep(0.1)
            pass

        start = time.time()
        test.execute()
        time_spent = time.time() - start
        assert test.executed
        assert 0.01 < time_spent < 0.2, f"(Threaded) Time spent ({time_spent}) is not within the permitted interval"

    def test_multiple_functions(self):
        test = threadgroup.ThreadGroup()

        @test.register()
        def f1():
            pass

        def shouldnt_run():
            assert False, f"Function {shouldnt_run.__name__} ran anyway"

        test.execute()
        assert test.executed

    def test_args_and_kwargs(self):
        test = threadgroup.ThreadGroup()

        @test.register(1, 2, kw1=True, kw2=False)
        def f1(a1, a2, kw1=None, kw2=None):
            assert a1 == 1
            assert a2 == 2
            assert kw1 is True
            assert kw2 is False

        test.execute()

        assert test.executed

    def test_update_fn_args(self):
        test = threadgroup.ThreadGroup()

        @test.register()
        def f1(a1, a2, kw1=None):
            assert a1 == 1
            assert a2 == 2
            assert kw1 is True

        test.update_fn_args(f1, 1, 2, kw1=True)

        test.execute()
        assert test.executed

    def test_multiple_groups_run_only_one(self):
        test = threadgroup.ThreadGroup()
        dont_run = threadgroup.ThreadGroup()

        @test.register()
        def f1():
            pass

        @dont_run.register()
        def d1():
            assert False, f"Function {d1.__name__} ran anyway"

        test.execute()
        assert test.executed
        assert dont_run.executed is False

    def test_run_multiple_groups(self):
        first = threadgroup.ThreadGroup()
        second = threadgroup.ThreadGroup()

        @first.register()
        def f1():
            pass

        @first.register()
        def f2():
            pass

        @second.register()
        def s1():
            pass

        @second.register()
        def s2():
            pass

        first.execute()
        assert first.executed
        assert second.executed is False

        second.execute()
        assert second.executed
