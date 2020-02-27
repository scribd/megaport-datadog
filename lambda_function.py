#!/usr/bin/env python
## Written for python 3.7
## CURRENTLY ONLY SUPPORTS MCR2
## For use with AWS Lambda

# Scribd, Inc.
# This code is licensed under MIT license (see LICENSE.txt for details)

from datadog import initialize, api
from statistics import mean
from pprint import pprint
import requests
import argparse
import logging
import time
import os

def lambda_handler(event, context):
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Megaport client class
    class MegaportAPI:
        def __init__(self):
            return None

        def get(self, url, payload={}, headers={}):
            response = requests.request("get", url, headers=headers, data=payload)
            return response

        def post(self, url, payload={}, headers={}):
            response = requests.request("POST", url, headers=headers, data=payload)
            return response

    # You will typically want to set these as Environment vars
    # You can use AWS Secrets Manager for these
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", required=False, default=os.getenv("MP_USERNAME"), help="Megaport username")
    parser.add_argument("-p", "--password", required=False, default=os.getenv("MP_PASSWORD"), help="Megaport password")
    parser.add_argument("-k", "--key", required=False, default=os.getenv("DD_API_KEY"), help="DataDog API key")
    parser.add_argument("-m", "--metric", required=False, default="megaport", help="DataDog Metric prefix e.g. megaport")
    args = parser.parse_args()

    mp_client = MegaportAPI()
    mp_url = "https://api.megaport.com/v2"

    # DataDog config and initialization
    options = {
        "api_key": args.key
    }

    initialize(**options)

    # Gets the token used on all API calls
    logging.info("Authenticating to megaport API")
    token_url = "{mp_url}/login?username={username}&password={password}".format(mp_url=mp_url, username=args.username, password=args.password)

    # Error handling for login
    try:
        r = mp_client.post(token_url)
        login_token = r.json()['data']['token']
    except:
        print(r.text)
        exit(1)

    # Gather your Megaport product UIDs and names
    logging.info("Getting a list of your megaport products")
    products_url = "{mp_url}/products?token={token}".format(mp_url=mp_url, token=login_token)
    products = mp_client.get(products_url).json()['data']

    # Main dict that will hold all the metrics/data
    product_metrics = {}

    # Setting up the skeleton of products in the user's account
    for p in products:
        product_metrics.update({p["productUid"]: {"product_name":p["productName"]}})

    # Get current time in epoch milliseconds
    epoch_current = int(time.time() * 1000)
    # Gather sample data for the past 30 minutes
    epoch_to = epoch_current - 1800000

    # Get bandwidth metrics for products
    for u in product_metrics:
        # default tags we want to set
        product_name = "product_name:{}".format(product_metrics[u]["product_name"])
        product_uid = "product_uid:{}".format(u)
        custom_tags = ["source:megaport_datadog.py", product_name, product_uid]
        
        logging.info("Getting metrics for {}".format(product_name))
        logging.info("time_from={} time_to={}".format(epoch_to, epoch_current))
        bandwidth_url = "{mp_url}/product/mcr2/{product_uid}/telemetry?token={token}&type=bits&to={to_time}&from={from_time}&token={token}".format(mp_url=mp_url, product_uid=u, to_time=epoch_current, from_time=epoch_to, token=login_token)
        raw_data = mp_client.get(bandwidth_url).json()["data"]

        product_metrics[u].update({"raw_data": raw_data,
                                "mbps_in_samples": [],
                                "mbps_out_samples": []})

        # Get bits in/out with their timestamp
        for r in raw_data:
            if r["subtype"] == "In":
                for s in r["samples"]:
                    # appending metrics so I can send multiple datapoints
                    # https://docs.datadoghq.com/api/?lang=python#metrics
                    product_metrics[u]["mbps_in_samples"].append((int(s[0]/1000), s[1]))
            elif r["subtype"] == "Out":
                for s in r["samples"]:
                        product_metrics[u]["mbps_out_samples"].append((int(s[0]/1000), s[1]))
            else:
                continue
        
        # Start sending our metrics to DataDog
        logging.info("Sending out collected metrics...")
        logging.info("Sending mbps_in: {}".format(product_metrics[u]["mbps_in_samples"]))
        # TODO: Error handling
        api.Metric.send(
            metric="{}.bandwidth.mbps_in".format(args.metric),
            points=product_metrics[u]["mbps_in_samples"],
            tags=custom_tags   
        )

        logging.info("Sending mbps_out: {}".format(product_metrics[u]["mbps_out_samples"]))
        # TODO: Error handling
        api.Metric.send(
            metric="{}.bandwidth.mbps_out".format(args.metric),
            points=product_metrics[u]["mbps_out_samples"],
            tags=custom_tags   
        )

    return logging.info("Done. Exiting...")

# If you want to test this locally uncomment the line below
# lambda_handler(None, None)