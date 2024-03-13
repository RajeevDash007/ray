# __pattern_start__
import ray
import time
from numpy import random

# Initialize Ray
ray.init()

def partition(collection):
    # Use the last element as the pivot
    pivot = collection.pop()
    greater, lesser = [], []
    for element in collection:
        if element > pivot:
            greater.append(element)
        else:
            lesser.append(element)
    return lesser, pivot, greater


def quick_sort(collection):
    if len(collection) <= 200000:  # magic number
        return sorted(collection)
    else:
        lesser, pivot, greater = partition(collection)
        lesser = quick_sort(lesser)
        greater = quick_sort(greater)
    return lesser + [pivot] + greater


@ray.remote
def quick_sort_distributed(collection):
    # Tiny tasks are an antipattern.
    # Thus, in our example we have a "magic number" to
    # toggle when distributed recursion should be used vs
    # when the sorting should be done in place. The rule
    # of thumb is that the duration of an individual task
    # should be at least 1 second.
    threshold = 200000

    if len(collection) <= threshold:
        return sorted(collection)
    else:
        lesser, pivot, greater = partition(collection)

        # Recursive calls
        lesser_ref = quick_sort_distributed.remote(lesser)
        greater_ref = quick_sort_distributed.remote(greater)

        # Efficiently pass ObjectRefs instead of data
        return ray.get(lesser_ref), pivot, ray.get(greater_ref)


for size in [200000, 4000000, 8000000]:
    print(f"Array size: {size}")
    unsorted = random.randint(1000000, size=(size)).tolist()
    s = time.time()
    quick_sort(unsorted)
    print(f"Sequential execution: {(time.time() - s):.3f}")

    s = time.time()
    # Adjust resources dynamically based on workload and available cores
    with ray.dynamic_resources(cpu=0):
        result = ray.get(quick_sort_distributed.remote(unsorted))
    print(f"Distributed execution: {(time.time() - s):.3f}")
    print("--" * 10)

# Shutdown Ray
ray.shutdown()


# Outputs:

# Array size: 200000
# Sequential execution: 0.040
# Distributed execution: 0.152
# --------------------
# Array size: 4000000
# Sequential execution: 6.161
# Distributed execution: 5.779
# --------------------
# Array size: 8000000
# Sequential execution: 15.459
# Distributed execution: 11.282
# --------------------

# __pattern_end__
