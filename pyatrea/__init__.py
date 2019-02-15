#
# Author: Juraj Nyiri
# Tested with:
# Atrea ECV 280 
#
# sw RD5 ver.:
# 2.01.26
# 2.01.3O
# 2.01.32
#

import requests
from xml.etree import ElementTree as ET
import demjson
import urllib 
import hashlib
import string
import random

class Atrea:
    def __init__(self, ip, password, code=""):
        self.ip = ip
        self.password = password
        self.code = code
        self.translations = {}
        self.commands = {}

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
    
    def setPower(self, power):
        try:
            power += 1
        except TypeError:
            return False
        power -= 1

        if(power < 99):
            power = "0"+str(power)
        elif(power < 10) and (power >= 0):
            power = "00"+str(power)
        elif(power == 100):
            power = str(power)
        else:
            return False

        self.commands['H10708'] = "00"+power
        return True

    def exec(self):
        url = 'http://'+self.ip+'/config/xml.cgi?auth='+self.code
        
        if(len(self.commands) > 0):
            for register in self.commands:
                url = url + "&" + register + self.commands[register]
            response = requests.get(url)
            return response.status_code == 200
        return False
    
    def setTemperature(self, temperature):
        try:
            temperature += 1
        except TypeError:
            return False
        temperature -= 1
        if(temperature >= 10 and temperature <= 40):
            temperature = str(int(temperature*10))
            if(len(temperature) == 3):
                self.commands['H10710'] = "00" + temperature
                return True
        return False
        
    
    #0 = manual
    #1 = weekly
    #2 = temporary
    def setProgram(self, program):
        try:
            program += 1
        except TypeError:
            return False
        program -= 1

        if(program == 0):
            self.commands['H10700'] = "00000"
            self.commands['H10701'] = "00000"
            self.commands['H10702'] = "00000"
            self.commands['H10703'] = "00000"
            return True
        elif(program == 1):
            self.commands['H10700'] = "00001"
            self.commands['H10701'] = "00001"
            self.commands['H10702'] = "00001"
            self.commands['H10703'] = "00001"
            return True
        elif(program == 2):
            self.commands['H10700'] = "00002"
            self.commands['H10701'] = "00002"
            self.commands['H10702'] = "00002"
            if 'H10703' in self.commands: self.commands.pop('H10703')
            return True

        return False
    
    #0 = off
    #1 = automat
    #2 = ventilation
    #3 = Night precooling
    #4 = Disbalance
    def setMode(self, mode):
        try:
            mode += 1
        except TypeError:
            return False
        mode -= 1
        if(mode == 0):
            self.commands['H10709'] = "00000"
            return True
        elif(mode == 1):
            self.commands['H10709'] = "00001"
            return True
        elif(mode == 2):
            self.commands['H10709'] = "00002"
            return True
        elif(mode == 3):
            self.commands['H10709'] = "00005"
            return True
        elif(mode == 4):
            self.commands['H10709'] = "00006"
            return True

        return False