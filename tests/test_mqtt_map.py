''' This SHOULD be a test file for mqtt_map
21 November 2018: I just cut and paste the "test" part of the mqtt_map.py module here.

TODO: Make it work.
'''

import json
import mqttgateway.mqtt_map as mmap

def test():
    ''' Test function. '''
    # load a valid map in JSON format
    jsonfilepath = './test_map2.json'
    with open(jsonfilepath, 'r') as json_file:
        json_data = json.load(json_file)
    # instantiate a class
    msgmap = mmap.msgMap(json_data)
    # printout some members
    function = msgmap.maps.function.m2i('lighting'); print function
    gateway = msgmap.maps.gateway.m2i('dummy'); print gateway
    location = msgmap.maps.location.m2i('office'); print location
    device = msgmap.maps.device.m2i('kitchen_track'); print device
    sender = msgmap.maps.sender.m2i('me'); print sender
    action = msgmap.maps.action.m2i('light_on'); print action
    m_args = {'key1': 'value1'}
    i_args = {}
    for key, value in m_args.iteritems():
        i_args[msgmap.maps.argkey.m2i(key)] = msgmap.maps.argvalue.m2i(value)
    print i_args

def reverse():
    ''' Another test function.'''
    jsonfilepath = './test_map.json'
    with open(jsonfilepath, 'r') as json_file:
        json_data = json.load(json_file)
    for item in ('function', 'gateway', 'location', 'device', 'sender', 'action', 'argkey', 'argvalue'):
        if 'map' not in json_data[item]: continue
        newmap = {}
        oldmap = json_data[item]['map']
        for key, value in oldmap.iteritems():
            newmap[value] = []
            newmap[value].append(key)
        json_data[item]['map'] = newmap
    print json.dumps(json_data)
    return

if __name__ == '__main__':
    test()
    #reverse()
