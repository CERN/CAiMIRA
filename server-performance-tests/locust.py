from locust import HttpUser, task, between
from gevent.pool import Group
import time 

'''
Method no. 1 - Simulation with each single user
running x requests in parallel.
Specify the desired number of parallel requests in 
"num_of_parallel_requests" variable (35 by default).

This method was used in simulations with one single
user perfoming 35 requests in parallel.
'''
# num_of_parallel_requests = 35
# class User(HttpUser):
#     wait_time = between(0.05, 0.1)
    
#     @task(1)
#     def test_api(self):
#         group = Group()
#         for i in range(0, num_of_parallel_requests):
#              group.spawn(lambda:self.client.get("/calculator-open/baseline-model/result"))
#         group.join()
#         while(1):
#             time.sleep(1)

'''
Method no. 2 - Simulation with different users 
running x requests concurrently.
With this method, each user is intended to
perform one single request.

This method was used in simulations with different
number of users requesting once at the same time.
'''
# class User(HttpUser):

#     @task(1)
#     def test_api(self):
#         self.client.get("/calculator-open/baseline-model/result")
#         while(1):
#             time.sleep(1)