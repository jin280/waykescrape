# Used Cars Scoring Program 

This code finds used cars in Stockholm and gives them scores based on different variables. It uses Selenium and BeautifulSoup to scrape data from a car database and then stores it in a pandas dataframe. It then uses the data from the dataframe to calculate a score for each car. The cars are then sorted by score and the best car for each fuel type is printed. The data is also exported to an Excel file. 

## Usage 

The code can be run using Python 3. It takes several command line arguments, including the timeout, mean normalize, current year, price limit, and headless. These can be used to customize the program to fit whatever criteria you would like. 

## Output 

The program outputs the best car for each fuel type as well as an Excel spreadsheet with the data from all of the cars.