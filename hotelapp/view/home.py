from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your view here.
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.urlresolvers import reverse




import json
from hotelapp.models import MapItem

from hotelapp.django.mongoserialize import MongoAwareEncoder

def get_Geojson(date,hour):
    jsonfile=MapItem.objects().filter(properties__date=date,properties__hour=hour).all().to_json()
    jsonString=json.loads(jsonfile)
    my_layer = {
    "type": "FeatureCollection",
    "features": jsonString,
    "crs": {
        "type": "link",
        "properties": {"href": "http://spatialreference.org/ref/epsg/4326", "type": "proj4"} }}

    #with open("/root/Desktop/DataChallenge/telefonica9.geojson", "w") as f:
    #f.write(json.dumps(my_layer, cls=MongoAwareEncoder, ensure_ascii=False))
    return json.dumps(my_layer, cls=MongoAwareEncoder, ensure_ascii=False)
from hotelapp.models import TelefonicaMap

@login_required
def main(request):
    TelMap = TelefonicaMap.objects.all()
    bbox = json.dumps(TelMap.extent())
    mapgeo=get_Geojson('2014-01-01',22)
    if request.is_ajax():

        return HttpResponse(mapgeo, mimetype='application/json')
    else:
        return render_to_response('map.html', { 'bbox': bbox }, context_instance=RequestContext(request))


"""
def main(request):
    TelMap = TelefonicaMap.objects.all()
    bbox = json.dumps(TelMap.extent())
    mapgeo=get_Geojson('2014-01-01',22)
    if request.is_ajax():
        '''d = {}
        for county in counties.geojson():
            geojson = json.loads(county.geojson)
            properties = {'name': county.name_trans, 'bbox':county.mpoly.extent, 'center':county.mpoly.point_on_surface.coords}
            geojson['id'] = county.geo_id
            geojson['properties'] = properties
            d[county.geo_id] = geojson'''
        return HttpResponse(mapgeo, mimetype='application/json')
    else:
        return render_to_response('complex-county.html', { 'bbox': bbox }, context_instance=RequestContext(request))
    """