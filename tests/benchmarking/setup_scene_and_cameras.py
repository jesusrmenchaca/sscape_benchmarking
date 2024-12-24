#!/usr/bin/python env

import os
import numpy as np
import json
import cv2
from sscape.rest_client import RESTClient
from argparse import ArgumentParser


def buildArgparser():
  parser = ArgumentParser()
  parser.add_argument('--user', required=True, help='user to log into REST server')
  parser.add_argument('--password', required=True, help='password to log into REST server')
  parser.add_argument('--camera', action='append' )
  parser.add_argument('--sensor', action='append' )
  parser.add_argument('--tripwire', action='append' )
  parser.add_argument('--roi', action='append' )
  parser.add_argument('--all', action='store_true' )
  parser.add_argument('--remove_all', action='store_true' )
  parser.add_argument('--setup_scene', action='store_true' )
  parser.add_argument('--dataset')
  parser.add_argument('--scene_file', help='scene configuration file', required=True)
  parser.add_argument('--cameras_file', help='camera configuration file')
  parser.add_argument('--auth', default='/run/secrets/percebro.auth',
                      help='user:password or JSON file for MQTT authentication')
  parser.add_argument('--rootcert', default='/run/secrets/certs/scenescape-ca.pem',
                      help='path to ca certificate')
  parser.add_argument('--broker', default='broker.scenescape.intel.com:1883',
                      help='hostname or IP of MQTT broker, optional :port')
  parser.add_argument('--resturl', default='https://web.scenescape.intel.com/api/v1',
                      help='URL of REST server')
  return parser


def main():
  args = buildArgparser().parse_args()

  #print(args)
  rest = RESTClient(args.resturl, rootcert=args.rootcert)
  assert rest.authenticate(args.user, args.password)

  scene_data = {}
  camera_data = {}
  
  with open( args.scene_file ) as fd:
    scene_data = json.load( fd )

    
  scene_name = scene_data['name']
  if args.setup_scene:
    getScene = rest.getScenes({'name': scene_name})
    if getScene['count'] == 1:

      scene_map_fname = '{}/{}'.format(args.dataset,scene_data['map'])
      map_data = cv2.imread( scene_map_fname )
      map_image = "/workspace/media/tmp.jpg"
      cv2.imwrite( map_image, map_data )
      with open(map_image, "rb") as f:
        map_data = f.read()
      parent_scene = rest.updateScene( getScene['results'][0]['uid'], {'map': (map_image, map_data), 'scale': scene_data['scale']})
      assert parent_scene, (parent_scene.statusCode, parent_scene.errors)

    else:

      scene_map_fname = '{}/{}'.format(args.dataset,scene_data['map'])
      map_data = cv2.imread( scene_map_fname )
      map_image = "/workspace/media/tmp.jpg"
      cv2.imwrite( map_image, map_data )
      with open(map_image, "rb") as f:
        map_data = f.read()
      parent_scene = rest.createScene({'name': scene_name, 'map': (map_image, map_data), 'scale': scene_data['scale']})
      assert parent_scene, (parent_scene.statusCode, parent_scene.errors)

  if args.remove_all:
    for objtype in ('region', 'sensor', 'tripwire', 'camera'):
      data = rest._get(f'{objtype}s', {})

      for item in data['results']:
        #print("Item", item)
        uid = item['uid']
        #print(f"Deleting {objtype} id {uid}")
        rest._delete(f"{objtype}/{uid}")
        
  target_scene_id = -1
  target_scene_found = False
  getAllScenes = rest.getScenes({'name': scene_name})
  if getAllScenes['count'] == 1:
    target_scene_id = getAllScenes['results'][0]['uid']
    target_scene_found = True
  else:
    return 1

  if 'regions' in scene_data and args.roi:
    for region in scene_data['regions']:
      if not region['name'] in args.roi:
        continue
      region_name = region['name']
      
      existing_regions = rest.getRegions({'name': region_name})
      if existing_regions['count'] != 0:
        rest.deleteRegion( existing_regions['results'][0]['uid'] )

      region_data = {}
      region_data['name'] = region_name
      region_data['points'] = region['points']
      region_data['scene'] = target_scene_id
      rest.createRegion(region_data)

  if 'tripwires' in scene_data and args.tripwire:
    for wire in scene_data['tripwires']:
      if wire['name'] not in args.tripwire:
        continue
      wire_name = wire['name']
      
      existing_wires = rest.getTripwires({'name': wire_name})
      if existing_wires['count'] != 0:
        rest.deleteTripwire( existing_wires['results'][0]['uid'] )

      wire_data = {}
      wire_data['name'] = wire_name
      wire_data['points'] = wire['points']
      wire_data['scene'] = target_scene_id
      rest.createTripwire(wire_data)

  if 'sensors' in scene_data and args.sensor:
    for sensor in scene_data['sensors']:
      if sensor['name'] not in args.sensor:
        continue
      sensor_name = sensor['name']
      existing_sensor = rest.getSensors({'name': sensor_name})
      if existing_sensor['count'] != 0:
        rest.deleteSensor( existing_sensor['results'][0]['uid'] )

      sensor_data = {}
      sensor_data['area'] = sensor['area']
      
      sensor_data['translation'] = sensor['translation']
      if sensor_data['area'] != 'scene':
        sensor_data['center'] = sensor['center']

        sensor_data['radius'] = sensor['radius']

      if sensor_data['area'] == 'poly':
        sensor_data['points'] = sensor['points']
      
      sensor_data['scene'] = target_scene_id
      sensor_data['name'] = sensor_name
      sensor_data['sensor_id'] = sensor_name
      sensor_db = rest.createSensor(sensor_data)
      assert sensor_db, (sensor_db.statusCode, sensor_db.errors)
      


  if args.cameras_file:
    with open( args.cameras_file ) as fd:
      camera_data = json.load( fd )
    for cam in camera_data:
      #print("Checking for", cam['name'])
      if args.all or (args.camera and cam['name'] in args.camera):
        camera_name = cam['name']
        translation = cam['translation']
        rotation = cam['rotation']
        distortion = cam['distortion']
        scale = cam['scale']
      
        camera_data = { 'name': camera_name, 'scene': target_scene_id, 'translation':  translation, 'rotation': rotation , 'scale': scale , 'transform_type': 'euler' }

        getCameraData = rest.getCameras({'name': camera_name})
        if getCameraData['count'] == 1:
          #print("Existing camera", getCameraData)
          rest.updateCamera(camera_data, getCameraData['results'][0]['uid'])
        else:
          newCamera = rest.createCamera(camera_data)
          assert newCamera, (newCamera.statusCode, newCamera.errors)



  return

if __name__ == '__main__':
  os._exit(main() or 0)
