# greenplum-syscat-ref
Greenplum System Catalog Reference

## Introduction
This code can be used to generate HTML docs and diagrams of the Greenplum system catalog tables.
The content is generated based on the catalog JSON files found here:
- https://github.com/greenplum-db/gpdb/tree/master/gpMgmt/bin/gppylib/data

## Example Diagram
![Example Diagram](https://github.com/stephendotcarter/greenplum-syscat-ref/blob/master/example.png "Example Diagram")

## Instructions
1. git clone https://github.com/stephendotcarter/greenplum-syscat-ref.git
2. pip install -r requirements.txt
3. mkdir -p html/img
4. python generate_content.py
