# PyAtrea
Python library for communication with Atrea ventilation units

## Usage examples:

### Initiate library:
```
atrea = Atrea("192.168.0.2","passwordOnAtreaWebsite")
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