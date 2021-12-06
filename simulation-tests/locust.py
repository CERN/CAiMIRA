import time
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    '''Time (in seconds) between the execution of each task.'''
    wait_time = between(10, 20)

    @task
    def baseline_model(self):
        self.client.get(url="/calculator-open/baseline-model/result")