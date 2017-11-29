import argparse
import matplotlib
import sqlalchemy
import urllib2
import xmldict

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import pandas as pd

from book import *

def GetTeamName(team_data):
    url = '{http://www.betfair.com/servicetypes/v1/ExchangeReadOnly/}'
    name = team_data[url + 'description'][url + 'runnerName']
    return name

def GetExchangeData(team_data):
    url = '{http://www.betfair.com/servicetypes/v1/ExchangeReadOnly/}'
    exchange_data = team_data[url + 'exchange']
    return exchange_data

def ParseRawData(data, team):
    url = '{http://www.betfair.com/servicetypes/v1/ExchangeReadOnly/}'
    exchange_data = data[url + 'GetByMarketsResponse']
    exchange_data = exchange_data[url + 'ResultSet']
    exchange_data = exchange_data[url + 'eventTypes']
    exchange_data = exchange_data[url + 'EventTypeNode']
    exchange_data = exchange_data[url + 'eventNodes']
    exchange_data = exchange_data[url + 'EventNode']
    exchange_data = exchange_data[url + 'marketNodes']
    exchange_data = exchange_data[url + 'MarketNode']
    exchange_data = exchange_data[url + 'runners']
    exchange_data = exchange_data[url + 'RunnerNode']
    team_data = exchange_data[team]
    return team_data

def PollExchange(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return xmldict.xml_to_dict(html)

def Initialise(url):
    url_prefix = '{http://www.betfair.com/servicetypes/v1/ExchangeReadOnly/}'
    data = PollExchange(url)
    team1_data = ParseRawData(data, 0)
    team2_data = ParseRawData(data, 1)

    team1 = {'name': None, 'market': None}
    team2 = {'name': None, 'market': None}
    team1['name'] = GetTeamName(team1_data)
    team2['name'] = GetTeamName(team2_data)
    team1['market'] = Book(team1['name'], url_prefix)
    team2['market'] = Book(team2['name'], url_prefix)

    return team1, team2

def main():
    parser = argparse.ArgumentParser(description='Betfair AT')
    parser.add_argument('-url', type=str, default=None)
    parser.add_argument('-db', type=str, default=None)
    args = parser.parse_args()

    index = 0
    url = args.url
    write_to_db = False

    if args.db is not None:
        engine = sqlalchemy.create_engine('sqlite:///{db}'.format(db=args.db))
        write_to_db = True

    # Initialise order books
    team1, team2 = Initialise(url)

    # Initialise lists for plotting
    team1_b_list = []
    team1_l_list = []
    team2_b_list = []
    team2_l_list = []

    while (True):
        # Scrape exchange data from website
        data = PollExchange(url)

        # Process raw data
        team1_data = ParseRawData(data, 0)
        team2_data = ParseRawData(data, 1)
        team1_exchange_data = GetExchangeData(team1_data)
        team2_exchange_data = GetExchangeData(team2_data)

        # Update books
        team1['market'].UpdateBook(team1_exchange_data)
        team2['market'].UpdateBook(team2_exchange_data)

        # Append prices to lists and plot moving window
        team1_b_list.append(team1['market'].GetTopPrice('back'))
        team1_l_list.append(team1['market'].GetTopPrice('lay'))
        team2_b_list.append(team2['market'].GetTopPrice('back'))
        team2_l_list.append(team2['market'].GetTopPrice('lay'))

        window_size = 100

        plt.clf()
        plt.step(range(max(0,index-window_size), index), team1_b_list[max(0,index-window_size):index], where='post')
        plt.step(range(max(0,index-window_size), index), team1_l_list[max(0,index-window_size):index], where='post')
        plt.step(range(max(0,index-window_size), index), team2_b_list[max(0,index-window_size):index], where='post')
        plt.step(range(max(0,index-window_size), index), team2_l_list[max(0,index-window_size):index], where='post')
        
        plt.pause(0.05)

        index = index + 1

        if write_to_db:
            team1['market'].GetPandasDepth().to_sql('team1_data', con=engine, if_exists='append')
            team2['market'].GetPandasDepth().to_sql('team2_data', con=engine, if_exists='append')

if __name__ == "__main__":
    main()