# Instructions for use (BETA)

This is a guide to help you use the calculator tool.
If you are using the expert version of the tool,  you should look at the expert notes.


## Disclaimer

The risk assessment tool simulates the long range airborne spread SARS-CoV-2 virus in a finite volume, assuming a homogenous mixture, and estimates the risk of COVID-19 infection thereto.
The results DO NOT include short-range airborne exposure (where the physical distance plays a factor) nor the other know modes of transmission of SARS-CoV-2.
Hence, this model implies that proper physical distancing, good hand hygiene and other barrier measures are ensured.
It is based on current scientific data and can be used to measures the effectiveness of different mitigation measures. 

Note that this model is based on a deterministic approach, i.e., at least one person is infected and shedding viruses into the volume.
Nonetheless, it is also important to understand that the absolute risk of infection is uncertain as it will depend on the probability that someone infected attends the event.
The model is mostly useful to compare the impact and effectiveness of mitigation measures such as ventilation, filtration, exposure time, activity and the size of the room on long-range airborne transmission of COVID-19 in indoor settings.
This application is meant for informative and educational purposes.
The user can be able to adapt different settings and measure the relative impact on the estimated infection probabilities to allow for a targeted decision making and investment.
The user should acknowledge that until the virus is in circulation among the population, the notion of 'zero risk' or a 'completely safe scenario' does not exist.
Each event is unique and the results are as accurate as the inputs.
The app is based on our scientific understanding of infectious diseases transmission, exposure and aerosol science as of November 2020. 

We do not assume responsibility for any injury or damage to persons or property arising out of or related to any use of this app.

## Usage

### Simulation Name & Room number

In order to be able to trace the risk assessments that you perform with the calculator, you can give each one a unique name - for example "Office use on Tuesday mornings".
The simulation name has no bearing on the calculation.
 
A room number is included, if you do not wish to use a formal room number any reference will do.

### Room Data

Please enter either the room volume (in m3) or both the floor area (m2) and the room height.
This information is available via GIS.

### Ventilation type

There are two main options:

#### Mechanical

If the room has mechanical ventilation (either a local or centralised system), you should select this option.
In order to make an accurate calculation you will need to know either the flow rate or the number of air changes per hour.  

#### Natural

Natural ventilation refers to rooms which have openable windows.
Please enter the number, height and width of the windows.
If there are multiple windows of different sizes, you should take an average.

The window opening distance is:

 * In the case of windows that slide, the length the window is moved open.

 * For hinged windows, it is the distance between the fixed frame and the movable glazed part when open.
 
**Notes**: If you are unsure about the opening distance for the window, it is recommended to choose a conservative value (5 cms, 0.05m or 10cms, 0.10m).
If you open the window at different distances throughout the day, choose an average value.

The width of the window is not currently used as an input to the model (height and opening distance is sufficient to calculate the free area), but is included for completeness.
When using natural ventilation, the circulation of air is simulated as a function of the difference between the temperature inside the room and the outside air temperature. The average temperature for each hour of the day has been computed for every month of the year based on historical data for Geneva, Switzerland.
It is therefore very important to enter the correct event time and date in the event data section.
Finally, you must specify when the windows are open - all the time (always), following HSE recommendations for 10 minutes every 2 hours, or during breaks (lunch and coffee breaks).
If you are unsure, we recommend choosing the 10 minutes per 2 hours option.

#### HEPA filtration

A HEPA filter is a high efficiency particulate matter filter, which removes small molecules from the air.
They can be very useful for removing virus particles from the air in an enclosed space.
The calculator allows you to simulate the installation of a HEPA air filter within the space.
The default air flow rate for the HEPA filter in the model is 250m3/hour.

### Event Data

Here we capture the information about the event being simulated.
First enter the number of occupants in the space, if you have a (small) variation in the number of people, please input the average or consider using the expert tool.
Within the number of people occupying the space, you should specify how many are infected. 

As an example, for a shared office with 4 people, where one person is infected, we enter 4 occupants and 1 infected person.

#### Activity type

There are three predefined activities in the tool at present.

**Office** = All persons seated, talking. Everyone (occupants and infected occupants) is treated the same in this model.

**Workshop** = Based on a mechanical assembly workshop, all persons are doing light exercise (standing, moving around, using tools) and talking. Everyone (occupants and infected occupants) is treated the same in this model.

**Training** = Based on a typical training course scenario. One individual (the trainer) is doing light exercise (standing) and talking, with all other individuals seated and talking quietly (whispering). In this case it is assumed that the infected person is the trainer, because this is the worst case in terms of transmission risk.
 

### Timings

You should enter the time (hours:minutes) for the start and end of the simulation period (i.e. 8:30am to 5:30pm for a typical office day).
It is important to enter the correct times for the simulation, in particular when using natural ventilation.
It is possible to specify a different time for the entry and exit of the infected person, however for most cases (where we do not know apriori which of the occupants is infected), it is recommended to set these to the same values as the activity start and end.

#### When is the event?

This is included for completeness in all simulations, however it is of particular relevance to those using natural ventilation because of variations in outside air temperature.
If you wish to simulate repetitive events, for example using an office for multiple days in the same month, choose recurrent usage.
 
Only the month is used by the model to look up outside air temperatures for the Geneva region.
 
### Breaks

#### Lunch

You have the option to specify a lunch break.
This will be useful if you plan to simulate a full working day, however you can select 'No' if it is not required for a shorter simulation.
During the lunch break it is assumed that all occupants will leave the simulated space (to go an eat lunch, somewhere else - restaurant or break room).
If you plan to eat lunch in the same area where you have been working, you should select 'No' even if a lunch break will be taken, since the risk of infection is related to the occupation of the simulated space.

### Coffee Breaks

Regular breaks are an important part of maintaining productivity during the day.
You have the option to choose no coffee breaks, 2 or 4 during the simulated period.
It is assumed that all occupants vacate the space during the break period.
If coffee breaks are taken in-situ, this option should be set to no breaks. 

When enabled, the breaks are spread evenly throughout the day - for example if we simulate the period from 9am to 6pm, with a lunch break from 1pm to 2pm, with 2 coffee breaks, one will be scheduled at 11am and the second at 4pm.
The exact timing of the breaks within the day is not particularly critical to an accurate simulation, so you do not need to be concerned about major differences if you take a coffee break at 10am instead of 11am.
The variation of coffee breaks can be altered in 5 minute increments up to 30 minutes in length.
Note that this doesn't necessarily have to be a coffee break, it can represent any period where the simulated space is vacated.
 
It should also be noted that the risk presented in the report does not take into account any potential exposures during break times.

#### Face Masks

At the time of writing, the removal of masks is authorised at workstations provided a physical distance (2m minimum) can be maintained. The model therefore includes the possibility simulate this behaviour.
Alternatively, the continuous wearing of masks can be simulated, i.e. all occupants (infected and non-infected alike) wear masks for the duration of the simulation.
 
If you have selected the Training activity type, this equates to the trainer and all participants either wearing masks throughout the training (Yes), or removing them when seated/standing at their socially distanced positions within the training room (No).


## Generate Report

When you have entered all the necessary information, please click on the Generate Report button to execute the model.


# Report

The report will open in your web browser.
It contains a summary of all the input data, which will allow the simulation to be repeated if required in future as we improve the calculation.

## Results

This part of the report shows the ``P(i)`` or probability of infection.
It is estimated based on the emission of virus into the simulated volume, and the amount which is inhaled by exposed individuals. This probability is valid for the simulation duration - i.e. if you have simulated one day and plan to work 5 days in these conditions, the cumulative probability of infection is ``(1-(1-P(i))^5)```.
If you are using the natural ventilation option, the simulation is only valid for the selected month, because the following or preceding month will have a different average temperature profile.

The ``R0`` for the simulation is calculated based on the probability of infection, multiplied by the number of exposed people. 

### Exposure graph

The graph shows the variation in the concentration of infectious quanta (one quanta is the amount of material which can cause infection if inhaled) within the simulated volume.
It is determined by:
* The presence of the infected person, who produces viral load in the space.
* The rate of production is related to the type of activity of the infected person (sitting, light exercise), their level of vocalisation (whispering or talking).
* The accumulation of infectious quanta in the space is driven by ventilation (either natural or mechanical, and or HEPA filtration).
    * In a mechanical ventilation scenario, the removal rate is constant, based on air flow in and out of the simulated space.
    * Under natural ventilation conditions, the effectiveness of ventilation relies upon the temperature difference between the inside and outside air temperature.
    * A HEPA filter removes infectious quanta from the air at a constant rate and is modelled in the same way as mechanical ventilation, however air passed through a HEPA filter is recycled not renewed (i.e. it is not fresh air). 

# Conclusion

This tool provides illustrations for COVID-19 Airborne risk only.
If you have any comments on your experience with the app, or feedback for potential improvements, please share them with the development team at cara-dev@cern.ch.
