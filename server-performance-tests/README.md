# locust

A simple open source load testing tool that allows to define user behavior.

In order to set it up for the first time, we followed the documentation at https://locust.io/. In particular, we:

* Defined a class for the users that will be simulating.
* Defined a ``wait_time`` variable that will make the simulated users wait between the specified seconds after each task executed.
* Decorated our method with ``@Task`` that creates a micro-thread that calls this method.
* Defined the ``self.client`` attribute that makes it possible to make HTTP calls that will be logged by Locust.

To use, uncomment the desired method on ``lucust.py``` file, open the terminal on this folder and run the following command:

``locust -f locust.py --host https://cara.web.cern.ch``

Then, open up a browser and point it to http://localhost:8089. 
By default we pointed out the test to our own web server.
``Start swarming`` will trigger the simulation.