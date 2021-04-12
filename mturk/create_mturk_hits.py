#!/usr/bin/env python
# coding: utf-8

import boto3
import csv
import xmltodict
import json
import pprint
import argparse
import sys

parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 description="generate MTurk HITs from a CSV file.")
parser.add_argument("aws_profile", help="AWS Profile Name", type=str)
parser.add_argument("papers_csv", help="CSV file with title, abstract, and URL for papers", type=str)
parser.add_argument("hits_ids_file", help="file containing HIT IDs generated", type=str)
args = parser.parse_args()
aws_profile = args.aws_profile
papers_csv = args.papers_csv
hits_ids_file = args.hits_ids_file

# Create the MTurk client object used to interact with MTurk
create_hits_in_production = False # Change this to True if publishing to production, not sandbox
environments = {
  "production": {
    "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
    "preview": "https://www.mturk.com/mturk/preview"
  },
  "sandbox": {
    "endpoint": 
          "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
    "preview": "https://workersandbox.mturk.com/mturk/preview"
  },
}
mturk_environment = environments["production"] if create_hits_in_production else environments["sandbox"]
session = boto3.Session(profile_name=aws_profile)  # This profile was created using AWS command line tools. Creating the that involved using access keys
client = session.client(
    service_name='mturk',
    region_name='us-east-1',
    endpoint_url=mturk_environment['endpoint'],
)

# The file mturk_template.html has the template for the HITs
html_layout = open('./mturk_template.html', 'r').read()
QUESTION_XML = """<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
        <HTMLContent><![CDATA[{}]]></HTMLContent>
        <FrameHeight>650</FrameHeight>
        </HTMLQuestion>"""
question_xml = QUESTION_XML.format(html_layout)

# MaxAssignments set to 1 here because I wanted to test this and so this way I could be the
# #    one and only worker working on this and it would be done
TaskAttributes = {
    'MaxAssignments': 1,           
    # How long the task will be available on MTurk (1 hour)     
    'LifetimeInSeconds': 60*60,
    # How long Workers have to complete each item (10 minutes)
    'AssignmentDurationInSeconds': 60*10,
    # The reward you will offer Workers for each response
    'Reward': '0.00',                     
    'Title': 'Petal labeling',
    'Keywords': 'biomimicry',
    'Description': 'Label the paper.'
}

# Loop over the papers
# Read the CSV file from the ground truth AirTable. The path to this needs to be adjusted as needed
results = []
hit_type_id = ''

with open(hits_ids_file, 'w') as hitsfile:
    writer = csv.writer(hitsfile)
    with open('ground_truth.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # skip the header
        for i, row in enumerate(reader):
            title, abstract, url = row
            response = client.create_hit(
                **TaskAttributes,
                Question=question_xml.replace('${title}',title).replace('${abstract}',abstract).replace('${url}',url)
            )
            hit_type_id = response['HIT']['HITTypeId']
            hit_id = response['HIT']['HITId']
            results.append({
                'title': title,
                'abstract': abstract,
                'url': url,
                'hit_id': hit_id,
            })
            # hitsfile.write(f"{hit_id}\n")
            writer.writerow((hit_id,title,abstract,url))
            if i > 0: break   # Only want to do a couple HITs for now

# Print out the URL to where you can view the HITs
print("You can view the HITs here:")
print(mturk_environment['preview']+"?groupId={}".format(hit_type_id))




