all: camunda.py

%.py: %.json
	datamodel-codegen --input $< --output $@ --validation ||\
	datamodel-codegen --input $< --output $@
	black -t py37 $@
