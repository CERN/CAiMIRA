## [CAiMIRA Calculator](https://caimira.web.cern.ch/)

This tool simulates the airborne spread of SARS-CoV-2 virus in a finite volume and estimates the risk of COVID-19 infection. It is based on current scientific data and can be used to compare the effectiveness of different mitigation measures.

### Virus data

SARS-CoV-2 covers the original "wild type" strain of the virus and three variants of concern (VOC):
- Alpha (also known as B.1.1.7, first identified in UK, Sept 2020),
- Beta (also known as B.1.351, first identified in South Africa, May 2020).
- Gamma (also known as P.1, first identified in Brazil/Japan, Jan 2021).
- Delta (also known as B.1.617.2, first identified in India, Oct 2020).
- Omicron (also known as B.1.1.529, first identified in South Africa, November 2021).

Modify the default as necessary, according to local area prevalence e.g. for [Geneva](https://www.covid19.admin.ch/fr/epidemiologic/virus-variants?geo=GE). <!-- #REMOVE? -->

### Ventilation data

- Mechanical ventilation = the HVAC supply of fresh air. Check the flow rates with the concerned technical department.
- Natural ventilation = the type of window opening. The opening distance is between the fixed frame and movable part when open (commonly used values are window height of 1.6m and window opening between 0.15m and 0.6m). In case of periodic opening, specify the duration (e.g. 10 min) per hour.
- HEPA filtration = the air flow of the device. The following values are based on the different fan velocities of a specific commercial device proposed by the HSE Unit:
    - Level 6 (max) = 430 m3/h (noisy),
    - Level 5 = 250 m3/h (ok w.r.t. noise, recommended),
    - Level 4 = 130 m3/h (silent),
    - Level 3 = 95 m3/h (silent).

### Activity types

The type of activity applies to both the infected and exposed persons:
- Office = all seated, talking 33% of the time,
- Small meeting (< 10 occ.) = all seated, talking time shared between all persons,
- Large meeting (>= 10 occ.) = speaker is standing and speaking 33% of the time, other occupants are seated,
- Call Centre = all seated, continuous talking,
- Control Room (day shift) = all seated, talking 50% of the time,
- Control Room (night shift) = all seated, talking 10% of the time,
- Library = all seated, no talking, just breathing,
- Laboratory = light physical activity, talking 50% of the time,
- Workshop = moderate physical activity, talking 50% of the time,
- Conference/Training (speaker infected) = speaker/trainer standing and talking, rest seated and talking quietly. Speaker/Trainer assumed infected (worst case scenario),
- Conference/Training (attendee infected) = someone in the audience is infected, all are seated and breathing.
- Gym = heavy exercise, no talking, just breathing.

### Activity breaks

If coffee breaks are included, they are spread out evenly throughout the day, in addition to any lunch break (if applicable).

Refer to the [Full Guide](full_guide.md) for more detailed explanations on how to use this tool.