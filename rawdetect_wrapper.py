#!/usr/bin/env python3

from sscape.detector import Detector
from sscape.scenescape import scenescape
from argparse import ArgumentParser
import cv2
import time
import math
import os
import re
from subprocess import Popen, PIPE

def build_args():
  args = ArgumentParser()
  args.add_argument( '--model', default='retail' )
  args.add_argument( '--input', required=True )
  args.add_argument( '--preprocess', action='store_true' )
  args.add_argument( '--frames', type=int )
  args.add_argument( '--max_store_frames', type=int, default=500 )
  args.add_argument( '--cores', type=int, default=4 )
  return args


def process_run( output ):
  run_time = 0
  fps = 0
  latency = 0
  stddev = 0

  print( len(output))
  output_lines = output.split('\n')
  for line in output_lines:

    if 'done' in line:
      continue

    match_string = '([\d]+) dets ([\d]+) frames in ([\d.]+)s : FPS ([\d.]+) Latency ([\d.]+)ms ([\d.]+)stddev.*'
    match_result = re.match( match_string, line )
    if match_result:
      run_time = match_result.group(1)
      dets = match_result.group(2)
      run_time = match_result.group(3)
      fps = match_result.group(4)
      latency = match_result.group(5)
      stddev = match_result.group(6)
      break
  return run_time, fps, latency, stddev

def run_test( args, frames, ncores ):
  basepath = '{}/rawdetect.py'.format(os.path.dirname(os.path.realpath(__file__)))
  test_args = [basepath, '--input', args.input ]
  if args.model:
    test_args.extend( ['--model', str(args.model)] )
  if args.preprocess:
    test_args.append( '--preprocess' )
  if args.frames:
    test_args.extend( ['--frames', str(frames)] )
  if args.max_store_frames:
    test_args.extend( ['--max_store_frames', str(args.max_store_frames)] )
  test_args.extend( ['--cores', str(ncores)] )
  process_test = Popen( test_args, text=True, stdout=PIPE )
  out = process_test.stdout.read()
  return out

def main():
  args = build_args().parse_args()
  initial_num_frames = args.frames / 10
  if initial_num_frames < 200:
    initial_num_frames = 200
  if initial_num_frames > 1000:
    initial_num_frames = 1000
  test_output = run_test( args, initial_num_frames, 1 )
  run_time, fps_single, latency, stddev = process_run( test_output )
  print( "FPS at ", 1, "cores:", fps_single )
  test_output = run_test( args, args.frames, args.cores )
  run_time, fps, latency, stddev = process_run( test_output )
  print( "FPS at ", args.cores, "cores:", fps )
  eff = 100 * float(fps) / (args.cores * float(fps_single))
  print( "Efficiency at ", eff, "%" )
  return 0

if __name__ == '__main__':
  exit( main() or 0 )
