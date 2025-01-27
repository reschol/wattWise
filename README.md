# This is the repository of the WattWise Spezialveranstaltung Project 2024

## Vorwort von Betreuer

We provide some initial files for a quick start, which in large parts are based on the Agri-PV Plant Optimization project by Joshua Spreng.

*The project is structured as follows*
- The main.py file is the entry point of the program and contains the main functions to run the optimization process.
- src/util contains utility functions for retrieving data from Entso-e and Renewables.ninja

*for executing the code you need working API keys for Renewables.ninja and Entso-e. Also install the requirements by calling pip install -r requirements.txt*.  
If you use additional packages please add that to the requirements file
 
## Open TODOS
- [x] Zeitkomponente fixen. 
  - Beispielsweise betrachte ich zum Model "trainieren" 2019. Sage dann aber die Daten vor für 2019. Natürlch ist das da dann besser. Ich muss die Zeit für 2020 vorhersagen. Bzw. die letzten 2 Jahre nehmen, die überhaupt verfügbar sind. bzw von den 2 Wochen an ein Jahr.
- [x] ~~SChleife bauen, wo Customer Haushalt jeweils aus dem Testdatensatz rausgenommen wird. Momentan ist er noch drin.~~ 
  - ist rausgefallen, da wir Testdatensatz nicht mehr zur Berechnung des SLPs nehmen. Allgemeines SLP geeigneter.
- [x] Modell verbessern:   
  - [x] nur die zwei Wochen als Vorhersage Basis benutzen
  - [x] keine Daten der zwei Wochen benutzen, STandard Load Profile normed (einfach mal googeln)
- [ ] Code schön schreiben mit Methoden


## Code TODO
- [ ] Define the missing variable. Replace with actual values. Momentan noch Daten aus 2024 VON Tibber
  - consumption_dependent_fixed_costs = 19.71  # ct per KwH 2024 value Tibber - Example value, replace with actual value
  - Consumption_independent_base_price = 15.73  # €/Monat - 2024 value Tibber - Example value, replace with actual value
-  [ ] Predict the load using weighted averages. Hier noch mehr weights ausprobieren. Was ist das beste?  
   -  Momentan: deferentiate between offseason and season
      -  weight_offseason_twoweeks = 0.5
      -  weight_offseason_SLP = 0.5
      -  weight_twoweeks = 0.7
      -  weight_SLP = 0.3