# threadgroup-lib
This package is used to define thread groups and register functions to run concurrently in that group

## Usage
Using it is fairly simply and intuitive: 
```python
import threadgroup

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
```
What we do here is to define two separate groups, `first` and `second`, then register which functions we want to run in each group

### Using with varvault
[Varvault](https://github.com/data-ductus/varvault) can be leveraged to create some very interesting code that runs concurrently while also being very flexible and easy to maintain:

```python
import time
import threadgroup
import varvault

class Keyring(varvault.Keyring):
    k1 = varvault.Key("k1", valid_type=str)
    k2 = varvault.Key("k2", valid_type=int)
    k3 = varvault.Key("k3", valid_type=float)


vault = varvault.create_vault(Keyring, "vault")
sleep = 0.5
init = threadgroup.ThreadGroup()
use = threadgroup.ThreadGroup()

@init.register()
@vault.vaulter(return_keys=Keyring.k1)
def set_k1():
    time.sleep(sleep)
    return "valid"

@init.register()
@vault.vaulter(return_keys=Keyring.k2)
def set_k2():
    time.sleep(sleep)
    return 1

@init.register()
@vault.vaulter(return_keys=Keyring.k3)
def set_k3():
    time.sleep(sleep)
    return 3.14

@use.register()
@vault.vaulter(input_keys=Keyring.k1)
def use_k1(k1=None):
    time.sleep(sleep)
    assert k1 == "valid"
    return k1

@use.register()
@vault.vaulter(input_keys=Keyring.k2)
def use_k2(k2=None):
    time.sleep(sleep)
    assert k2 == 1
    return k2

@use.register()
@vault.vaulter(input_keys=Keyring.k3)
def use_k3(k3=None):
    time.sleep(sleep)
    assert k3 == 3.14
    return k3

start = time.time()
init.execute()
assert sleep - 0.2 < time.time() - start < sleep + 0.2, "Took too long to run. Concurrency seems broken"
assert Keyring.k1 in vault and vault.get(Keyring.k1) == "valid"
assert Keyring.k2 in vault and vault.get(Keyring.k2) == 1
assert Keyring.k3 in vault and vault.get(Keyring.k3) == 3.14
assert init.executed
assert use.executed is False

start = time.time()
use.execute()
assert sleep - 0.2 < time.time() - start < sleep + 0.2, "Took too long to run. Concurrency seems broken"
results = use.get_results()
```
We define a varvault object called `vault` which we set the variables to. The functions `set_k1`, `set_k2`, `set_k3` set each of the keys to the vault and they all run in the thread group `init`. 
We then use those variables in `use_k1`, `use_k2`, `use_k3`. 

The benefit of using varvault together with thread-groups is that varvault already abstracts away input variables and return variables from functions, 
allowing for a decoupled flow that works extremely well to run in thread-groups that are executed in this fashion. Since functions are registered and then executed when `execute()` is called, 
supplying input variables to the functions and handling return variables from the functions is a bit of a hassle. Varvault handles this entirely, 
allowing the user to focus on other things and running things concurrently (as much as Python will allow). 

### Running without thread groups
It's entirely possible to use the library to just run functions concurrently. This is how you may use it: 
```python
import threadgroup
from typing import List

def f1(a1):
    assert a1 == 1
    return a1

def f2(a2):
    assert a2 == 2
    return a2

def f3(a1, kw1=None):
    assert a1 == 1
    assert kw1 is True
    return a1, kw1

functions: List[threadgroup.Function] = [threadgroup.create_function(f1, 1), threadgroup.create_function(f2, 2), threadgroup.create_function(f3, 1, kw1=True)]
result: threadgroup.ResultList[threadgroup.ResultStruct] = threadgroup.threaded_execution(functions)
assert f"{result}" == "[(function=f1; result=1), (function=f2; result=2), (function=f3; result=(1, True))]"
```
What we do here is to define three different functions that each take different arguments. We then build a list of functions with their arguments. We then run those functions concurrently by calling `threadgroup.threaded_execution`.  

It's also possible to run the same function multiple times with different input parameters. This is how you'd do it:
```python
import threadgroup
from typing import List

arg_values = [1, 2, 3, 4, 5]

def f1(a1):
    assert a1 in arg_values, f"{a1} not in {arg_values}"
    return a1

functions: List[threadgroup.Function] = [threadgroup.create_function(f1, arg_value) for arg_value in arg_values]
result: threadgroup.ResultList[threadgroup.ResultStruct] = threadgroup.threaded_execution(functions)
assert f"{result}" == "[(function=f1; result=1), (function=f1; result=2), (function=f1; result=3), (function=f1; result=4), (function=f1; result=5)]"
```
In this example we also create a list of functions, but this time we do it based on the input parameters in `arg_values`, allowing it to scale easily based on an iterable.
We then do the same as previously and run the functions concurrently through `threadgroup.threaded_execution`. 
