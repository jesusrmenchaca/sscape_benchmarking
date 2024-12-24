#!/usr/bin/python env

import os
import numpy as np
import json
import cv2
from sscape.rest_client import RESTClient
from argparse import ArgumentParser
from update_yml import yml_load, yml_save, yml_add_camera


def buildArgparser():
  parser = ArgumentParser()
  parser.add_argument('--user', required=True, help='user to log into REST server')
  parser.add_argument('--password', required=True, help='password to log into REST server')
  parser.add_argument('--query', action='store_true')
  parser.add_argument('--map_file', help='scene map file')
  parser.add_argument('--map_image_file', help='scene map image file')
  parser.add_argument('--scene_name', help='Scene name to give' )
  parser.add_argument('--update_yml', help='docker-compose.yml file to update' )
  parser.add_argument('--model', help='Inference model to use', default='retail' )
  parser.add_argument('--modelconfig', help='Inference modelconfig to use' )
  parser.add_argument('--input_base', help='Video input base directory' )
  parser.add_argument('--single_container', action='store_true', 
                      help='Force all video input to be tied to one container.' )
  parser.add_argument('--clean', action='store_true',
                      help='Removes scene and cameras from map' )
  parser.add_argument('--clean_all', action='store_true',
                      help='Cleans the whole db.')
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

  if args.query:
    
    all_cameras = rest.getCameras(None)
    print("Exisiting cameras:")
    for cam in range(all_cameras['count']):
      print( all_cameras['results'][cam] )
    

  if args.clean_all:
    all_scenes = rest.getScenes(None)
    if all_scenes['count'] > 0:
      for scene in range(all_scenes['count']):
        scene_id = all_scenes['results'][scene]['uid']
        rest.deleteScene(scene_id)
    
    all_cameras = rest.getCameras(None)
    if all_cameras['count'] > 0:
      for cam in range(all_cameras['count']):
        cam_id = all_cameras['results'][cam]['uid']
        rest.deleteCamera(cam_id)
  
  if args.map_file:
    with open( args.map_file ) as fd:
      map_data = json.load( fd )
    
    scene_name = args.scene_name if args.scene_name else map_data['Name']
    target_scene_found = False
    target_scene_id = -1
    scene_scale = 0.0

    image_filename = args.map_image_file if args.map_image_file else map_data['map']
    if not os.path.exists(image_filename):
      print("Error, no such file found", image_filename)

    else:
      map_file_data = cv2.imread( image_filename )
      map_image = "/workspace/media/tmp.jpg"
      cv2.imwrite( map_image, map_file_data )
      with open(map_image, "rb") as f:
        map_file_data = f.read()

      existing_scene = rest.getScenes({'name': scene_name})
      if existing_scene['count'] == 1:
        #delete camera, it already exists.
        #print("Deleting existing scene")
        rest.deleteScene(existing_scene['results'][0]['uid'])

      scene_scale = map_data['Scale']
      parent_scene = rest.createScene({'name': scene_name, 'map': (map_image, map_file_data), 'scale': scene_scale})
      assert parent_scene, (parent_scene.statusCode, parent_scene.errors)

      all_scenes_data = rest.getScenes({'name': scene_name})
      if all_scenes_data['count'] == 1:
        target_scene_found = True
        target_scene_id = all_scenes_data['results'][0]['uid']

    for cam in map_data['Sensors']:
      camera_data = {}
      camera_data['name'] = cam
      camera_data['scene'] = f'{target_scene_id}'
      camera_data['sensor_id'] = cam

      camera_data['transform1'] = map_data['Sensors'][cam]['camera_homography'][0]['x']
      camera_data['transform2'] = map_data['Sensors'][cam]['camera_homography'][0]['y']
      camera_data['transform3'] = map_data['Sensors'][cam]['camera_homography'][1]['x']
      camera_data['transform4'] = map_data['Sensors'][cam]['camera_homography'][1]['y']
      camera_data['transform5'] = map_data['Sensors'][cam]['camera_homography'][2]['x']
      camera_data['transform6'] = map_data['Sensors'][cam]['camera_homography'][2]['y']
      camera_data['transform7'] = map_data['Sensors'][cam]['camera_homography'][3]['x']
      camera_data['transform8'] = map_data['Sensors'][cam]['camera_homography'][3]['y']

      camera_data['transform9'] = map_data['Sensors'][cam]['map_homography'][0]['x']/scene_scale
      camera_data['transform10'] = map_data['Sensors'][cam]['map_homography'][0]['y']/scene_scale
      camera_data['transform11'] = map_data['Sensors'][cam]['map_homography'][1]['x']/scene_scale
      camera_data['transform12'] = map_data['Sensors'][cam]['map_homography'][1]['y']/scene_scale
      camera_data['transform13'] = map_data['Sensors'][cam]['map_homography'][2]['x']/scene_scale
      camera_data['transform14'] = map_data['Sensors'][cam]['map_homography'][2]['y']/scene_scale
      camera_data['transform15'] = map_data['Sensors'][cam]['map_homography'][3]['x']/scene_scale
      camera_data['transform16'] = map_data['Sensors'][cam]['map_homography'][3]['y']/scene_scale
      
      #camera_data['translation'] = [0, 0, 0]
      #camera_data['rotation'] = [-125.0, 0.0, 0.0]
      camera_data['scale'] = [1.0, 1.0, 1.0]
      camera_data['transform_type'] = 'homography'

      existing_camera = rest.getCameras({'name': cam})
      if existing_camera['count'] == 1:
        #delete camera, it already exists.
        print("Deleting existing camera")
        rest.deleteCamera(existing_camera['results'][0]['uid'])
      

      #print("Creating new camera", cam)
      newCamera = rest.createCamera(camera_data)
      assert newCamera, (newCamera.statusCode, newCamera.errors)

    if args.update_yml:
      yml_data = yml_load(args.update_yml)
      network_name = list(yml_data['networks'].keys())[0]
      input_volumes = [f'./{args.input_base}:/videos', './models:/opt/intel/openvino/deployment_tools/intel_models']
      #print("Using network", network_name)
      
      inputs = []
      intrinsics = []
      cameras = []
      for cam in map_data['Sensors']:
        #cam_input = './videos/'.format(map_data['Sensors'][cam]['input'])
        cam_input = f'/videos/{cam}.mp4'
        
        fx = map_data['Sensors'][cam]['intrinsics']['fx']
        fy = map_data['Sensors'][cam]['intrinsics']['fy']
        cx = map_data['Sensors'][cam]['intrinsics']['cx']
        cy = map_data['Sensors'][cam]['intrinsics']['cy']
        intrinsics_cmd = '{{"fx":{},"fy":{},"cx":{},"cy":{}}}'.format(fx,fy,cx,cy)
        if args.single_container:
          inputs.append(cam_input)
          cameras.append(cam)
          intrinsics.append(intrinsics_cmd)
        else:
          cam_container_name = f'{cam}-video'
          yml_add_camera(yml_data, network_name, cam_container_name, \
                        [cam], [cam_input], [intrinsics_cmd], \
                        args.model, args.modelconfig, input_volumes)
      if args.single_container:
        #print("Adding aggregated-camera container")
        yml_add_camera(yml_data, network_name, 'aggregated-video', \
                       cameras, inputs, intrinsics, \
                       args.model, args.modelconfig, input_volumes)
      yml_save(yml_data, args.update_yml)
  


  return

if __name__ == '__main__':
  os._exit(main() or 0)
