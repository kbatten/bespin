# TODO: filter on Id glob

import xml.dom.minidom
import json

class Miner(object):
    def __init__(self, database):
        """Initialize the Miner

        Keyword arguments:
        database -- either a string or a file object
        """
        if isinstance(database, str):
            self.database = file(database,"w")
        else:
            self.database = database

    def loadxml(self, xmlfile, kind=None, idfilter=None):
        """Load data from an xml file

        Keyword arguments:
        xmlfile -- either a string or a file object
        """
        if isinstance(xmlfile, str):
            xmlfile = file(xmlfile)

        try:
            data_xml = xml.dom.minidom.parse(xmlfile)
        except:
            return None

        root = data_xml.documentElement

        if kind and root.tagName != kind:
            return None
        
        if root.tagName == "Ability":
            return self._parse_xml_ability(root, idfilter)
        return None

    def _get_attributes(self, node):
        # generate key value pairs of attributes
        # for a node
        for i in range(node.attributes.length):
            item = node.attributes.item(i)
            yield item.name, item.value

    def _recurse_copy_nodes(self, node_xml, node_json):
        # recursively copy xml to json

        # first copy the attributes for the current node
        for attribute, value in self._get_attributes(node_xml):
            if not '^' in node_json:
                node_json['^'] = {}
            node_json['^'][attribute] = value

        # if node is actually a list of like named child
        # nodes then handle it differently
        # TODO: detect when multiple children have the same name
        if node_xml.tagName.endswith("List"):
            is_list = True
        else:
            is_list = False
        # now loop through all the children and add them
        for child in node_xml.childNodes:
            # get the value for the current node
            if isinstance(child, xml.dom.minidom.Text):
                if child.nodeValue.strip("\n "):
                    node_json['%'] = child.nodeValue

            # recurse into the children
            if isinstance(child, xml.dom.minidom.Element):
                if is_list:
                    if not child.tagName in node_json:
                        node_json[child.tagName] = []
                    node_json_item = {}
                    self._recurse_copy_nodes(child, node_json_item)
                    node_json[child.tagName].append(node_json_item)
                else:
                    node_json[child.tagName] = {}
                    self._recurse_copy_nodes(child, node_json[child.tagName])


    def _parse_xml_ability(self, root, idfilter):
        # parse Ability xml data and return json
        # only concern is using the word 'type' here
        # as an index
        data_json = {
            'type':"Ability"
            }

        node_xml = root
        node_json = data_json
        self._recurse_copy_nodes(node_xml, node_json)

        return data_json
