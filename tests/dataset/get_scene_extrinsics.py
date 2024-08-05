#!/usr/bin/python env

import os
import numpy as np
import cv2
import json
from sscape.rest_client import RESTClient
from argparse import ArgumentParser


def buildArgparser():
  parser = ArgumentParser()
  parser.add_argument('--user', required=True, help='user to log into REST server')
  parser.add_argument('--password', required=True, help='password to log into REST server')
  parser.add_argument('--cameras_output', required=True, help='Output file to write')
  parser.add_argument('--scene_output', required=True, help='Output file to write')
  parser.add_argument('--add', help='thing to add')
  parser.add_argument('--scene', help='scene name to extract')
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

  scene_name = args.scene
  getAllScenes = rest.getScenes({'name': scene_name})
  target_scene = getAllScenes['results'][0]
  print( target_scene )
  with open( args.cameras_output, 'w' ) as fd:
    json.dump( target_scene['cameras'], fd, indent=2 )
  with open( args.scene_output, 'w' ) as fd:
    del target_scene['cameras'] 
    json.dump( target_scene, fd, indent=2 )


  return


if __name__ == '__main__':
  os._exit(main() or 0)
