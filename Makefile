# Simple Makefile to package python for AWS Lambda

build:
	pip install --target ./package -r requirements.txt
	zip -r9 function.zip package lambda_function.py