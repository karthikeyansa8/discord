import timeit

def timed_api(api_request_to_time):
    def wrapper(*args,**kwargs):
        start_time = timeit.default_timer()
        response = api_request_to_time(*args,**kwargs)
        end_time = timeit.default_timer()
        execution_time = end_time - start_time
        print(f"Execution time for {api_request_to_time.__name__}: {execution_time} seconds")
        return response,execution_time
    return wrapper

@timed_api
def print_hello():
    print("hello")
    a = "5"
    a = int(a)

if __name__ == '__main__':
    print_hello()   