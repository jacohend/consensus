
import requests, traceback, sys
from geopy.geocoders import Nominatim
import geocoder


def uniquify(lst):
    lst.sort()
    i = len(lst) - 1
    while i > 0:
        if lst[i] == lst[i - 1]:
            lst.pop(i)
        i -= 1
    return lst

def subtract(ls, m):
    result = []
    for i in ls:
        found = False
        for j in m:
            if i==j:
                found = True
        if not found:
            result.append(i)
    return result

def associate(children, parents):
    orphans = []
    for child in children:
        found = False
        for parent in parents:
            if child.parent == parent.id:
                parent["children"].append(child)
                found = True
        if not found:
            orphans.append(child)
    return orphans, parents


def get_city(city):
    g = geocoder.google(city)
    g = g.json
    if "city" in g and "lat" in g and "lon" in g:
        return {"city": g["city"], "latitude": g["lat"], "longitude": g["lon"]}


def get_toponym(ip):
    sys.stderr.write("looking up locale for ip {}".format(ip))
    try:
        g = geocoder.ip(ip) 
        print(str(g))
        if g.latlng:
            return {"city": g.city, "latitude": g.latlng[0], "longitude": g.latlng[1]}
        elif g.city:
            return get_city(city)
        else:
            return {"city": "unknown", "latitude": 0.0, "longitude": 0.0}
    except Exception as e:
        traceback.print_exc()
    return {}


def toponum_fuzzer(tn):
    location = geolocator.geocode(tn["city"])
    return {"latitude":location.latitude, "longitude":location.longitude, "real":tn}