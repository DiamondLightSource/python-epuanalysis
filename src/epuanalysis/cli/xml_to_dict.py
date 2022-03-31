import argparse
import json
import xmltodict

from rich.pretty import pprint


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="Path to XML file", dest="xml_file")
    args = parser.parse_args()
    with open(args.xml_file, "r") as xf:
        content = xf.read()
        xd = xmltodict.parse(content)
    pprint(json.loads(json.dumps(xd)))
