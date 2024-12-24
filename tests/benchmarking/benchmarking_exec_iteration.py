#!/usr/bin/env python3

import json
import os
from argparse import ArgumentParser
from benchmarking_exec_utils import *
from update_yml import yml_save, yml_load, yml_add_camera, yml_add_service, yml_remove_service

def build_args():
  args = ArgumentParser()
  args.add_argument('--config', required=True, help='Benchmarking configuration to use')
  args.add_argument('--dataset', required=True, help='Dataset to use.')
  args.add_argument('--network', required=True, help='Temp network to use.')
  args.add_argument('--supass', required=True, help='Temp supass to use.')
  return args

def benchmark_iteration_setup_scene( network, supass, cameras_cfg, scene_cfg, dataset, sensors, tripwires, rois ):

  script_path = os.path.abspath(__file__)
  script_dir = os.path.dirname(script_path)
  #add_or_configure_scene
  sscape_base_cmd = f'python {script_dir}/setup_scene_and_cameras.py'
  sscape_base_cmd += f' --user admin --password {supass}'
  sscape_base_cmd += f' --scene_file {scene_cfg} --dataset {dataset}'

  for sensor in sensors:
    sscape_base_cmd += f' --sensor {sensor}'
  for wire in tripwires:
    sscape_base_cmd += f' --tripwire {wire}'
  for roi in rois:
    sscape_base_cmd += f' --roi {roi}'

  utils_run_sscape_cmdline( network, sscape_base_cmd + ' --setup_scene' )

  return

def benchmark_iteration_add_cameras_to_scene( network, supass, cameras_cfg, scene_cfg, cameras_to_use ):

  script_path = os.path.abspath(__file__)
  script_dir = os.path.dirname(script_path)
  #add_or_configure_scene
  sscape_base_cmd = f'python {script_dir}/setup_scene_and_cameras.py'
  sscape_base_cmd += f' --user admin --password {supass}'
  sscape_base_cmd += f' --scene_file {scene_cfg}'
  for cam in cameras_to_use:
    sscape_cmd_camera = sscape_base_cmd + f' --cameras_file {cameras_cfg} --camera {cam}'
    utils_run_sscape_cmdline( network, sscape_cmd_camera )
  return

def benchmark_iteration_setup_containers( docker_compose, sys_cfg, camera_info, network, cameras, input_base, scene_controller_name, scene_recorder_name, ovcores=None, camera_rate=None ):
  modelconfig = None
  if 'MODELCONFIG' in sys_cfg:
    modelconfig = sys_cfg['MODELCONFIG']

  volumes = ['./models:/opt/intel/openvino/deployment_tools/intel_models', f'./{input_base}:/videos' ]

  for cam in cameras:
    found = False
    for cam_in_info in camera_info:
      if cam == cam_in_info['uid']:
        camera_input = f'/videos/{cam}.mp4'
        camera_id = f'{cam}'
        camera_svc = f'{camera_id}-video'
        fx = cam_in_info['intrinsics']['fx']
        fy = cam_in_info['intrinsics']['fy']
        cx = cam_in_info['intrinsics']['cx']
        cy = cam_in_info['intrinsics']['cy']
        intrinsics = f'{{"fx":{fx},"fy":{fy},"cx":{cx},"cy":{cy}}}'
        yml_add_camera(docker_compose, network, camera_svc, [camera_id], \
                       [camera_input], [intrinsics], sys_cfg['MODEL'], \
                       modelconfig, ovcores=ovcores, volumes=volumes, rate=camera_rate)
        found = True
        break
    if not found:
      print("Camera", cam, "does not exist!")

  #add scene
  scene_controller = yml_add_service( network, ['django',
                                                'controller.auth',
                                                {'source':'root-cert', 'target':'certs/scenescape-ca.pem'},
                                                {'source':'vdms-client-key', 'target':'certs/scenescape-vdms-c.key'},
                                                {'source':'vdms-client-cert', 'target':'certs/scenescape-vdms-c.crt'}])
  #scene_controller = yml_add_service( network, ['django', 'controller.auth'] )
  scene_controller['volumes'] = ['./${DBROOT}/media:/home/scenescape/SceneScape/media', './:/workspace']
  #scene_controller['command'] = 'controller --broker broker.scenescape.intel.com --ntp ntpserv --regulaterate 0.1'
  scene_controller['command'] = 'controller --broker broker.scenescape.intel.com --ntp ntpserv'
  scene_controller['environment'] = [ 'DBROOT' ]
  scene_controller['tty'] = True
  docker_compose['services'][scene_controller_name] = scene_controller

  #add scene_recorder
  scene_recorder = yml_add_service( network, [] )
  scene_recorder['volumes'] = ['./:/workspace']
  scene_recorder['environment'] = ['SUPASS']
  scene_recorder['command'] = 'bash -c "SUPASS=${SUPASS} PYTHONPATH=/workspace tests/perf_tests/scene_perf/scene_mqtt_recorder.py"'
  scene_recorder['tty'] = True
  docker_compose['services'][scene_recorder_name] = scene_recorder

  return

def benchmark_iteration_docker_update(bench_yml_filename, supass, config):
  config['DOCKER_OPTS'] = '--project-directory {} --file {} --progress quiet'.format(os.getcwd(), bench_yml_filename)
  return utils_update_docker( supass, '{}/{}'.format(config['WDIR'],config['DBROOT']), config['DOCKER_OPTS'] )

def benchmark_iteration_log( scene_controller_container_name, scene_recorder_container_name, label, perf_data=None ):
  utils_log_container( scene_controller_container_name, f'scene_controller_log_{label}.txt' )
  utils_log_container( scene_recorder_container_name, f'scene_recorder_log_{label}.txt' )
  if perf_data:
    perf_fname = f'perf_log_{label}.txt'
    with open(perf_fname, 'w') as fd:
      for data in perf_data:
        if isinstance(data,dict):
          json.dump(data, fd)
        else:
          fd.write( data )
        fd.write( '\n' )

  command = f'mv scene_controller_prof_2.0.prof profiler_{label}.prof'
  utils_run_command( command.split(' ') )

  return

def benchmark_iteration_stop(bench_yml_data, sys_cfg, scene_controller_name, scene_recorder_name, cameras):
  yml_remove_service(bench_yml_data, scene_recorder_name)
  yml_remove_service(bench_yml_data, scene_controller_name)

  for cam in cameras:
    camera_svc = f'{cam}-video'
    yml_remove_service(bench_yml_data, camera_svc)
  return

def benchmark_iteration_measure_cpu(services):
  command = 'docker stats --no-stream'
  stdout, stderr, res = utils_run_command_with_stdout(command.split(' '))
  stdout = stdout.decode('utf-8').splitlines()
  results = {}
  for svc in services:
    results[svc] = {}
  if res == 0:
    for line in stdout:
      line_cols = line.split()
      if line_cols[1] in services:
        perf_data = { 'CPU':line_cols[2], 'MEM':line_cols[3] }
        results[ line_cols[1] ] = perf_data
        #print( "perf_data for ", line_cols[1], "is", perf_data )
  else:
    print("Docker stats command failed")
    print(stderr)
  return results
