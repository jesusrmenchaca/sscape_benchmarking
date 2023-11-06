#!/usr/bin/env python3

import json
import os


default_config = {
  'report' : {
                'lheader' : '',
                'rheader' : 'Intel',
                'footer' : 'SceneScape',
                'URL' : 'http://www.intel.com/scenescape'
             },
  'experiments' : ['inference', 'scene'],
  'inference': { 'results' : ['FPS', 'LATENCY'],
                 'columns' : ['DEVICE', 'NUM_CORES', 'INPUT', 'RESULTS'],
                 'report' : ['all'],
                 'short_desc': 'Inference performance test',
                'description' : 'The Inference performance test measures the framerate achieved by Percebro, while decoding and \
                                 running inference on the requested model. It requests NUM_CORES streams from OpenVINO, and \
                                 requests the specified DEVICE to run inference on.\n' },
  'scene' : {'results' : ['MPS', 'FELL_BEHIND'],
             'columns' : ['N_CAMERAS', 'RESULTS'],
             'report' : ['all'],
             'short_desc' : 'Scene controller performance test',
             'description' : 'The Scene performance test measures the time spent by the Scene Controller in processing every message. \
                              The test simulates n number of cameras sending detections, and measures the time spent in processing \
                              each message.\n' }
}


def parse_config( fname ):
  cfg = {}
  with open(fname) as f:
    f_data = json.load( f )
    cfg = f_data

  # sanitize,
  if not 'experiments' in cfg:
    cfg['experiments'] = {}

  
  return cfg
