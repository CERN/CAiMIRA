#### Disclaimer

The following list includes the open-source dependencies used in this project, along with their respective licenses. It covers both the core dependencies explicitly specified in the project's requirements, as well as their transitive dependencies (dependencies of dependencies).

Including transitive dependencies is essential to acknowledge the full spectrum of open-source contributions that contribute to the functionality of this project. It also ensures compliance with open-source licenses and recognizes the efforts of all contributors, even those indirectly involved.

## External Libraries

??? "Back-end (Python) Dependencies"
??? "Front-end (JavaScript) Dependencies"

    #### jQuery 3.5.1

    - License: [MIT License](https://github.com/jquery/jquery/blob/main/LICENSE.txt)

    #### jQuery Colorbox

    - License: [MIT License](https://github.com/jackmoore/colorbox/blob/1.6.4/LICENSE.md)

    #### ScrollMagic

    - License: [MIT License](https://github.com/janpaepke/ScrollMagic/blob/v2.0.5/LICENSE.md)

    #### Twitter Bootstrap 4.5.3

    - License: [MIT License](https://github.com/twbs/bootstrap/blob/v4.5.3/LICENSE)

    #### d3.js

    - License: [ISC License](https://github.com/d3/d3/blob/v7.8.5/LICENSE)


??? "Other references"

    #### Rest Countries

    - License: [MP License 2.0](https://gitlab.com/restcountries/restcountries/-/blob/master/LICENSE?ref_type=heads)

    #### WHO COVID-19 Global Data

    - Endpoint: `https://covid19.who.int/WHO-COVID-19-global-data.csv`

    #### ArcGIS Geocode

    - Endpoint: `https://geocode.arcgis.com`

    #### View Hub Resources

    - Endpoint: `https://view-hub.org/resources`

    #### CERN Web Analytics

    - Endpoint: `https://webanalytics.web.cern.ch/`

    #### Zenodo Badge

    - Endpoint: `https://zenodo.org/badge/DOI/10.5281/zenodo.6520431.svg`
    - Description: Zenodo itself does not impose any specific license on the content that is deposited. Instead, it allows the depositor to choose the license for their content. This means that the permissiveness of the Zenodo badge (with the DOI) depends entirely on the license chosen by the person depositing the content.

    #### Swiss COVID-19 Data

    - Endpoint: `https://www.covid19.admin.ch/en/epidemiologic/case/d/development?epiRelDev=abs`

    ### External APIs

    - **Geographical location**:

        There is one external API call to fetch required information related to the geographical location inserted by a user.
        The documentation for this geocoding service is available at [https://developers.arcgis.com/rest/geocode/api-reference/geocoding-suggest.htm](https://developers.arcgis.com/rest/geocode/api-reference/geocoding-suggest.htm) .
        Please note that there is no need for keys on this API call. It is **free-of-charge**.

    - **Humidity and Inside Temperature**:

        For the `CERN theme` as the authorized sensors are installed at CERN.

    - **ARVE**:

        The ARVE Swiss Air Quality System provides trusted air data for commercial buildings in real-time and analyzes it with the help of AI and machine learning algorithms to create actionable insights. Terms and Conditions available here [https://www.arveair.com/terms-and-conditions/](https://www.arveair.com/terms-and-conditions/).

        Create secret:

            $ read ARVE_CLIENT_ID
            $ read ARVE_CLIENT_SECRET
            $ read ARVE_API_KEY
            $ oc create secret generic \
            --from-literal="ARVE_CLIENT_ID=$ARVE_CLIENT_ID" \
            --from-literal="ARVE_CLIENT_SECRET=$ARVE_CLIENT_SECRET" \
            --from-literal="ARVE_API_KEY=$ARVE_API_KEY" \
            arve-api

    - **CERN Data Service**:

        The CERN data service collects data from various sources and expose them via a REST API endpoint.
        The service is enabled when the environment variable `DATA_SERVICE_ENABLED` is set to 1.

### License Distribution

![License Distribution Pie Chart](license_distribution.png)

## List of Open Source Licenses

The list of open-source dependencies provided here includes licenses for both direct dependencies and dependencies of dependencies. This comprehensive list covers a wide range of licenses, each with its own terms and conditions. Below is a summary of the most frequently encountered licenses along with their descriptions and usage:

1. **MIT License**
    - The MIT License is a permissive free software license originating at the Massachusetts Institute of Technology (MIT). It is a short and simple license that allows developers to use, modify, and distribute the software for both commercial and non-commercial purposes.

2. **Apache License, Version 2.0**
    - The Apache License, Version 2.0 is a widely used open-source software license that allows users to use the software for any purpose, to distribute it, to modify it, and to distribute modified versions of the software under the terms of the license.

3. **Berkeley Software Distribution License (BSDL)**
    - The BSD License is a family of permissive free software licenses that allow users to do anything they want with the source code, as long as they include the original copyright and license notice in any copy of the code or substantial portion of it.

4. **Mozilla Public License 2.0 (MPL)**
    - The Mozilla Public License is a free and open-source software license developed and maintained by the Mozilla Foundation. It is a copyleft license, which means that derived works can only be distributed under the same license terms.

5. **Python Software Foundation Licene (PSFL)**
    - The Python Software Foundation License (PSFL) is a BSD-style, permissive software license which is compatible with the GNU General Public License (GPL).[1] Its primary use is for distribution of the Python project software and its documentation. Since the license is permissive, it allows proprietization of the derivations.

6. **Internet Systems Consourtium License (ISCL)**
    - The ISC license is a permissive free software license published by the Internet Software Consortium, now called Internet Systems Consortium (ISC). It is functionally equivalent to the simplified BSD and MIT licenses.

7. **Historical Permission Notice and Disclaimer License (HPND)**
    - The Historical Permission Notice and Disclaimer (HPND) is an open source license, approved by the Open Source Initiative (OSI) and verified as GPL-compatible by the Free Software Foundation. The license can be almost functionally identical to the new, 3-clause BSD License (if the option for the no-promotion clause is exercised), or the MIT License (if the option for the no-promotion clause is not exercised).

8. **GNU General Public License 2.0 or later (GPL-2.0-or-later)**

    - The GNU General Public License (GPL) is a copyleft license that allows users to modify and distribute software. Any modified versions must also be distributed under the GPL. The "or later" part means that the software can be distributed under any later version of the GPL as well. GPL ensures that software remains free and open-source.  
    
9. **GNU Lesser General Public License 2.1 or later (LGPL-2.1-or-later)**

    - The GNU Lesser General Public License (LGPL) is a more permissive version of the GPL, specifically intended for software libraries. It allows proprietary software to link to LGPL-licensed libraries without requiring the proprietary software itself to be open-source. Like the GPL, the LGPL requires modifications to the LGPL-licensed software to be released under the LGPL.

10. **Expat License (also known as MIT License)**

    - The Expat License is an open-source license that is functionally identical to the MIT License. It is a permissive license that allows users to modify and distribute the software. The Expat license is commonly used in projects like XML parsing libraries and other lightweight open-source software.

11. **Dual License**

    - A dual license means that the software is distributed under two different licenses, and the user can choose which one to comply with. This is commonly used to provide a more permissive license for open-source usage and a more restrictive commercial license for proprietary use. For example, a project may be available under both the MIT License and the GPL.
