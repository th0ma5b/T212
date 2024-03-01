from trading212_rest import Trading212
import pandas as pd
from enum import Flag, auto
import os
import glob

class Mode(Flag):
    VERBOSE = auto()
    DEBUG = auto()
    DUMP_DF_TO_FILE = auto()

# Notes:
# - return tickers in a stockopedia format.
# - can return them for the whole exchange, or your portfolio
# - can be filtered by exchange, instrument type (STOCK, ETF, etc...)
#
# - Note difference between t212 tickers and tickers (generic)
#
# TODOs:
# - write to json file and read back from json file in debug mode. So less access to server.
# - get_position() should take google format? instead of t212 format?
# - issue with NSQ being NMQ in stockopedia for Gravity ticker GRVY
# - convert stockopedia ticker name to Trading212 name? long name...

# New class which return dataframes and lists
class T212(Trading212):
    """My API client for Trading212"""
    """Dependency: Rest API client for Trading212"""


    ### Class variables:
    # Create a mapping between 3-letter exchange code and the word to search in exchanges['name'] string
    # The google prefix is used: see https://stockmarketmba.com/globalstockexchanges.php
    # stockopedia uses google prefix, but not always (see WBAG/Vienna).
    # other problem, Trading212 has 3 exchanges for LON ('LON-NON-ISA', 'LON', 'AIM')

    exchcode_2_exchanges_df_name_d = {
        'AMS':            'Euronext Amsterdam',  
        'BIT':                'Borsa Italiana',  
        'NSQ':                        'NASDAQ',  
        'LON-NON-ISA': 'London Stock Exchange NON-ISA', # LON
        'EPA':                'Euronext Paris',  
        'OTC':                   'OTC Markets',  
        'SWX':            'SIX Swiss Exchange',  
        'LON':         'London Stock Exchange',  # LON.  Warning: this string is also part of AIM and NON-ISA, so make sure perform comparison over the full string.
        'MAD':               'Bolsa de Madrid',  
        'WBAG':                 'Wiener Börse',  # stockopedia prefix instead, not google prefix.
        'NYQ':                          'NYSE',  
        'EBR':             'Euronext Brussels',  
        'ELI':               'Euronext Lisbon',  
        'FRA':          'Deutsche Börse Xetra',  
        'AIM':     'London Stock Exchange AIM', # LON
    }


    # All LON-NON-ISA, LON and AIM are the same LON
    exchanges_df_name_2_exchode_d = {
                   'Euronext Amsterdam':'AMS' ,  
                       'Borsa Italiana':'BIT' ,  
                               'NASDAQ':'NSQ' ,  
        'London Stock Exchange NON-ISA':'LON' , # LON
                       'Euronext Paris':'EPA' ,  
                          'OTC Markets':'OTC' ,  
                   'SIX Swiss Exchange':'SWX' ,  
                'London Stock Exchange':'LON' ,  # LON.
                      'Bolsa de Madrid':'MAD' ,  
                         'Wiener Börse':'WBAG',  # stockopedia prefix instead, not google prefix.
                                 'NYSE':'NYQ' ,  
                    'Euronext Brussels':'EBR' ,  
                      'Euronext Lisbon':'ELI' ,  
                 'Deutsche Börse Xetra':'FRA' ,  
            'London Stock Exchange AIM':'LON' , # LON
    }


    def get_latest_file(path, *paths):
        """Returns the name of the latest (most recent) file 
        of the joined path(s)"""
        fullpath = os.path.join(path, *paths)
        files = glob.glob(fullpath)  # You may use iglob in Python3
        if not files:                # I prefer using the negation
            return None                      # because it behaves like a shortcut
        latest_file = max(files, key=os.path.getctime)
        _, filename = os.path.split(latest_file)
        return filename

#    def json_data_to_dataframe(json_data, dict_not_list=None):
#        if dict_not_list:
#            json_data = [json_data]
#        
#        df = pd.DataFrame(json_data)


    def __try_load_df_from_json_file(self, filename):
        """ Load df from t212 server or from a file if in debug mode"""
        """ if file does not exists, then create it"""
        if Mode.DEBUG in self.mode:

            # Create directory
            dirname='db_t212' # dirname='stockopedia_db'
            try:
                os.makedirs(dirname)
            except FileExistsError:
                # directory already exists
                pass

            # Get most recent previous file name (before writing new one)
            prev_file=T212.get_latest_file(dirname, f'{filename}*')

            if prev_file is None:
                return None

            prev_file = os.path.join(dirname, prev_file)

            print(f'Loading df from {prev_file}')
            return pd.read_json(prev_file, orient='index')

        return None
                



    def __init__(self, my_api_key: str, demo: bool = True, mode: Mode=Mode(0)):
        Trading212.__init__(self, api_key=my_api_key, demo=demo)

        self.mode = mode

        # Access server only once at init, dump json data into dataframes
        self.exch_df = self.__try_load_df_from_json_file('t212_exchanges')
        if self.exch_df is None:
            print(f'Loading exch_df from Trading212 server')
            self.exch_df = pd.DataFrame(self.exchanges())
        print(f"\nexch_df=\n{self.exch_df}")

        self.pf_df = self.__try_load_df_from_json_file('t212_portfolio') # fails due to file format, TODO redump it first and then use it
        #self.pf_df = None
        if self.pf_df is None:
            print(f'Loading pf_df from Trading212 server')
            pf_list = self.portfolio()
            # Convert JSON data to Pandas DataFrame
            self.pf_df = pd.DataFrame(pf_list)
        print(f"\npf_df=\n{self.pf_df}")
        #print(f"\ntype pf_df={type(self.pf_df)}")

        self.instr_df = self.__try_load_df_from_json_file('t212_instruments')
        if self.instr_df is None:
            print(f'Loading instr_df from Trading212 server')
            instr_pf_list = self.instruments()
            # Convert JSON data to Pandas DataFrame
            self.instr_df = pd.DataFrame(instr_pf_list)
        print(f"\ninstr_df=\n{self.instr_df}")

        #if mode & mode.DEBUG == mode.DEBUG:
        if Mode.DUMP_DF_TO_FILE in self.mode:
            print("TODO: dump to json file")
            # filename = 'tmp/t212_exchanges.json'
            # exch_df.to_json(filename, orient='index') # The orient parameter defaults to 'columns'.
            


        # exchanges could also be loaded from a file if server goes wrong:
        #     # WA timing error exception so load data from a file - this was because it was called many times!
        #     prev_file = 'tmp/t212_exchanges.json'
        #     print(f'Loading prev_df from {prev_file}')
        #     exch_df = pd.read_json(prev_file, orient='index')

    def equity_orders_df(self):
            orders_l = self.equity_orders()
            orders_df = pd.DataFrame(orders_l)
            return orders_df

    def portfolio_df(self):
            pf_df = self.pf_df
            return pf_df

    def position(self, ticker): # if ticker is not part of portfolio, then it returns an empty dataframe
        if ticker is None:
            pf_df = self.pf_df
        else:
            t212_ticker = ticker
            pf_df = self.pf_df.loc[self.pf_df['ticker'] == t212_ticker]
        return pf_df


    # exchid parameter is the instrument workingScheduleId for now
    # it would be better if it was the exchange id, but there multiple workingScheduleId per exchange.
    # ir would be even better if could use the exchage 3-letter codename.
    # def instruments_df(self, typ=None, exchid=None): # e.g. typ = "STOCK"
    #     instr_df = self.instr_df

    #     if typ is not None:
    #         instr_df = instr_df.loc[(instr_df['type'] == typ)]
    #     if exchid is not None:
    #         instr_df = instr_df.loc[(instr_df['workingScheduleId'] == exchid)] # Filtered on exchange id

    #     #instr_lon_df = instr_df.loc[(instr_df["type"] == "STOCK") & (instr_df['currencyCode'] == "GBX") &
    #     #                            (instr_df['workingScheduleId'] != 101) & (instr_df['workingScheduleId'] != 100)]

    #     #print(f"\nfiltered instr_df={instr_df}")
    #     return instr_df

    # exchcode: 3-letter exchange id codename,  to choose from : 
    def instruments_df(self, typ=None, exchcode=None): # e.g. typ = "STOCK"
        instr_df = self.instr_df
        #print(f"{instr_df.loc[(instr_df['ticker'] == 'GTLYl_EQ')]}") # debug

        if typ is not None:
            instr_df = instr_df.loc[(instr_df['type'] == typ)]

        if exchcode is not None:
            workingScheduleIds = self.exchcode_2_workingScheduleIds(exchcode)
            print(f"workingScheduleIds={workingScheduleIds}")
            # instr_df Filtered on exchange id
            my_mask = instr_df['workingScheduleId'].isin(workingScheduleIds) # the .isin() method returns a boolean Series indicating whether each element in the column is contained in the given list.
            instr_df = instr_df[my_mask]

        print(f"\nfiltered instr_df={instr_df}")
        return instr_df


    def exchanges_df(self):
        return self.exch_df

    def get_exchcodes(self):
        return T212.exchcode_2_exchanges_df_name_d.keys()


    # e.g. 'GOOGL_US_EQ'
    def get_pf_t212_tickers(self):
        pf_df = self.portfolio_df()
        t212_pf_tickers = pf_df['ticker'].tolist()
        return t212_pf_tickers


    def __t212_get_pf_tickers_and_instr_df_and_mask(self, typ=None, exchcode=None, subtyp='NO_PRF'): # generic tickers
        # Now convert t212 tickers to generic tickers:
        # using instruments information
        # # e.g. 'GOOGL_US_EQ' -> 'GOOGL'
        # # can use instruments columns: ticker -> shortName
        t212_pf_tickers = self.get_pf_t212_tickers()
        #print(f"t212_pf_tickers={t212_pf_tickers}")
        #t212_pf_tickers = ['GSKl_EQ', 'GTLYl_EQ'] # debug
        instr_df = self.instruments_df(typ, exchcode)

        if subtyp == 'NO_PRF':
            # Remove preferrence shares
            #instr_df = instr_df[instr_df['name'].str.contains('% PRF|(Preference)', regex=False) == False]
            #instr_df = instr_df[instr_df['name'].str.contains('% PRF|\(Preference\)') == False]
            instr_df = instr_df[instr_df['name'].str.contains(' PRF|\(Preference\)') == False] # also exclude "Bristol & West PRF"

        pf_mask = instr_df['ticker'].isin(t212_pf_tickers) # the .isin() method returns a boolean Series indicating whether each element in the column is contained in the given list.
        #print(f"\nmask={instr_df[pf_mask]}") # print the resulting DataFrame, containing only the rows that match the mask
        tickers_short = instr_df[pf_mask]['shortName'].tolist()
        #print(f"\ngeneric_tickers={tickers)short}")
        return tickers_short, instr_df, pf_mask


    def __get_pf_tickers_short(self, typ=None, exchcode=None, subtyp='NO_PRF'): # generic tickers
        tickers_short, _, _ = self.__t212_get_pf_tickers_and_instr_df_and_mask(typ, exchcode, subtyp)
        return tickers_short

    
    def get_pf_tickers(self, typ=None, exchcode=None, subtyp='NO_PRF'): # generic tickers such as LON:CNA
        tickers_short, instr_df, pf_mask = self.__t212_get_pf_tickers_and_instr_df_and_mask(typ, exchcode, subtyp)

        # workingScheduleId -> exchange codename
        workingScheduleIds = instr_df[pf_mask]['workingScheduleId'].tolist()
        
        exchanges = list(map(lambda id: self.workingScheduleId_2_exchcode(id), workingScheduleIds))
        
        #tickers = list(map(lambda (x,y): str(x) + "" + y, zip(exchanges,tickers_short))) # Fail
        tickers = list(map(lambda x,y: str(x) + ":" + y, exchanges, tickers_short)) # Success

        return tickers


    ## call this function if get a 404 error:
    #def try_other_exchange(ticker):
    #    s = ticker
    #    if ticker[0:4] == 'FRA:':
    #        s='ETR:'+ticker[4:]
    #    elif ticker[0:4] == 'NSQ:':
    #        s='NMQ:'+ticker[4:]
    #    elif ticker[0:4] == 'OTC:':
    #        s='PNK:'+ticker[4:]
    #    return s

        
    
    # for the whole exchange (not just your portfolio)
    def __get_tickers_short(self, typ=None, exchcode=None): # generic tickers
        instr_df = self.instruments_df(typ, exchcode)
        return instr_df['shortName'].tolist()

    # for the whole exchange (not just your portfolio)
    # generic tickers such as LON:CNA
    # a AIM ticker will also return LON:
    def get_tickers(self, typ=None, exchcode=None, subtyp='NO_PRF'):
        instr_df = self.instruments_df(typ, exchcode)
        if subtyp == 'NO_PRF':
            # Remove preferrence shares
            #instr_df = instr_df[instr_df['name'].str.contains('% PRF|(Preference)', regex=False) == False]
            #instr_df = instr_df[instr_df['name'].str.contains('% PRF|\(Preference\)') == False]
            instr_df = instr_df[instr_df['name'].str.contains(' PRF|\(Preference\)') == False] # also exclude "Bristol & West PRF"

        tickers_short = instr_df['shortName'].tolist()


        # workingScheduleId -> exchange codename
        workingScheduleIds = instr_df['workingScheduleId'].tolist()
        
        exchanges = list(map(lambda id: self.workingScheduleId_2_exchcode(id), workingScheduleIds))
        
        tickers = list(map(lambda x,y: str(x) + ":" + y, exchanges, tickers_short)) # Success

        return tickers




    # returns the exchange codename (in stockopedia format) e.g.: 'LON', 'NYQ, etc...'
    # Note: it returns the stockopedia format,
    #       it does returns the same 'LON' prefix for these 3 Trading212 exchanges (LON, LON-NON-ISA and AIM)
    #       the inverse of exchcode_2_workingScheduleIds apart for (LON, LON-NON-ISA and AIM)
    #       workingScheduleId for LON, LON-NON-ISA and AIM return the same LON codename
    def workingScheduleId_2_exchcode(self, id):
        # workingScheduleId -> exchange
        exch_df = self.exchanges_df()
        #print(f"\nexch_df={exch_df}")
        #     id                           name                                   workingSchedules
        # 6   68  London Stock Exchange NON-ISA  [{'id': 114, 'timeEvents': [{'date': '2023-10-...
        # 11  64      London Stock Exchange AIM  [{'id': 101, 'timeEvents': [{'date': '2023-10-...
        # 13  42          London Stock Exchange  [{'id': 88, 'timeEvents': [{'date': '2023-10-0...
        
        # search id through all the workingSchedules of every exchange
        for index, row in exch_df.iterrows():
            for workingSchedule_d in row['workingSchedules']:
                # once found id, return exchange name
                if id == workingSchedule_d['id']:
                    exchanges_df_name = row['name']
                    return T212.exchanges_df_name_2_exchode_d[exchanges_df_name]
                    #else: handle error as becore with the swich statement?
                    #    print(f"ERROR: Cannot handled: {row['name']}")
                    #    return row['name']


    # 'LON_AIM' -> [100, 101]   
    #def exchcode_2_workingScheduleIds(self, exchcode):
    #    exchid = self.exchcode_2_exchid(exchcode)
    #    workingScheduleIds = self.exchid_2_workingScheduleIds(exchid)
    #    return workingScheduleIds
    def exchcode_2_workingScheduleIds(self, exchcode_l: list): # exchcode is now a list of exchanages
        workingScheduleIds_l = []
        for exchcode in exchcode_l:
            exchid = self.exchcode_2_exchid(exchcode)
            workingScheduleIds = self.exchid_2_workingScheduleIds(exchid)
            workingScheduleIds_l += workingScheduleIds
        return workingScheduleIds_l

    # 'LON' -> exchanges_df id
    def exchcode_2_exchid(self, exchcode):
        exch_df = self.exchanges_df()
        exchanges_df_name = T212.exchcode_2_exchanges_df_name_d[exchcode]
        # TODO:: catch error if loopup failed?
        for index, row in exch_df.iterrows():
            #if exchanges_df_name in row['name']:
            if exchanges_df_name == row['name']: # full match so that can pick the correct LSE
                return row['id']
        return None
 

    # list workingSchedules id's corresponding to exchanges id 
    def exchid_2_workingScheduleIds(self, exchid: int):
        df = self.exch_df
        workingSchedules_dics = df.loc[(df['id'] == exchid), 'workingSchedules'].values[0]
        # Note first df.loc() takes a first parameter which is the filter condition, and a second which is the column being output.
        # .values[0] added to get the actual value instead of 1x1 dataFrame

        #print(f"\nworkingSchedules_dics={workingSchedules_dics}")
        workingScheduleIds = [d['id'] for d in workingSchedules_dics]  # workingSchedules_dics is a list of dict
        #print(f"workingScheduleIds={workingScheduleIds}")
        return workingScheduleIds
        
        
        
        

### Key take aways:
# about dataFrames:
# typical mistake: df.loc(). should be df.loc[].
