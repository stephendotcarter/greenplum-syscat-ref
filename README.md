# greenplum-syscat-ref
Greenplum System Catalog Reference

View the generated content:
- http://stephendotcarter.github.io/greenplum-syscat-ref

## Introduction
This code can be used to generate HTML docs and diagrams of the Greenplum system catalog tables.
The content is generated based on the catalog JSON files found here:
- https://github.com/greenplum-db/gpdb/tree/master/gpMgmt/bin/gppylib/data

## Example Diagram
![Example Diagram](https://github.com/stephendotcarter/greenplum-syscat-ref/blob/master/example.png "Example Diagram")

## Requirements
- graphviz (specificlly "dot" package)
  - http://www.graphviz.org/Download.php

## Instructions
1. git clone https://github.com/stephendotcarter/greenplum-syscat-ref.git
2. pip install -r requirements.txt
3. mkdir -p html/img
4. python generate_content.py data/5.0.json
5. cd html
6. python -m SimpleHTTPServer 8000
7. Connect to http://localhost:8000
