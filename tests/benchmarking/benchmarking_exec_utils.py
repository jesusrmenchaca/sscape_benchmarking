
import os
import shutil
import time
from subprocess import Popen, PIPE, run

def utils_clean_directory(path):
  if os.path.exists(path):
    shutil.rmtree(path)
  os.mkdir(path)
  return

def utils_check_config(cfg, attribute):
  if not attribute in cfg or cfg[attribute] is None:
    return False
  return True

def utils_run_command(cmd):
  process = Popen(cmd)
  process.wait()
  #print(process.stdout)
  return process.returncode == 0

def utils_find_container_base_name(container):
  cmd = f"docker ps | grep {container} | awk '{{print $NF}}' | sed -e 's/{container}/ /g'"
  process = run(cmd, shell=True, stdout=PIPE, text=True)
  base_name = process.stdout.strip().split(' ')
  return base_name

def utils_find_container_system_name(container):
  cmd = f"docker ps | grep {container} | awk '{{print $NF}}'"
  process = run(cmd, shell=True, stdout=PIPE, text=True)
  base_name = process.stdout.strip().split(' ')
  return base_name

def utils_find_network_name(network_base_name):
  cmd = f"docker network list | grep {network_base_name} | awk '{{print $2}}'"
  process = run(cmd, shell=True, stdout=PIPE, text=True)
  return process.stdout.strip()

def utils_update_docker( supass, dbroot, docker_opts ):
  os.environ['SUPASS'] = supass
  os.environ['DBROOT'] = dbroot
  up_command = 'docker compose '
  up_command += docker_opts
  up_command += ' up -d'
  up_command += ' --remove-orphans'
  bring_up_command = up_command.split(' ')

  return utils_run_command( bring_up_command )

def utils_run_sscape_cmdline( network_name, cmd ):
  sscape_cmd = f'docker/scenescape-start --network {network_name} {cmd}'
  sscape_cmd_split = sscape_cmd.split(' ')
  return utils_run_command( sscape_cmd_split )

def utils_log_container( container_name, filename ):
  cmd = f'docker logs {container_name}'
  with open(filename,'w') as fd:
    process = run(cmd, shell=True, stdout=PIPE, text=True)
    fd.write(process.stdout)
  return

def utils_wait_container(container, search_string=None, timeout=None):
  bare_cmd = f'wait_for_container {container}'
  if search_string:
    bare_cmd += f' {search_string}'
    if timeout:
      bare_cmd += f' {timeout}'
  wait_bash_cmd = f'source tests/test_utils.sh ; {bare_cmd}'

  wait_cmd = ['bash', '-c', wait_bash_cmd]
  return utils_run_command(wait_cmd) 

def utils_system_wait():
  # Wait 3 secs
  time.sleep(3)
  # Then wait for pgserver, web, etc
  base_name = utils_find_container_base_name('ntpserv')
  #print("Base name", base_name)
  if not utils_wait_container( '{}{}{}'.format(base_name[0], 'pgserver', base_name[1]), "'Container is ready'", 120):
    print( "Failed waiting for pgserver!" )
    return False
  if not utils_wait_container( '{}{}{}'.format(base_name[0], 'web', base_name[1])):
    print( "Failed waiting for web!" )
    return False
  return True
