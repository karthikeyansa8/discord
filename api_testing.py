import requests
from wrapper_tools import timed_api

@timed_api
def daily_report_performance():
    response = requests.get(url="https://api.learnbasics.fun/report/generate/?report_type=1",timeout=300,json={
    "school_test_ids":[1200]
    })
    return response

if __name__ == "__main__":
    reponse,execution_time = daily_report_performance()
    
    print(reponse,execution_time)