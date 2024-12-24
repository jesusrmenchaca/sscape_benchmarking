#!/usr/bin/env python3

import yaml
from argparse import ArgumentParser

def build_args():
  parser = ArgumentParser()
  parser.add_argument('--file', required=True, help='docker-compose.yml file to process')
  parser.add_argument('--add_camera', help='Add a camera')
  parser.add_argument('--framerate', help='Camera rate')
  parser.add_argument('--ovcores', help='OVCores setting for container')
  parser.add_argument('--input', help='Input file to use', action='append')
  parser.add_argument('--intrinsics', help='Intrinsics string to use', action='append')
  parser.add_argument('--mqttid', help='MQTT IDs to use', action='append')
  parser.add_argument('--model', help='Model to use', default='retail')
  parser.add_argument('--delete_service', help='Delete a service')
  parser.add_argument('--add_scene_recorder', help='Add the mqtt recorder to the yml file')
  parser.add_argument('--network', default='scenescape', help='Configure the network name')
  return parser

def yml_add_service( network_name, add_secrets ):
  srv = {}
  srv['image'] = 'scenescape:latest'
  srv['init'] = True
  srv['networks'] = { network_name : None }
  srv['depends_on'] = ['broker', 'ntpserv']
  srv['privileged'] = True
  srv['secrets'] = [] #['certs']
  if len(add_secrets):
    srv['secrets'].extend(add_secrets)
  srv['restart'] = 'always'

  return srv

def yml_add_camera(docker_compose, network, add_camera, mqttid, \
                  input, intrinsics, model, modelconfig, \
                  ovcores=None, volumes=None, rate=None):
  #print("Add cameras IDs",  mqttid, len(mqttid))
  if not add_camera in docker_compose['services']:
    srv = yml_add_service( network, ['percebro.auth', {'source':'root-cert','target':'certs/scenescape-ca.pem'}] )
    srv['command'] = ['percebro']
    assert len(mqttid) == len(input)
    if len(intrinsics) != 1:
      assert len(intrinsics) == len(input)
    for idx, _ in enumerate(input):
      srv['command'].extend( [f'--camera={input[idx]}'] )
      srv['command'].extend( [f'--cameraid={mqttid[idx]}'] )
      if len(intrinsics) == 1:
        srv['command'].extend( [f'--intrinsics={intrinsics[0]}'] )
      else:
        srv['command'].extend( [f'--intrinsics={intrinsics[idx]}'] )
    srv['command'].extend( [f'--camerachain={model}'] )
    if modelconfig is not None:
      srv['command'].extend( [f'--modelconfig={modelconfig}'] )
    if ovcores is not None:
      srv['command'].extend( [f'--ovcores={ovcores}'] )
    if rate is not None:
      srv['command'].extend( [f'--framerate={rate}'] )
    srv['command'].extend( ["--ntp=ntpserv","--auth=/run/secrets/percebro.auth","broker.scenescape.intel.com"] )
    if volumes is None:
      srv['volumes'] = ['./models:/opt/intel/openvino/deployment_tools/intel_models', './:/workspace', './videos:/videos' ]
    else:
      srv['volumes'] = volumes

    docker_compose['services'][add_camera] = srv
  return

def yml_load(filename, image_version=None):
  docker_compose = {}
  with open(filename) as input_fd:
    docker_compose = yaml.load(input_fd,Loader=yaml.Loader)
  if image_version:
    for svc in docker_compose['services']:
      docker_compose['services'][svc]['image'] += ':' + image_version
      print("After load Svc", svc, "has image", docker_compose['services'][svc]['image'])
  return docker_compose

def yml_save(docker_compose, filename):
  output_fd = open(filename, 'w')
  if output_fd :
    yaml.dump(docker_compose, output_fd)
  return

def yml_find_container_by_command(docker_compose, command):
  found = []
  for svc in docker_compose['services']:
    if 'command' in docker_compose['services'][svc] and command in docker_compose['services'][svc]['command']:
      found.append(svc)
  return found

def yml_find_container_by_name(docker_compose, svc_name):
  found = []
  for svc in docker_compose['services']:
    if svc == svc_name:
      found.append(svc)
  return found

def yml_replace_network(docker_compose, new_net_name):
  old_network = list(docker_compose['networks'].keys())[0]
  docker_compose['networks'] = { new_net_name: None }
  for svc in docker_compose['services']:
    print("Svc", svc, "has image", docker_compose['services'][svc]['image'])
    new_net = {new_net_name: None}
    if docker_compose['services'][svc]['networks'][old_network] is not None:
      new_net[new_net_name] = docker_compose['services'][svc]['networks'][old_network]
    docker_compose['services'][svc]['networks'] = new_net
  return

def yml_remove_service(docker_compose, service):
  if service in docker_compose['services']:
    del docker_compose['services'][service]
  return

def yml_add_recorder_service(docker_compose,recorder_name, network_name):
  if not recorder_name in docker_compose['services']:
    srv = yml_add_service( network_name, ['percebro.auth'] )
    srv['command'] = f'bash -c "PYTHONPATH=/workspace tests/perf_tests/scene_perf/scene_mqtt_recorder.py "'
    srv['volumes'] = ['./:/workspace' ]
    srv['tty'] = True
    docker_compose['services'][recorder_name] = srv
  return

def main():
  args = build_args().parse_args()

  docker_compose = yml_load(args.file)

  if args.add_camera is not None:
    yml_add_camera(docker_compose, args.network, args.add_camera, args.mqttid, args.input, args.intrinsics, args.model, args.modelconfig, ovcores=args.ovcores, rate=args.framerate)

  if args.add_scene_recorder is not None and (not args.add_scene_recorder in docker_compose['services']):
    yml_add_recorder_service(docker_compose, args.add_scene_recorder, args.network)

  if args.delete_service is not None and args.delete_service in docker_compose['services']:
    yml_remove_service(docker_compose, args.delete_service)

  yml_save(docker_compose,args.file)
  return
  
if __name__ == '__main__':
  exit( main() or 0 )
