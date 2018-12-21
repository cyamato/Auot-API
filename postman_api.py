#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Python 2.7
# Copyright (c) 2018 Craig Yamato
import yaml
import os
import sys
import datetime
import requests
import json
import unicodedata

# Load config file
with open('config.yml') as c:
    config = yaml.load(c)

# Postman API Call for Collections
postman_url = 'https://api.getpostman.com/collections'
postman_headers = {
    'X-Api-Key': config['postman']['api_key'] 
}
payload = {}

# Make Reqest
response = requests.request('GET', postman_url, headers = postman_headers, 
    data = payload, allow_redirects=False)
# Turn JSON Response to Phython Dict
try:
    postman_collections = response.json()
except ValueError:
    print ('Error: Postman API Call for Collections failed, JSON was not '
        'properly formated')
    sys.exit()

# Check for error in response form Postman
if 'error' in postman_collections:
    print(postman_collections['error']['message'])
    sys.exit()
    
# Save Postman Response to file
pm_out_file = open('postman/' + config['postman']['collections_output_file'],'w')
pm_out_file.write(json.dumps(postman_collections, sort_keys=True, indent=4, 
    separators=(',', ': ')).encode("utf-8"))
pm_out_file.close()
    
# Find the Target API Collection's UID
target_api_collection = ''
for collection in postman_collections['collections']:
    if collection['name'] == config['postman']['target_collection']:
        target_api_collection = collection['uid']
        
if target_api_collection is '':
    print('The Target API Collection was not found')
    sys.exit()
        
# Get the Target API Collection
postman_url = 'https://api.getpostman.com/collections/'+target_api_collection
postman_headers = {
    'X-Api-Key': config['postman']['api_key'] 
}
payload = {}

# Make Reqest
response = requests.request('GET', postman_url, headers = postman_headers, 
    data = payload, allow_redirects=False)
# Turn JSON Response to Phython Dict
try:
    postman_collection = response.json()
except ValueError:
    eString = 'Error: Postman API Call for the Target Collection failed, '
    eString = eString + 'JSON was not properly formated' 
    print (eString)
    sys.exit()

# Check for error in response form Postman
if 'error' in postman_collection:
    print(postman_collection['error']['message'])
    sys.exit()
    
# Save Postman Response to file
pm_out_file = open('postman/' + config['postman']['target_collection_output_file'],'w')
pm_out_file.write(json.dumps(postman_collection, sort_keys=True, indent=4, 
    separators=(',', ': ')).encode("utf-8"))
pm_out_file.close()

apis = postman_collection['collection']['item']

# Get the curent time
now = datetime.datetime.now()

# Write the first lines of Python code
api_file_header = '#!/usr/bin/python2\n'
api_file_header = api_file_header + '# -*- coding: utf-8 -*-\n'
api_file_header = api_file_header + '# Auto Generated API Libary from the ' 
api_file_header = api_file_header + config['postman']['target_collection'] 
api_file_header = api_file_header + ' Postman Collection\n'
api_file_header = api_file_header + '# Created On: ' + now.isoformat() 
api_file_header = api_file_header +'\nimport requests, json\n\n'

# Write The Main API Class
main_api = 'class API:\n'
main_api = main_api + '    ' + '"""' 
main_api = main_api + postman_collection['collection']['info']['description'] 
main_api = main_api + '\n\n'
main_api = main_api + '    ' + 'Args:\n'
for authHeader in config['api_libary']['auth_headers']:
    main_api = main_api + '    ' + '    ' + authHeader.replace('-', '_') 
    main_api = main_api + ' (str): ' 
    main_api = main_api + config['api_libary']['auth_headers'][authHeader] 
    main_api = main_api + '\n'
main_api = main_api + '\n' + '    ' + '"""\n'

request_api = """    # Write the request def
    # API Request
    def apiRequest(self, method, url, headers, payload):
        # Add Kentk Auth Headers
"""

# Auth Headers
headKeys = config['api_libary']['auth_headers'].keys()
for head in headKeys:
    request_api = request_api + '        ' + 'headers[\'' + head 
    request_api = request_api + '\'] = self.' + head.replace('-', '_') + '\n'

# Enforced Header
headKeys = config['api_libary']['enforced_header'].keys()
for head in headKeys:
    request_api = request_api + '        ' + 'headers[\'' + head + '\'] = \'' 
    request_api = request_api + config['api_libary']['enforced_header'][head] 
    request_api = request_api + '\'\n'
    
# Request
request_api = request_api + """        # Make Reqest
        response = requests.request(method, url, headers = headers, 
            data = payload, allow_redirects=False, verify=False)

        # Turn JSON Response to Phython Dict
        try:
            json_response = response.json()
        except ValueError:
            print(\'place holder\')
            return({\'name\': \'request error\', \'message\': response.text})

        # Check for error in response
        if \'error\' in json_response:
            print(json_response[\'error\'][\'message\'])
            return({'name': 'request error', 
                'message': json_response['error']['message']})
        elif response.status_code < 200 or response.status_code > 299:
            return({\'name\': \'request error\', \'message\': response.text})
        else:
            return(json_response)
            
"""

# Function to make the document protoypes
def py_prototypes(PT, spacing):
    """ This founction will make a documented prototype
    
    """
    propertyString = ''
    if not isinstance(PT, dict):
        return spacing + '{}'
    ptKeys = PT.keys()
    # Loop through each keys
    for key in ptKeys:
        # Process Lists
        if isinstance(PT[key], list):
            if not PT[key]:
                propertyString = propertyString + spacing + key + ' (list): \n'
            elif isinstance(PT[key][0], dict):
                propertyString = propertyString + spacing + key 
                propertyString = propertyString + ' (list of ' + key 
                propertyString = propertyString + '): A dict in the frame of:\n' 
                propertyString = propertyString + py_prototypes(PT[key][0], 
                    spacing + '    ')
            elif type(PT[key][0]).__name__ is 'NoneType':
                propertyString = propertyString + spacing + key + ' (list of ' 
                ropertyString = propertyString + 'str' + '): \n'
            elif isinstance(PT[key][0], unicode):
                propertyString = propertyString + spacing + key + ' (list of ' 
                ropertyString = propertyString + 'str' + '): \n'
            else:
                propertyString = propertyString + spacing + key + ' (list of ' 
                ropertyString = propertyString + type(PT[key][0]).__name__ 
                ropertyString = propertyString + '): \n'
        # Process Objects
        elif isinstance(PT[key], dict):
            propertyString = propertyString + spacing + key + ' (' + key 
            propertyString = propertyString + ': object): A dict in the '
            propertyString = propertyString + 'frame of:\n'
            pBuild = py_prototypes(PT[key], spacing + '    ')
            propertyString = propertyString + pBuild
        elif type(PT[key]).__name__ is 'NoneType':
            propertyString = propertyString + spacing + key + ' (str): \n'
        elif isinstance(PT[key], unicode):
            propertyString = propertyString + spacing + key + ' (str): \n'
        else:
            propertyString = propertyString + spacing + key + ' (' 
            propertyString = propertyString + type(PT[key]).__name__ + '): \n'
    return propertyString
    
# Function to build the document docstring arguments
def py_docstringBuild(doc_parameters, PT, spacing):
    # Args
    docstring = ''
    docstring = docstring + '\n' + spacing + '    ' + 'Args:\n'
    if len(doc_parameters) > 0:
        for parameter in doc_parameters:
            docstring = docstring + spacing + '    ' + '    ' + parameter + ' (str): \n'
    if PT['request']['body']:
        if PT['request']['body']['raw']:
            try:
                raw = json.loads(PT['request']['body']['raw'])
            except ValueError:
                raw = {}
            docstring = docstring + spacing + '    ' + '    ' + 'payload (payload: object): in the frame of:\n'
            docstring = docstring + py_prototypes(raw, spacing + '    ' + '    ' + '    ')
    docstring = docstring + '\n'
    # Returns
    docstring = docstring + spacing + '    ' + 'Returns:\n'
    docstring = docstring + spacing + '    ' + '    ' + 'Returns a Dict of a JSON Object:  Errors are returned in th form of {\'name\': \'request error\', \'message\': \'str\'}\n\n'
    if 'response' in PT:
        if len(PT['response']) > 0:
            if PT['response'][0]['body']:
                try:
                    body = json.loads(PT['response'][0]['body'])
                    docstring = docstring + py_prototypes(body, spacing + '    ' + '    ')
                except TypeError:
                    docstring = docstring
            else:
                docstring = docstring
        else:
            docstring = docstring
    else:
        docstring = docstring
    return docstring
    
# Build the api call classes and fucntions
def make_py_Class(requests, spacing):
    classes = ''
    subClasses = []
    for request in requests:
        if 'request' in request:
            method = 'method = \'' + request['request']['method'] + '\'\n'
            url = '\'' + request['request']['url']['protocol'] + '://'
            payload = False
            parameters = ['self']
            doc_parameters = []
            
            # Build URL
            usePeriod = False
            for domain in request['request']['url']['host']:
                if usePeriod:
                    url = url + '.'
                usePeriod = True
                url = url + domain
            for path in request['request']['url']['path']:
                url = url + '/'
                path = path.strip()
                if path.startswith('{{'):
                    url = url + '\' + '
                    path = path.strip('{')
                    path = path.strip('}')
                    parameters.append(path)
                    doc_parameters.append(path)
                    url = url + path
                    url = url + ' + \''
                else:
                    url = url + path
            url = url + '\'\n'
            
            # Build Payload
            if 'body' in request['request']:
                if 'raw' in request['request']['body']:
                    if request['request']['body']['raw'] != '':
                        parameters.append('payload')
                        payload = True
            
            # Build def Header
            classes = classes + spacing + 'def ' 
            classes = classes + request['name'].title().replace(' ', '') + '(' 
            classes = classes + ', '.join(parameters) + '):\n'
            
            # DocLine
            classes = classes + spacing + '    ' + '"""' 
            # DocLine Discritpion
            if 'description' in request:
                cName = request['description'].replace('\n', '\\n')
                cName = cName.replace('\r', '')
                classes = classes + cName + '\n'
            else:
                classes = classes + 'Autogenrated\n'
            classes = classes + py_docstringBuild(doc_parameters, request, 
                spacing + '    ')
            classes = classes + spacing + '    ' + '"""\n'
            
            # Insert Vers
            classes = classes + spacing + '    ' + 'method = ' + method
            classes = classes + spacing + '    ' + 'url = ' + url
            if payload:
                classes = classes + spacing + '    ' + 'if isinstance(payload, '
                classes = classes + 'dict):\n'
                classes = classes + spacing + '    ' + '    ' + 'try:\n'
                classes = classes + spacing + '    ' + '    ' + '    ' 
                classes = classes + 'payload = json.dumps(payload)\n'
                classes = classes + spacing + '    ' + '    ' 
                classes = classes + 'except ValueError:\n'
                classes = classes + spacing + '    ' + '    ' + '    ' 
                classes = classes + 'return {\'name\': \'request error\', '
                classes = classes + '\'message\': \'ValueError in submited '
                classes = classes + 'dict\'}\n'
            else:
                classes = classes + spacing + '    ' + 'payload = \'\'\n'
            
            # Make call
            classes = classes + spacing + '    ' + 'return '
            classes = classes + 'self.apiRequest(method, url, {}, payload)\n'
            classes = classes + '\n'
        elif 'item' in request:
            class_name = request['name'].replace(' ', '')
            subClasses.append(class_name)
            next_item = request['item']
            newClass = spacing + 'class ' + class_name.upper() + ':\n'
            
            if 'description' in request:
                newClass = newClass + spacing + '    """'
                classD = request['description'].replace('\n', '\\n')
                classD = classD.replace('\r', '')
                newClass = newClass + classD + '\n\n'
                newClass = newClass + spacing + '    ' + 'Args:\n'
                newClass = newClass + spacing + '    ' + '    ' + 'parent' 
                newClass = newClass + '(parent: class): the parent class '
                newClass = newClass + 'calling this class\n'
                newClass = newClass + spacing + '    ' + '\n'
                newClass = newClass + spacing + '    ' + '"""\n'
            
            # Build the class code
            classCode = make_py_Class(next_item, spacing + '    ')
            classes = classes + newClass + classCode['classes']
            
            # Add Init
            classes = classes + spacing + '    ' 
            classes = classes + 'def __init__(self, parent):\n'
            classes = classes + spacing + '    ' + '    ' 
            classes = classes + 'self.parent = parent\n'
            classes = classes + spacing + '    ' + '    ' 
            classes = classes + 'self.apiRequest = parent.apiRequest\n'
            
            for authHeader in config['api_libary']['auth_headers']:
                authHeader = authHeader.replace('-', '_')
                classes = classes + spacing + '    ' + '    ' + 'self.' 
                classes = classes + authHeader + ' = parent.' + authHeader 
                classes = classes + '\n'
            
            # Load subclasses
            for subClass in classCode['subClasses']:
                classes = classes + spacing + '        ' + 'self.' + subClass 
                classes = classes + ' = self.' + subClass.upper() + '(self)\n'
            classes = classes + '\n'
    return ({'classes': classes, 'subClasses': subClasses})

codeForClasses = make_py_Class(apis, '    ')

class_string = api_file_header + main_api + request_api 
class_string = class_string + codeForClasses['classes']

class_string = class_string + '    ' + '#INIT Process\n'

authHeaders = []
authHeadersStr = ''
for authHeader in config['api_libary']['auth_headers']:
    authHeader = authHeader.replace('-', '_')
    authHeaders.append(authHeader)
    authHeadersStr = authHeadersStr + '    ' + '    ' + 'self.' + authHeader 
    authHeadersStr = authHeadersStr + ' = ' + authHeader + '\n'
    
class_string = class_string + '    ' + 'def __init__(self, ' 
class_string = class_string + ', '.join(authHeaders) + '):\n'
class_string = class_string + authHeadersStr

for subClass in codeForClasses['subClasses']:
    class_string = class_string + '        self.' + subClass + ' = self.' + subClass.upper() + '(self)\n'

py_out_file = open('python/' + config['api_libary']['file_name'] + '.py','w')
py_out_file.write(class_string.encode("utf-8"))
py_out_file.close()

# Write Javascript Libary
js_module = '// ' + config['api_libary']['file_name'] + '.JS\n'
js_module = js_module + '/** Copyright (c) 2018 Craig Yamato */\n'
js_module = js_module + '\n'
js_module = js_module + '/**\n'
js_module = js_module + ' * @fileoverview\n' 
jsName = postman_collection['collection']['info']['description']
jsName = jsName.replace('\n', '\n * ')
js_module = js_module + ' * ' + jsName + '\n'
js_module = js_module + ' * @version ' + config['api_libary']['version'] + '\n'
js_module = js_module + ' * @exports\n' 
js_module = js_module + ' */\n'
js_module = js_module + '\'use strict\';\n'
js_module = js_module + 'const https = require(\'https\');\n'
js_module = js_module + 'const http = require(\'http\');\n'
js_module = js_module + '\n'

# Build JS functions
def make_js_functions(request, spacing, name):
    method = request['method']
    payload = False
    parameters = []
    function = ''
    
    # Build URL
    protocol = request['url']['protocol']
    url = '.'.join(request['url']['host'])
    path2 = ''
    pathElements = len(request['url']['path'])
    for path in request['url']['path']:
        pathElements = pathElements - 1
        path = path.strip()
        path2 = path2 + '/'
        if path.startswith('{{'):
            path = path.strip('{')
            path = path.strip('}')
            parameters.append(path)
            path2 = path2 + '\' + ' + path
            if pathElements > 0:
                path2 = path2 + ' + \''
        else:
            path2 = path2 + path
            if pathElements is 0:
                path2 = path2 + '\''
                
    # Build Payload
    if 'body' in request:
        if 'raw' in request['body']:
            if request['body']['raw'] != '':
                parameters.append('payload')
                payload = True
    
    # Build function Header
    function = function + spacing + name + ' (' + ', '.join(parameters) 
    function = function + ') {\n'
    function = function + spacing + '    ' + 'const p = this.parent;\n'
    function = function + spacing + '    ' + 'return new '
    function = function + 'Promise((resolve, reject) => {\n'
    
    # Insert Vers
    function = function + spacing + '    ' + '    ' + 'const method = \'' 
    function = function + method + '\';\n'
    function = function + spacing + '    ' + '    ' + 'const protocol = \'' 
    function = function + protocol + '\';\n'
    
    function = function + spacing + '    ' + '    ' + 'const url = \'' + url 
    function = function + '\';\n'
    function = function + spacing + '    ' + '    ' + 'const path = \'' + path2 
    function = function + ';\n'
    if payload:
        function = function + spacing + '    ' + '    ' + 'if (typeof(payload) '
        function = function + 'is \'object\') {\n'
        function = function + spacing + '    ' + '    ' + '    ' + 'payload = '
        function = function + 'JSON.stringify(payload);\n'
        function = function + spacing + '    ' + '    ' + '}\n'
    else:
        function = function + spacing + '    ' + '    ' + 'let '
        function = function + 'payload = \'\';\n'
    
    # Make call
    function = function + spacing + '    ' + '    ' + 'p.apiRequest(method, '
    function = function + 'protocol, url, path, payload)\n'
    function = function + spacing + '    ' + '    ' + '    ' + '.then((result) '
    function = function + '=> {\n'
    function = function + spacing + '    ' + '    ' + '    ' + '    ' 
    function = function + 'resolve(result);\n'
    function = function + spacing + '    ' + '    ' + '    ' + '})\n'
    function = function + spacing + '    ' + '    ' + '    ' 
    function = function + '.catch((reson) => {\n'
    function = function + spacing + '    ' + '    ' + '    ' + '    ' 
    function = function + 'reject(reson);\n'
    function = function + spacing + '    ' + '    ' + '    ' + '});\n'
    function = function + spacing + '    ' + '});\n'
    function = function + spacing + '}\n'
    
    return function

# Build the api call classes and fucntions
def make_js_classes(items, spacing, parentClass):
    functions = []
    jsSubClass = []
    jsClass = ''
    class_name = 'API'
    subClassNames = []
    first = True
    if 'name' in items:
        class_name = items['name'].replace(' ', '').upper()
        first = False
    next_items = items['item']
    # Loop through each item to see if its a folder
    for next_item in next_items:
        if 'request' in next_item:
            functions.append(make_js_functions(next_item['request'], '    ', next_item['name'].title().replace(' ', '')))
        elif 'item' in next_item:
            if 'name' in next_item:
                subClassNames.append(next_item['name'].replace(' ', '').upper())
            jsSubClass.append(make_js_classes(next_item, '', class_name)['code'])
    # Write the classes
    if not first:
        jsClass = spacing + 'class ' + class_name + ' {\n'
        classConstructure = spacing + '    ' + 'constructor (parent) {\n'
        classConstructure = classConstructure + spacing + '    ' + '    ' 
        classConstructure = classConstructure + 'this.parent = parent;\n'
        for subClassName in subClassNames:
            classConstructure = classConstructure + spacing + '    ' + '    ' 
            classConstructure = classConstructure + 'this.' + subClassName 
            classConstructure = classConstructure + ' = new ' + subClassName 
            classConstructure = classConstructure + '(this.parent);\n'
        classConstructure = classConstructure + '    ' + spacing + '}\n'
        jsClass = jsClass + classConstructure
        
    if len(functions) > 0:
        jsClass = jsClass + ''.join(functions)
        functions = []
    if not first:
        jsClass = jsClass + '}\n\n'
        
    jsClass = jsClass + ''.join(jsSubClass)
    return ({'code': jsClass, 'subClasses': subClassNames})

jsClassCode = make_js_classes(postman_collection['collection'], '', '')
js_module = js_module + jsClassCode['code']

# Main JS Class
js_module = js_module + 'class API {\n'
# Build JS Constructure Element
js_constructure_args = []
js_constructure_args_string = ''

for authHeader in config['api_libary']['auth_headers']:
    authHeader2 = authHeader.replace('-', '_')
    js_constructure_args.append(authHeader2)
    js_constructure_args_string = js_constructure_args_string + '    ' + '    ' 
    js_constructure_args_string = js_constructure_args_string + '    ' + '\'' 
    js_constructure_args_string = js_constructure_args_string +  authHeader 
    js_constructure_args_string = js_constructure_args_string + '\': ' 
    js_constructure_args_string = js_constructure_args_string + authHeader2 
    js_constructure_args_string = js_constructure_args_string + ',\n'
    
for authHeader in config['api_libary']['enforced_header']:
    js_constructure_args_string = js_constructure_args_string + '    ' + '    ' 
    js_constructure_args_string = js_constructure_args_string + '    ' + '\'' 
    js_constructure_args_string = js_constructure_args_string + authHeader 
    js_constructure_args_string = js_constructure_args_string + '\': \''
    jscHead = config['api_libary']['enforced_header'][authHeader]
    js_constructure_args_string = js_constructure_args_string + jscHead 
    js_constructure_args_string = js_constructure_args_string + '\',\n'

js_module = js_module + '    ' + 'constructor (' 
js_module = js_module + ', '.join(js_constructure_args) + ') {\n'
js_module = js_module + '    ' + '    ' + 'this.headers = {\n'
js_module = js_module + js_constructure_args_string
js_module = js_module +  '    ' + '    ' + '},\n'
for subClassName in jsClassCode['subClasses']:
    js_module = js_module + '    ' + '    ' + 'this.' + subClassName 
    js_module = js_module + ' = new ' + subClassName + '(this);\n'
js_module = js_module + '    ' + '}\n'
js_module = js_module + '\n'

# Write API Request
js_module2 = ''
js_module2 = js_module2 + '    ' 
js_module2 = js_module2 + 'apiRequest (method, protocol, url, path, payload) {\n'
js_module2 = js_module2 + '    ' + '    ' + 'const headers = this.headers;\n'
js_module2 = js_module2 + '    ' + '    ' 
js_module2 = js_module2 + 'return new Promise((resolve, reject) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'let options = {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'hostname: url,\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'path: path,\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'method: method,\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'headers: headers,\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '};\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'let web = http;\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'if (protocol is \'https\') {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'web = https;\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'let responseJSON = \'\';\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'const req = web.request(options, (res) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'if (res.statusCode < 200 || res.statusCode > 299) {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'resolve({\'name\': \'request error\', \'message\': '
js_module2 = js_module2 + 'responseJSON});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' + 'return;\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'res.on(\'data\', (chunk) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'responseJSON = responseJSON + chunk;\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'res.on(\'end\', (chunk) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' + 'try {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'resolve(JSON.parse(responseJSON));\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + '} catch (err) {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'reject({\'name\': \'request error\', \'message\': '
js_module2 = js_module2 + 'err.message});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'req.on(\'error\', (e) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'resolve({\'name\': \'request error\', \'message\': '
js_module2 = js_module2 + 'e.message});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'if (payload) {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'if (typeof(payload) is \'object\') {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'req.write(JSON.stringify(payload));\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '} else {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '    ' 
js_module2 = js_module2 + 'req.write(payload);\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'req.end();\n'
js_module2 = js_module2 + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '    ' + '}\n'
js_module2 = js_module2 + '}\n'
js_module2 = js_module2 + '\n'

js_module3 = js_module + js_module2 + 'module.exports = API;'

js_out_file = open('node/' + config['api_libary']['file_name'] + '.js','w')
js_out_file.write(js_module3.encode("utf-8"))
js_out_file.close()

# Mods for Browser Javascript file
js_module2 = ''
js_module2 = js_module2 + 'apiRequest (method, protocol, url, path, payload) '
js_module2 = js_module2 + '{\n'
js_module2 = js_module2 + '    '  + 'let fetchPrams = {\n'
js_module2 = js_module2 + '    ' + '    ' + 'headers: this.headers,\n'
js_module2 = js_module2 + '    ' + '    ' + 'method: method\n'
js_module2 = js_module2 + '    ' + '}\n'
js_module2 = js_module2 + '    ' + 'if (payload) {\n'
js_module2 = js_module2 + '    ' + '    ' + 'prams.body = payload\n'
js_module2 = js_module2 + '    ' + '}\n'
js_module2 = js_module2 + '    ' + 'url = protocol + "://" + url;\n'
js_module2 = js_module2 + '\n'
js_module2 = js_module2 + '    ' + 'fetch(url, fetchPrams)\n'
js_module2 = js_module2 + '    ' + '    ' + '.then((res) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'response = {}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'if (res.status < 200 or '
js_module2 = js_module2 + 'res.status > 299) {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'response = '
js_module2 = js_module2 + '{\'name\': \'request error\', \'message\': '
js_module2 = js_module2 + 'res.body};\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'try {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'response = '
js_module2 = js_module2 + 'res.json();\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '} catch (err) {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '    ' + 'response = '
js_module2 = js_module2 + '{\'name\': \'request error\', \'message\': '
js_module2 = js_module2 + 'err.message};\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + '}\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'return response;\n'
js_module2 = js_module2 + '    ' + '    ' + '})\n'
js_module2 = js_module2 + '    ' + '    ' + '.catch((err) => {\n'
js_module2 = js_module2 + '    ' + '    ' + '    ' + 'return {\'name\': '
js_module2 = js_module2 + '\'request error\', \'message\': err.message};\n'
js_module2 = js_module2 + '    ' + '    ' + '});\n'
js_module2 = js_module2 + '}\n'

js_module3 = js_module + js_module2

js_out_file = open('js/' + config['api_libary']['file_name'] + '.js','w')
js_out_file.write(js_module3.encode("utf-8"))
js_out_file.close()

print()