# PyAtrea

Python library for communication with Atrea ventilation units

## Install:

```
python3 -m pip install pyatrea
```

## Usage examples:

### Initiate library:

```
from pyatrea import pyatrea

atrea = pyatrea.Atrea("192.168.0.2","passwordOnAtreaWebsite")
```

### Get status of your unit with human readable identifications (if available):

```
status = atrea.getStatus()
if(status == False):
    exit("Authentication failed")

for id, value in status.items():
    print(atrea.getTranslation(id) + ":" + value)
```

### Get human readable warnings and errors:

```
status = atrea.getStatus()
params = atrea.getParams()

for warning in params['warning']:
    if status[warning] == "1":
        print(atrea.getTranslation(warning))
for alert in params['alert']:
    if status[alert] == "1":
        print(atrea.getTranslation(alert))
```

# Development

## Linters

Project includes all settings for VSCode and uses flake8 and black for formatting.

If you are using Visual Studio Code, all you will need to install is black via pip, and visual studio code should offer to install needed extensions.
