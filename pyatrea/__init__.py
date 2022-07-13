#
# Author: Juraj Nyiri
# Tested with:
# Atrea ECV 280
# sw RD5 ver.:
# 2.01.26
# 2.01.3O
# 2.01.32
#
# Atrea Duplex 390
# Driver: 71.16
# RD4: 72.06
# Digi: 73.17
# Web: 74.11

import requests
from xml.etree import ElementTree as ET
import demjson3
import urllib
import hashlib
import string
import random
from enum import IntEnum


class AtreaProgram(IntEnum):
    MANUAL = 0
    WEEKLY = 1
    TEMPORARY = 2


class AtreaMode(IntEnum):
    OFF = 0
    AUTOMATIC = 1
    VENTILATION = 2
    CIRCULATION_AND_VENTILATION = 3
    CIRCULATION = 4
    NIGHT_PRECOOLING = 5
    DISBALANCE = 6
    OVERPRESSURE = 7
    PERIODIC_VENTILATION = 8
    STARTUP = 9
    RUNDOWN = 10
    DEFROSTING = 11
    EXTERNAL = 12
    HP_DEFROSTING = 13
    IN1 = 14
    IN2 = 15
    D1 = 16
    D2 = 17
    D3 = 18
    D4 = 19


class Atrea:
    def __init__(self, ip, port=80, password="", code=""):
        self.ip = ip
        self.port = port
        self.password = password
        self.code = str(code)
        self.translations = {}
        self.translations["params"] = {}
        self.translations["words"] = {}
        self.status = {}
        self.params = {}
        self.commands = {}
        self.writable_modes = {}
        self.modesToIds = {}
        self.idsToModes = {}
        self.configDir = {}
        self.gettingTranslations = False

    def getBaseURL(self):
        return "http://" + self.ip + ":" + str(self.port) + "/"

    def getAuthURL(self):
        return "auth=" + self.code

    def getURL(self, param):
        url = self.getBaseURL()
        if "?" in param:
            url += param + "&"
        else:
            url += param + "?"
        url += (
            self.getAuthURL()
            + "&"
            + random.choice(string.ascii_letters)
            + random.choice(string.ascii_letters)
        )
        return url

    def decompress(self, s):
        dict = {}
        data = list(s)
        currChar = data[0]
        oldPhrase = currChar
        out = [currChar]
        code = 512
        for char in data[1:]:
            currCode = ord(char)
            if currCode < 512:
                phrase = char
            elif currCode in dict:
                phrase = dict[currCode]
            else:
                phrase = oldPhrase + currChar
            out.append(phrase)
            currChar = phrase[0]
            dict[code] = oldPhrase + currChar
            code = code + 1
            oldPhrase = phrase
        return "".join(out)

    def parseTranslations(self, textNode):
        for param in textNode.findall("params"):
            data = demjson3.decode(param.text)
            for dataKey, dataValue in data.items():
                self.translations["params"][dataKey] = dataValue
        for word in textNode.findall("words"):
            data = demjson3.decode(word.text)
            for dataKey, dataValue in data.items():
                self.translations["words"][dataKey] = dataValue
        return self.translations

    def getTranslations(self):
        if (
            not self.translations
            or self.translations["params"] == {}
            or self.translations["words"] == {}
        ) and not self.gettingTranslations:
            self.gettingTranslations = True
            response = requests.get(self.getURL("lang/texts_2.xml"))
            if response.status_code == 200:
                xmldoc = ET.fromstring(response.content)
                if xmldoc.tag == "compress":
                    text = ET.fromstring(self.decompress(xmldoc.text))
                    self.parseTranslations(text)
                else:
                    for text in xmldoc.findall("texts"):
                        self.parseTranslations(text)
            self.gettingTranslations = False
        return self.translations

    def getConfigDir(self):
        if not self.configDir:
            response = requests.get(self.getURL("cfgdir.xml"))
            if response.status_code == 200 and "HTTP: 404 Page" not in response.text:
                self.configDir = ET.fromstring(response.content)
                return self.configDir
            return False
        return self.configDir

    def findChild(self, element, id):
        for child in element:
            if "id" in child.attrib and child.attrib["id"].lstrip("0") == id:
                return child

    def getModel(self):
        status = self.getStatus()
        configDir = self.getConfigDir()
        if not configDir:
            return False

        data = {}
        data["main"] = ""
        data["category"] = ""
        data["model"] = ""

        main = self.findChild(configDir, status["H10520"])
        data["main"] = main.attrib["name"]
        category = self.findChild(main, status["H10521"])
        data["category"] = category.attrib["name"]
        model = self.findChild(category, status["H10522"])
        data["model"] = model.attrib["name"]
        return data

    def getID(self):
        status = self.getStatus()
        txt = ""
        for i in range(300, 310):
            if "H12" + str(i) not in status:
                return False
            txt += chr(int(status["H12" + str(i)]))
        return txt

    def getVersion(self):
        status = self.getStatus()
        if int(status["I00022"]) > 0:
            return status["I00020"] + "." + status["I00021"] + "." + status["I00022"]
        return status["I00020"] + "." + status["I00021"]

    def getLatestVersion(self):
        status = self.getStatus()
        if "I10009" in status and int(status["I10009"]) > 0:
            return status["I10007"] + "." + status["I10008"] + "." + status["I10009"]
        if "I10007" in status and "I10008" in status:
            return status["I10007"] + "." + status["I10008"]
        return "0.0"

    def getParams(self, useCache=True):
        if not self.params or not useCache:
            self.params = {}
            self.params["warning"] = []
            self.params["alert"] = []
            self.params["ids"] = []
            self.params["coefs"] = {}
            self.params["offsets"] = {}
            response = requests.get(self.getURL("user/params.xml"))
            if response.status_code == 200:
                xmldoc = ET.fromstring(response.content)
                for param in xmldoc.findall("params"):
                    for child in list(param):
                        if child.tag == "i":
                            if "id" in child.attrib:
                                id = child.attrib["id"]
                                self.params["ids"].append(id)
                                if "flag" in child.attrib:
                                    if child.attrib["flag"] == "W":
                                        self.params["warning"].append(id)
                                    elif child.attrib["flag"] == "A":
                                        self.params["alert"].append(id)

                                if "coef" in child.attrib:
                                    self.params["coefs"][id] = float(
                                        child.attrib["coef"]
                                    )

                                if "offset" in child.attrib:
                                    self.params["offsets"][id] = float(
                                        child.attrib["offset"]
                                    )
        return self.params

    def getStatus(self, useCache=True):
        if not self.status or not useCache:
            response = requests.get(self.getURL("config/xml.xml"))

            if response.status_code == 200:
                if "HTTP: 403 Forbidden" in response.text:
                    self.auth()
                    response = requests.get(self.getURL("config/xml.xml"))
                    if (
                        response.status_code == 200
                        and "HTTP: 403 Forbidden" in response.text
                    ):
                        return False
                if response.status_code == 200:
                    self.status = {}
                    xmldoc = ET.fromstring(response.content)
                    parentData = xmldoc[
                        0
                    ]  # Known paths to data nodes: /RD5WEB/RD5/ and /PCOWEB/PCO/
                    for data in list(parentData):
                        for child in list(data):
                            if child.tag == "O":
                                self.status[child.attrib["I"]] = child.attrib["V"]
        return self.status

    def getTranslation(self, id):
        translations = self.getTranslations()

        if id in translations["params"]:
            param = "params"
        elif id in translations["words"]:
            param = "words"
        else:
            return id

        if "d" in translations[param][id]:
            toBeTranslated = translations[param][id]["d"]
            if toBeTranslated == "not%20to%20be%20translated":
                toBeTranslated = translations[param][id]["t"]
        else:
            if "t" in translations[param][id] and not isinstance(
                translations[param][id], str
            ):
                toBeTranslated = translations[param][id]["t"]
            else:
                toBeTranslated = translations[param][id]

        if hasattr(urllib, "parse"):
            return urllib.parse.unquote(toBeTranslated)
        else:
            return urllib.unquote(toBeTranslated)  # pylint: disable=E1101

    def loadSupportedModes(self):
        status = self.getStatus()
        if status == False:
            return False

        for mode in list(AtreaMode):
            self.writable_modes[mode] = False

        if "I12004" in status and "H11700" in status:
            try:
                binary_writable_modes = "{0:08b}".format(int(status["I12004"]))
                H11700 = int(status["H11700"])
            except AttributeError:
                return False

            for i in range(8):
                if (i == 3 or i == 4) and (int(H11700) == 0):
                    self.writable_modes[i] = False
                else:
                    self.writable_modes[i] = int(binary_writable_modes[7 - i]) != 0
        else:
            response = requests.get(self.getURL("lang/userCtrl.xml"))
            if response.status_code == 200:
                xmldoc = ET.fromstring(response.content)
                modeEcNode = xmldoc.find("./layout/options/op[@id='ModeEC']")
                if modeEcNode:
                    for option in modeEcNode:
                        if "title" in option.attrib:
                            title = option.attrib["title"]
                            mode = None
                            if title == "$perVentilation":
                                mode = AtreaMode.PERIODIC_VENTILATION
                            elif title == "$ventilation":
                                mode = AtreaMode.VENTILATION
                            elif title == "$circulation":
                                mode = AtreaMode.CIRCULATION
                            elif title == "$startUp":
                                mode = AtreaMode.STARTUP
                            elif title == "$runDown":
                                mode = AtreaMode.RUNDOWN
                            elif title == "$defrosting":
                                mode = AtreaMode.DEFROSTING
                            elif title == "$external":
                                mode = AtreaMode.EXTERNAL
                            elif title == "$hpDefrosting":
                                mode = AtreaMode.HP_DEFROSTING
                            elif title == "$nightBefCool":
                                mode = AtreaMode.NIGHT_PRECOOLING
                            elif title == "IN1":
                                mode = AtreaMode.IN1
                            elif title == "IN2":
                                mode = AtreaMode.IN2
                            elif title == "D1":
                                mode = AtreaMode.D1
                            elif title == "D2":
                                mode = AtreaMode.D2
                            elif title == "D3":
                                mode = AtreaMode.D3
                            elif title == "D4":
                                mode = AtreaMode.D4

                            if mode:
                                self.modesToIds[mode] = int(option.attrib["id"])
                                self.idsToModes[int(option.attrib["id"])] = mode
                                if (not "rw" in option.attrib) or option.attrib[
                                    "rw"
                                ] == "1":
                                    self.writable_modes[mode] = True
                else:
                    return False
            else:
                return False

        return self.writable_modes != {}

    def getSupportedModes(self):
        if self.writable_modes == {}:
            self.loadSupportedModes()
        return self.writable_modes

    def getMode(self):
        status = self.getStatus()
        if "H10705" in status:
            return AtreaMode(self.getValue("H10705"))
        elif "H01000" in status:
            return self.idsToModes[self.getValue("H01000")]

    def loadUserLabels(self):
        labels = {}
        response = requests.get(self.getURL("config/texts.xml"))
        if response.status_code == 200:
            xmldoc = ET.fromstring(response.content)
            textsNode = xmldoc.find("texts")
            if textsNode:
                for text in textsNode:
                    labels[text.attrib["id"]] = text.attrib["value"]
        return labels

    def getProgram(self):
        status = self.getStatus()
        if "H10700" in status:
            value = self.getValue("H10700")
            if value == 0:
                return AtreaProgram.MANUAL
            if value == 1:
                return AtreaProgram.WEEKLY
            if value == 2:
                return AtreaProgram.TEMPORARY
        if "H01015" in status:
            value = self.getValue("H01015")
            if value == 1:
                return AtreaProgram.MANUAL
            if value == 0:
                return AtreaProgram.WEEKLY
            if value == 2:
                return AtreaProgram.TEMPORARY

    def getValue(self, key):
        status = self.getStatus()
        if key in status:
            value = int(status[key])
            params = self.getParams()
            if key in params["offsets"]:
                value -= params["offsets"][key]
            if key in params["coefs"]:
                value /= params["coefs"][key]
            return value
        return None

    def getFrontendVersionFromVer(self):
        response = requests.get(self.getURL("ver.txt"))
        if response.status_code == 200:
            version = ""
            try:
                int(response.text[0:2], 16)  # check if response is hexadecimal
                for i in range(3):
                    tmp = int(response.text[2 * i : 2 + 2 * i], 16)
                    if i < 2 or tmp > 0:
                        version += (
                            ("" if i == 0 else ".")
                            + ("0" if tmp < 10 else "")
                            + str(tmp)
                        )
                return version
            except ValueError:
                return False
        return False

    def isAtreaUnit(self):
        response = requests.get(self.getURL("config/login.cgi?magic="))
        if response.status_code == 200:
            xmldoc = ET.fromstring(response.content)
            if xmldoc.text == "denied":
                return True
            elif (
                xmldoc.text is None
                and "HTTP: 404 Page (/config/login.cgi)" in response.text
            ):
                return True if self.getFrontendVersionFromVer() else False
        return False

    def auth(self):
        magic = hashlib.md5(("\r\n" + self.password).encode("utf-8")).hexdigest()
        response = requests.get(self.getURL("config/login.cgi?magic=" + magic))
        if response.status_code == 200:
            xmldoc = ET.fromstring(response.content)
            if xmldoc.text == "denied":
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

        if power < 12 or power > 100:
            return False

        self.setCommand("H10708", power)
        self.setCommand("H01020", power)
        return True

    def exec(self):
        url = self.getURL("config/xml.cgi")

        if len(self.commands) > 0:
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

        if temperature >= 10 and temperature <= 40:
            self.setCommand("H10710", int(temperature * 10))
            self.setCommand("H01021", temperature)
            return True
        return False

    def setCommand(self, id, value):
        params = self.getParams()
        status = self.getStatus()
        if id in params["ids"] or id in status:
            if id in params["coefs"]:
                value = int(value * params["coefs"][id])
            if id in params["offsets"]:
                value = int(value + params["offsets"][id])
            self.commands[id] = f"{value:05}"

    def prepareUpdate(self):
        self.commands["H10006"] = f"{1:05}"
        self.setCommand("H10006", 1)
        return True

    def setProgram(self, program):
        try:
            program += 1
        except TypeError:
            return False
        program -= 1

        if program == AtreaProgram.MANUAL:
            self.setCommand("H10700", 0)
            self.setCommand("H10701", 0)
            self.setCommand("H10702", 0)
            self.setCommand("H10703", 0)
            self.setCommand("H01015", 1)
            self.setCommand("H01016", 1)
            self.setCommand("H01017", 1)
            return True
        elif program == AtreaProgram.WEEKLY:
            self.setCommand("H10700", 1)
            self.setCommand("H10701", 1)
            self.setCommand("H10702", 1)
            self.setCommand("H10703", 1)
            self.setCommand("H01015", 0)
            self.setCommand("H01016", 0)
            self.setCommand("H01017", 0)
            return True
        elif program == AtreaProgram.TEMPORARY:
            self.setCommand("H10700", 2)
            self.setCommand("H10701", 2)
            self.setCommand("H10702", 2)
            if "H10703" in self.commands:
                self.commands.pop("H10703")
            self.setCommand("H01015", 2)
            self.setCommand("H01016", 2)
            self.setCommand("H01017", 2)
            return True

        return False

    def setMode(self, mode):
        try:
            mode += 1
        except TypeError:
            return False
        mode -= 1

        supportedModes = self.getSupportedModes()
        if not supportedModes[mode]:
            return False

        if mode in self.modesToIds:
            id = self.modesToIds[mode]
        else:
            id = int(mode)

        self.setCommand("H10709", id)
        self.setCommand("H01019", id)
        return True
