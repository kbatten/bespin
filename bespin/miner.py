# TODO: filter on fqn/Id glob

import xml.dom.minidom
import json
import sqlite3


class Miner(object):
    def __init__(self, database):
        """Initialize the Miner

        Keyword arguments:
        database -- path to sqlite database
        """
        self.conn = sqlite3.connect(database)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS swtor
(key TEXT PRIMARY KEY, id TEXT, kind TEXT, value TEXT, version INT, revision INT, source TEXT)''')


    def close(self):
        self.conn.commit()
        self.c.close()


    def loadxml(self, xmlfile, kinds=None, idfilter=None):
        """Load data from an xml file

        Keyword arguments:
        xmlfile -- either a string or a file object
        kinds -- a list that filters results on type (Ability, Tag, etc)
        idfilter -- a blob that filters results based on Id
        """
        if isinstance(xmlfile, str):
            xmlfile = file(xmlfile)

        try:
            data_xml = xml.dom.minidom.parse(xmlfile)
        except:
            return False

        root = data_xml.documentElement

        if kinds and not root.tagName in kinds:
            return False

        # store the results into the database
        data_json = self._parse_xml(root, idfilter)
        if 'GUID' in data_json['^']:
            guid = data_json['^']['GUID']
        else:
            return False
        if 'fqn' in data_json['^']:
            id = data_json['^']['fqn']
        elif 'Id' in data_json['^']['Id']:
            id = data_json['^']['Id']
        else:
            return False
        kind = root.tagName
        version = 0
        if 'Version' in data_json['^']:
            revision = int(data_json['^']['Version'])
        else:
            revision = 0
        row = (guid, id, kind, json.dumps(data_json), version, revision, xmlfile)
        try:
            self.c.execute('INSERT INTO swtor VALUES (?,?,?,?,?,?,?)', row)
        except sqlite3.IntegrityError:
            self.c.execute('UPDATE swtor SET id=?, kind=?, value=?, version=?, revision=?, source=? WHERE key=? AND revision<?',row[1:]+(row[0],row[5]))
        self.conn.commit()

        return True


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


    def _parse_xml(self, root, idfilter):
        # parse Ability xml data and return json
        # only concern is using the word 'type' here
        # as an index
        data_json = {
            'type':root.tagName
            }

        node_xml = root
        node_json = data_json
        self._recurse_copy_nodes(node_xml, node_json)

        return data_json
