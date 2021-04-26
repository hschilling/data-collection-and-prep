from pathlib import Path
import argparse
import os
import sys

import requests
import pandas as pd

from dotenv import load_dotenv

def retrieve_airtable_data(table, api_key):
    '''
    Uses airtable API key to request table data from airtable.
    
    Parameters
    table : string name of the table
    '''
    # api_key = 'XXXXX'
    headers = {
        "Authorization": "Bearer %s" % api_key,
    }
    
    url = 'https://api.airtable.com/v0/appmifYhoEdnfPIbU/%s' % table
    params = ()
    airtable_records = []
    run = True
    while run:
        response = requests.get(url, params=params, headers=headers)
        airtable_response = response.json()
        airtable_records += (airtable_response['records'])
        if 'offset' in airtable_response:
            run = True
            params = (('offset', airtable_response['offset']),)
        else:
            run = False

    airtable_rows = []
    for record in airtable_records:
        airtable_rows.append(record['fields'])
    df = pd.DataFrame(airtable_rows)

    return df
#
if __name__ == "__main__":
    default_path_to_env = Path( Path.home(), '.petal_env')

    parser = argparse.ArgumentParser(prog = sys.argv[0],
                                     description = "get airtable with labeled papers.")
    parser.add_argument("--env_path", help = "path to .env file containing API keys",
                        default = default_path_to_env, type = str)

    parser.add_argument('table', type=str, help='name of Airtable to retrieve')

    args = parser.parse_args()

    load_dotenv(args.env_path)

    table = args.table

    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    # table = 'Colleen%20and%20Alex'
    df = retrieve_airtable_data(table, AIRTABLE_API_KEY)
    
    df.to_csv('../data/%s.csv' % table.replace('%20', '_'))