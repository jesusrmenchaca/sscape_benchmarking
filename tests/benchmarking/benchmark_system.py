#!/usr/bin/env python3

import time
from argparse import ArgumentParser
from benchmarking_exec_system import *
from benchmarking_exec_iteration import *
from update_yml import yml_load, yml_save, yml_replace_network, yml_find_container_by_command, yml_remove_service

def build_args():
  args = ArgumentParser()
  args.add_argument('--config', required=True, help='Benchmarking configuration to use')
  args.add_argument('--dataset', required=True, help='Dataset to use')
  args.add_argument('--label', required=True, help='Run label to use')
  args.add_argument('--version', default='latest', help='Image version')
  return args

def benchmark_run_start(sys_cfg):
  sys_started = benchmark_system_start(sys_cfg)
  if not sys_started:
    print("Something failed during bring-up!")

  return sys_started

def benchmark_run_stop(sys_cfg):
  benchmark_system_stop(sys_cfg)
  return 0

def benchmark_run_iteration(sys_cfg, dataset, cameras, sensors, tripwires, rois, label, camera_rate=None):

  cameras_cfg = f'{dataset}/cameras.json'
  scene_cfg = f'{dataset}/scene.json'
  input_base = f'{dataset}/videos'

  camera_info = {}
  with open(cameras_cfg) as fd:
    camera_info = json.load(fd)

  bench_yml_filename = '{}/docker-compose.yml'.format(sys_cfg['WDIR'])

  utils_system_wait()

  docker_network_name = utils_find_network_name(sys_cfg['runtime_network'])

  benchmark_iteration_setup_scene(docker_network_name, sys_cfg['SUPASS'], \
                                  cameras_cfg, scene_cfg, dataset, \
                                  sensors, tripwires, rois)

  benchmark_iteration_add_cameras_to_scene(docker_network_name, sys_cfg['SUPASS'], \
                                   cameras_cfg, scene_cfg, \
                                   cameras)
  bench_yml_data = yml_load(bench_yml_filename)
  scene_controller_name = 'scene_controller'
  scene_recorder_name = 'scene_recorder'
  ovcores_setting = getattr(sys_cfg, 'OVCORES_PER_CAMERA', None)
  if ovcores_setting is not None:
    ovcores_setting = int(ovcores_setting) * len(cameras)
    if 'MAX_OVCORES' in sys_cfg:
      ovcores_setting = max(ovcores_setting, sys_cfg['MAX_OVCORES'])
  benchmark_iteration_setup_containers(bench_yml_data, sys_cfg, camera_info, \
                                        sys_cfg['runtime_network'], cameras, \
                                        input_base, \
                                        scene_controller_name, scene_recorder_name, \
                                        ovcores = ovcores_setting, camera_rate = camera_rate )
  yml_save(bench_yml_data, bench_yml_filename)

  #kick off docker compose
  run_ok = benchmark_iteration_docker_update(bench_yml_filename, sys_cfg['SUPASS'], sys_cfg)
  perf_data = []
  # wait for ~30 s
  if run_ok:
    time.sleep(5)
    scene_controller_system_name = utils_find_container_system_name(scene_controller_name)[0]
    scene_recorder_system_name = utils_find_container_system_name(scene_recorder_name)[0]

    timer = 0
    time_start = time.time()
    steps = 0
    print()
    while timer < sys_cfg['RUN_TIME']:
      #time.sleep(5)
      perf_data.append(benchmark_iteration_measure_cpu([scene_controller_system_name]))

      time_now = time.time()
      timer = int(time_now - time_start)
      steps += 1
      if (steps%10) == 0:
        print( sys_cfg['RUN_TIME'] - timer, " remaining")
    #time.sleep(sys_cfg['RUN_TIME'])
  else:
    print( "Failed updating iteration")

  # Get log from mqtt-recorder, scene controller.
  benchmark_iteration_log(scene_controller_system_name, scene_recorder_system_name, label, perf_data)

  # Remove the video, scene, and recorder containers
  benchmark_iteration_stop(bench_yml_data, sys_cfg, scene_controller_name, scene_recorder_name, cameras)
  yml_save(bench_yml_data, bench_yml_filename)

  # This stops the removed services.
  run_ok = benchmark_iteration_docker_update(bench_yml_filename, sys_cfg['SUPASS'], sys_cfg)

  #utils_system_wait()

  return 0


def main():
  args = build_args().parse_args()

  print("System: Initial setup", args.version)
  sys_cfg = benchmark_system_setup(args.config, args.version)

  scene_cfg = f'{args.dataset}/scene.json'
  with open( scene_cfg ) as fd:
    scene_data = json.load( fd )

  all_sensors = []
  all_tripwires = []
  all_rois = []
  if 'sensors' in scene_data:
    for sensor in scene_data['sensors']:
      all_sensors.append(sensor['name'])
  if 'tripwires' in scene_data:
    for wire in scene_data['tripwires']:
      all_tripwires.append(wire['name'])
  if 'regions' in scene_data:
    for roi in scene_data['regions']:
      all_rois.append(roi['name'])

  print("Sensors found", all_sensors)
  print("Wires found", all_tripwires)
  print("ROIs found", all_rois)

  camera_rate = None
  if 'CAMERA_RATE' in sys_cfg:
    camera_rate = sys_cfg['CAMERA_RATE']
  result = 1
  min_cameras = 0
  cameras = []
  if 'MIN_CAMERAS' in sys_cfg:
    for iteration in range(sys_cfg['MIN_CAMERAS'] - 1):
      cameras.append(f'Cam{iteration}')
      min_cameras += 1
  print("System: Starting ..")
  if benchmark_run_start(sys_cfg):
    result = 0
    for iteration in range(min_cameras, sys_cfg['MAX_CAMERAS']):
      print("Starting iteration", iteration)
      cameras.append(f'Cam{iteration}')

      if 'CAMERA_ACCUM_RATE' in sys_cfg:
        camera_rate = float(sys_cfg['CAMERA_ACCUM_RATE']) / float(len(cameras))

      iterate_tripwires = all_tripwires
      num_wires = 1
      if sys_cfg['ITERATE_TRIPWIRES']:
        iterate_tripwires = []
        num_wires = 1 + len(all_tripwires)

      for num_wire in range(num_wires):

        iterate_sensors   = all_sensors
        num_sensors = 1
        if sys_cfg['ITERATE_SENSORS']:
          iterate_sensors = []
          num_sensors = 1 + len(all_sensors)
        for num_sensor in range(num_sensors):

          iterate_rois      = all_rois
          num_rois = 1
          if sys_cfg['ITERATE_ROIS']:
            iterate_rois = []
            num_rois = 1 + len(all_rois)
          for num_roi in range(num_rois):


            iteration_label = f'{args.label}_{iteration+1}cameras_{num_wire}tripwires_{num_sensor}sensors_{num_roi}rois'

            print("Running iteration {}/{} on {}".format(iteration,sys_cfg['MAX_CAMERAS'], len(cameras), len(iterate_sensors)))
            benchmark_run_iteration(sys_cfg, args.dataset, cameras, iterate_sensors, iterate_tripwires, iterate_rois, iteration_label, camera_rate=camera_rate)
            if num_roi:
              iterate_rois.append( all_rois[num_roi-1] )

          if num_sensor:
            iterate_sensors.append( all_sensors[num_sensor-1] )
        if num_wire:
          iterate_tripwires.append( all_tripwires[num_wire-1] )

      print(" ...  done")
    print("Test done, saving log")
    benchmark_system_log(sys_cfg, args.label)
    benchmark_run_stop(sys_cfg)

  return

if __name__ == '__main__':
  exit(main() or 0)
