# megaport-datadog

## Purpose

This script will pull metrics from [Megaport API](https://dev.megaport.com/) and push them to DataDog. It uses the the Megaport API to gather the last 30 minutes worth of mbps in/out samples. These samples are then pushed via the [DataDog API](https://docs.datadoghq.com/api/?lang=python#post-timeseries-points). Megaport provides their metrics at ~5 minute intervals. DataDog will not care about the duplicated samples and will do a no-op.

**NOTE** This is only for routers of type "MCR2". If you would like to view bandwidth data from another Megaport product you will need to change the "products" address URI. Please refer to: https://dev.megaport.com/#service-metrics--2

## Prerequisites

* Megaport user and password (I would recommend creating a new read-only user for this)
* An AWS account with access to Lambda
* DataDog API key
* Linux or OS X

## How to use locally

1. User pyenv or venv to create a virtual environment (optional, but recommended)
2. `make install`
3. Uncomment the last line in [lambda_function.py](lambda_function.py)
4. `python lambda_function.py`

## How to create a Lambda in AWS

1. `make build`
2. Create a new Lambda in AWS
3. Upload function.zip, which was created by `make build`
4. Create a trigger based on a CloudWatch event and choose "schedule" then input a desired cron. I do a trigger every 5 minutes. `cron(0/5 * * * ? *)`
5. Create three environment variables: `DD_API_KEY`, `MP_PASSWORD`, and `MP_USERNAME`. Input your sensitive values.
6. Test

## DataDog

If you do not specific a custom metric prefix, you should see your metric as `megaport.*` in DataDog. There you can make a dashboard and monitors to your liking.
