#!/usr/bin/env python3

import json
import os
import shutil
import time
from update_yml import yml_load, yml_save, yml_replace_network, yml_find_container_by_command, yml_remove_service
from benchmarking_exec_utils import *

## Stuff from utils

from argparse import ArgumentParser

sample_yml = 'sample_data/docker-compose-example.yml'


def benchmark_system_setup(test_config):
  test_pid = os.getpid()
  config = None
  with open(test_config) as fd:
    config = json.load(fd)

  if not utils_check_config(config, 'TEST_NAME'):
    config['TEST_NAME'] = f'test_{test_pid}'

  if not utils_check_config(config, 'DBROOT'):
    config['DBROOT'] = '{}_db'.format(config['TEST_NAME'])

  if not utils_check_config(config, 'WDIR'):
    config['WDIR'] = '{}_wdir'.format(config['TEST_NAME'])

  if not utils_check_config(config, 'SUPASS'):
    config['SUPASS'] = 'tmppass123'

  if not utils_check_config(config, 'BASE_YML'):  
    config['BASE_YML'] = sample_yml

  # Clean-up test-root
  utils_clean_directory(config['WDIR'])

  # Clean-up dbroot
  utils_clean_directory('{}/{}'.format(config['WDIR'],config['DBROOT']))
  db_required_dirs = ['db', 'media', 'migrations']
  for dir in db_required_dirs:
    utils_clean_directory('{}/{}/{}'.format(config['WDIR'],config['DBROOT'], dir))

  bench_yml_filename = '{}/docker-compose.yml'.format(config['WDIR'])
  shutil.copy(config['BASE_YML'], bench_yml_filename)

  bench_net = '{}_net'.format(config['TEST_NAME'])
  config['runtime_network'] = bench_net

  bench_yml_data = yml_load(bench_yml_filename)
  if 'version' in bench_yml_data:
    del bench_yml_data['version']
  yml_replace_network(bench_yml_data, bench_net)

  #Remove the video containers.
  cam_calib_svcs = yml_find_container_by_command(bench_yml_data, 'camcalibration')
  for svc in cam_calib_svcs:
    yml_remove_service(bench_yml_data, svc)
  video_svcs     = yml_find_container_by_command(bench_yml_data, 'percebro')
  for svc in video_svcs:
    yml_remove_service(bench_yml_data, svc)

  scene_controller_svcs = yml_find_container_by_command(bench_yml_data, 'controller')
  for svc in scene_controller_svcs:
    yml_remove_service(bench_yml_data, svc)

  db_svcs = yml_find_container_by_command(bench_yml_data, 'database')
  for svc in db_svcs:
    bench_yml_data['services'][svc]['command'] = bench_yml_data['services'][svc]['command'].replace('--preloadexample', '')
    bench_yml_data['services'][svc]['volumes'] = ['./:/workspace']

  web_svcs = yml_find_container_by_command(bench_yml_data, 'webserver')
  for svc in web_svcs:
    bench_yml_data['services'][svc]['volumes'] = ['./${DBROOT}/media:/workspace/media']

  yml_save(bench_yml_data, bench_yml_filename)

  config['DOCKER_OPTS'] = '--project-directory {} --file {} --progress quiet'.format(os.getcwd(), bench_yml_filename)

  return config


def benchmark_system_start(test_config):

  up_ok = utils_update_docker( test_config['SUPASS'], '{}/{}'.format(test_config['WDIR'],test_config['DBROOT']), test_config['DOCKER_OPTS'] )

  if up_ok:
    return utils_system_wait()

  return False

def benchmark_system_stop(test_config):

  up_command = 'docker compose '
  up_command += test_config['DOCKER_OPTS']
  up_command += ' down'
  bring_up_command = up_command.split(' ')
  
  return utils_run_command( bring_up_command )

def benchmark_system_log(test_config, label):
  return  

def build_args():
  args = ArgumentParser()
  args.add_argument('--config', required=True, help='Benchmarking configuration to use')
  return args

