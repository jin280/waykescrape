from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import argparse


# URL to scrape
URL = "https://www.wayke.se/sok/stockholm"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=2)
    parser.add_argument('--mean_normalize', type=bool, default=False)
    parser.add_argument('--current_year', type=int, default=2023)
    parser.add_argument('--price_limit', type=int, default=200000)
    parser.add_argument('--headless', type=bool, default=True)
    args = parser.parse_args()

    url = URL
    timeout = args.timeout
    mean_normalize = args.mean_normalize
    current_year = args.current_year
    price_limit = args.price_limit
    headless = args.headless

    # string of the html pages
    htmlTotal = ''

    if headless:
        # open browser headless
        options = webdriver.FirefoxOptions()
        options.headless = True
        driver = webdriver.Firefox(options=options)
    else:
        driver = webdriver.Safari()
    driver.get(url)
    # wait until page is rendered
    time.sleep(timeout)

    # click a button that says Håller med och fortsätt
    driver.find_element(By.XPATH, "//button[contains(.,'Håller med')]").click()

    # iterate every element in pagination-list class and click it
    i = 1
    while True:
        try:
            # get html
            htmlTotal += driver.page_source
            i += 1
            # get button that has title Sida i
            driver.find_element(
                By.XPATH, "//button[text()='" + str(i) + "']").click()
            time.sleep(timeout)
            print(f"Page {i} loaded")
        except Exception as e:
            print("Error on page " + str(i), e)
            break

    soup = BeautifulSoup(htmlTotal, 'html.parser')

    # find all divs with class "product-card-body"
    divs = soup.find_all('div', class_='product-card-body')

    # make an empty df with columns for driven mil, price, year, fuel type, transmission, and model
    df = pd.DataFrame(columns=['Driven mil', 'Price',
                               'Year', 'Fuel type', 'Transmission', 'Model'])

    # loop through divs
    for div in divs:
        # get element with a
        a = div.find('a')
        # contruct url from href
        url = 'https://www.wayke.se' + a['href']
        model = a.text
        # get ul with class "product-card-usp-list"
        ul = div.find('ul', class_='product-card-usp-list')
        # the first li is year, second is driven mil, third is transmission, fourth is fuel type
        lis = ul.find_all('li')
        year = lis[0].text
        driven_mil = lis[1].text
        transmission = lis[2].text
        fuel_type = lis[3].text
        # find div with class "product-card-price-value"
        price_div = div.find('div', class_='product-card-price-value')
        price = price_div.text
        # if any value is empty, skip
        if not (model and year and driven_mil and transmission and fuel_type and price):
            continue
        # if year is more than current year, skip
        if int(year) >= current_year:
            continue
        # add all data to df with concat
        df = pd.concat([df, pd.DataFrame([[driven_mil, price, year, fuel_type, transmission, model]], columns=[
            'Driven mil', 'Price', 'Year', 'Fuel type', 'Transmission', 'Model'])])

    # keep only trasmission = Automat
    df = df[df['Transmission'] == 'Automat']

    # remove any non-numeric characters from driven mil, price, year
    df['Driven mil'] = df['Driven mil'].str.replace(r'\D', '')
    df['Price'] = df['Price'].str.replace(r'\D', '')
    df['Year'] = df['Year'].str.replace(r'\D', '')

    # convert columns driven mil, price, year to numeric
    df['Driven mil'] = pd.to_numeric(df['Driven mil'].str.replace(' mil', ''))
    df['Price'] = pd.to_numeric(df['Price'].str.replace(' kr', ''))
    df['Year'] = pd.to_numeric(df['Year'].str.replace(' år', ''))

    # if driven mil or price is 0, drop row
    df = df[df['Driven mil'] != 0]
    df = df[df['Price'] != 0]

    if price_limit:
        df = df[df['Price'] <= price_limit]

    # drop transmission
    df = df.drop('Transmission', axis=1)

    # create column score
    df['Score'] = 0.0

    # copy driven mil, price, year to new columns
    df['Driven mil copy'] = df['Driven mil']
    df['Price copy'] = df['Price']
    df['Year copy'] = df['Year']

    # inverse value for driven mil, and price
    df['Driven mil copy'] = df['Driven mil copy'].apply(
        lambda x: 1/x if x != 0 else 1)
    df['Price copy'] = df['Price copy'].apply(lambda x: 1/x if x != 0 else 1)

    if mean_normalize:
        # mean normalize copies driven mil, price, year
        df['Driven mil copy'] = (
            df['Driven mil copy'] - df['Driven mil copy'].mean()) / df['Driven mil copy'].std()
        df['Price copy'] = (df['Price copy'] -
                            df['Price copy'].mean()) / df['Price copy'].std()
        df['Year copy'] = (df['Year copy'] - df['Year copy'].mean()
                           ) / df['Year copy'].std()
    else:
        # min max normalize copies driven mil, price, year
        df['Driven mil copy'] = (df['Driven mil copy'] - df['Driven mil copy'].min()) / (
            df['Driven mil copy'].max() - df['Driven mil copy'].min())
        df['Price copy'] = (df['Price copy'] - df['Price copy'].min()) / \
            (df['Price copy'].max() - df['Price copy'].min())
        df['Year copy'] = (df['Year copy'] - df['Year copy'].min()) / \
            (df['Year copy'].max() - df['Year copy'].min())

    # create column for average mil per year
    df['mil per year'] = df['Driven mil'] / (current_year - df['Year'])

    # make int
    df['mil per year'] = df['mil per year'].astype(int)

    # copy mil per year to new column
    df['mil per year copy'] = df['mil per year']

    # inverse value for mil per year, if mil per year is 0, set to 1
    df['mil per year copy'] = df['mil per year copy'].apply(
        lambda x: 1/x if x != 0 else 1)

    if mean_normalize:
        # mean normalize mil per year
        df['mil per year copy'] = (
            df['mil per year copy'] - df['mil per year copy'].mean()) / df['mil per year copy'].std()
    else:
        # min max normalize mil per year
        df['mil per year copy'] = (df['mil per year copy'] - df['mil per year copy'].min()) / (
            df['mil per year copy'].max() - df['mil per year copy'].min())

    # sort by price
    df = df.sort_values(by='Price')

    # score is the mean
    df['Score'] = df[['Driven mil copy', 'Price copy',
                      'Year copy', 'mil per year copy']].mean(axis=1)

    df = df.sort_values(by='Score', ascending=False)

    # get unique fuel types
    fuel_types = df['Fuel type'].unique()

    # get the lowest score for each fuel type
    for fuel_type in fuel_types:
        # select rows with fuel type
        df_fuel_type = df[df['Fuel type'] == fuel_type]
        # get the highest score
        lowest_score = df_fuel_type['Score'].max()
        # get and print the row with the lowest score
        row = df_fuel_type[df_fuel_type['Score'] == lowest_score]
        print(
            f"For fuel type {fuel_type} the best car is: {row['Model'].values[0]}")

    # export to csv
    df.to_excel('cars.xlsx', index=False)


if __name__ == "__main__":
    main()
