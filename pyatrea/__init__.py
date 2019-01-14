import requests
from xml.etree import ElementTree as ET
import demjson
import urllib 
import hashlib
import string
import random

class Atrea:
    def __init__(self, ip, password):
        self.ip = ip
        self.password = password
        self.code = ""
        self.translations = {}

    def getTranslations(self):
        if not self.translations:
            self.translations['params'] = {}
            self.translations['words'] = {}
            response = requests.get('http://'+self.ip+'/lang/texts_2.xml?'+random.choice(string.ascii_letters)+random.choice(string.ascii_letters))
            if(response.status_code == 200):
                xmldoc = ET.fromstring(response.content)
                for text in xmldoc.findall('texts'):
                    for param in text.findall('params'):
                        data = demjson.decode(param.text)
                        for dataKey, dataValue in data.items():
                            self.translations['params'][dataKey] = dataValue
                    for word in text.findall('words'):
                        data = demjson.decode(word.text)
                        for dataKey, dataValue in data.items():
                            self.translations['words'][dataKey] = dataValue
        return self.translations

    def getParams(self):
        params = {}
        params['warning'] = []
        params['alert'] = []
        response = requests.get('http://'+self.ip+'/user/params.xml?'+random.choice(string.ascii_letters)+random.choice(string.ascii_letters))
        if(response.status_code == 200):
            xmldoc = ET.fromstring(response.content)
            for param in xmldoc.findall('params'):
                for child in list(param):
                    if(child.tag == "i"):
                        if 'flag' in child.attrib and 'id' in child.attrib :
                            if(child.attrib['flag'] == "W"):
                                params['warning'].append(child.attrib['id'])
                            elif(child.attrib['flag'] == "A"):
                                params['alert'].append(child.attrib['id'])
        return params

    def getStatus(self):
        status = {}
        response = requests.get('http://'+self.ip+'/config/xml.xml?auth='+self.code+'&'+random.choice(string.ascii_letters)+random.choice(string.ascii_letters))

        if(response.status_code == 200):
            if "HTTP: 403 Forbidden" in response.text:
                self.auth()
                response = requests.get('http://'+self.ip+'/config/xml.xml?auth='+self.code+'&'+random.choice(string.ascii_letters)+random.choice(string.ascii_letters))
                if response.status_code == 200 and "HTTP: 403 Forbidden" in response.text:
                    return False
            if(response.status_code == 200):
                xmldoc = ET.fromstring(response.content)
                for parentData in xmldoc.findall('RD5'):
                    for data in list(parentData):
                        for child in list(data):
                            if(child.tag == "O"):
                                status[child.attrib['I']] = child.attrib['V']
        return status

    def getTranslation(self, id):
        translations = self.getTranslations()
        
        if(id in translations['params']):
            param = 'params'
        elif(id in translations['words']):
            param = 'words'
        else:
            return id

        if('d' in translations[param][id]):
            toBeTranslated = translations[param][id]['d']
            if(toBeTranslated == "not%20to%20be%20translated"):
                toBeTranslated = translations[param][id]['t']
        else:
            toBeTranslated = translations[param][id]['t']

        if(hasattr(urllib, 'parse')):
            return urllib.parse.unquote(toBeTranslated)
        else:
            return urllib.unquote(toBeTranslated) #pylint: disable=E1101
    
    def auth(self):
        magic = hashlib.md5(("\r\n"+self.password).encode('utf-8')).hexdigest()
        response = requests.get('http://'+self.ip+'/config/login.cgi?magic='+magic+'&'+random.choice(string.ascii_letters)+random.choice(string.ascii_letters))
        if(response.status_code == 200):
            xmldoc = ET.fromstring(response.content)
            if(response.content == "denied"):
                return False
            else:
                self.code = xmldoc.text
        return False