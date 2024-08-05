#!/usr/bin/python env

import os
import numpy as np
import cv2
from sscape.rest_client import RESTClient
from argparse import ArgumentParser


def buildArgparser():
  parser = ArgumentParser()
  parser.add_argument('--user', required=True, help='user to log into REST server')
  parser.add_argument('--password', required=True, help='password to log into REST server')
  parser.add_argument('--add', help='thing to add')
  parser.add_argument('--scene', help='scene name to add')
  parser.add_argument('--camera', help='camera to add')
  parser.add_argument('--translation', help='camera translation')
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

  print(args)
  rest = RESTClient(args.resturl, rootcert=args.rootcert)
  assert rest.authenticate(args.user, args.password)

  """ Verifies that camera can exist even if the scene associated with it is deleted.
  Also verifies that the orphaned camera can be assigned to another scene.

  Steps:
    * Create new scene
    * Create new camera and assign to the new scene
    * Delete the new scene
    * Check the orphaned camera still exists in all camera list
    * Add orphaned camera to another scene
    * Get the entire list of cameras and verify that the new camera is has the new scene ID
  """

  try:
    if args.add and args.add == 'scene':
      
      scene_name = args.scene
      rows = 2500
      cols = 10000
      channels = 3
      map_data = np.zeros((rows, cols, channels), dtype = "uint8")
      for r in range( 0, rows, 100 ):
        cv2.line( map_data, (0, r), (cols-1,r), (255,255,255), 3 )
      for c in range( 0, cols, 1000 ):
        cv2.line( map_data, (c, 0), (c,rows-1), (255,255,255), 3 )

      map_image = 'tmp.jpg'
      map_image = "/workspace/media/tmp.jpg"
      cv2.imwrite( map_image, map_data )
  
      with open(map_image, "rb") as f:
        map_data = f.read()

      parent_scene = rest.createScene({'name': scene_name, 'map': (map_image, map_data), 'scale': 99.0})
      assert parent_scene, (parent_scene.statusCode, parent_scene.errors)

    if args.add and args.add == 'camera' and args.camera:
      scene_name = args.scene
      target_scene_id = -1
      target_scene_found = False
      getAllScenes = rest.getScenes({'name': scene_name})
      if getAllScenes['count'] == 1:
        target_scene_found = True
        target_scene_id = getAllScenes['results'][0]['uid']

      if target_scene_found:
        camera_name = args.camera
        translation = [0, 0, 0]
        rotation = [-125.0, 0.0, 0.0]
        scale = [1.0, 1.0, 1.0]
        if args.translation:
          arg_translation = args.translation.split(',')
          for idx in range(len(arg_translation)):
            if idx >= 3:
              break
            translation[idx] += float(arg_translation[idx])
        print("Using translation", translation)    
        camera_data = { 'name': camera_name, 'scene': '1', 'translation':  translation, 'rotation': rotation , 'scale': scale , 'transform_type': 'euler' }
        camera_data['scene'] = f'{target_scene_id}'
        camera_data['name'] = camera_name
        print(camera_data)
        newCamera = rest.createCamera(camera_data)
        assert newCamera, (newCamera.statusCode, newCamera.errors)

    getAllCameras = rest.getCameras({})
    print(getAllCameras)

  except:
    print("Something failed")

  return


if __name__ == '__main__':
  os._exit(main() or 0)
