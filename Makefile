# Simple Makefile to package python for AWS Lambda

build:
	pip install --target ./package -r requirements.txt
	cp lambda_function.py ./package
	cd package; zip -r9 function.zip .; cd ..
	mv package/function.zip .

cleanup:
	rm -rf package/ function.zip