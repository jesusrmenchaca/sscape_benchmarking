#!/usr/bin/env python3


from sscape.detector import Detector
from sscape.scenescape import scenescape
from argparse import ArgumentParser
import cv2
import time
import math

def build_args():
  args = ArgumentParser()
  args.add_argument( '--model', default='retail' )
  args.add_argument( '--input', required=True )
  args.add_argument( '--preprocess', action='store_true' )
  args.add_argument( '--frames', type=int )
  args.add_argument( '--max_store_frames', type=int, default=500 )
  args.add_argument( '--cores', type=int, default=4 )
  return args

def sleep_needed( prevtime, curtime, frametime ):
  delta = (curtime - prevtime)*1000
  if delta <= 1:
    return
  else:
    time.sleep( (frametime - delta)/1000 )
  return



latencies = []
start_time = time.time()

def postprocess_store( store, frameIdx ):
  now = time.time() - start_time
  frame_time = now - store[frameIdx][1]
  #print( "fid {} took {:.3f} ({:.3f} to {:.3f}) -> {:.3f}".format(frameIdx, frame_time, store[frameIdx][1], now, 1/frame_time) )
  latencies.append( frame_time )
  return

def postprocess_latencies( ):
  global latencies
  avg = 0
  stddev = 0
  for l in latencies:
    avg += l*1000

  #print( "Total latency {:.3f}ms".format(avg) )
  avg /= len(latencies)

  for l in latencies:
    tmp = (l*1000 - avg)
    stddev += tmp*tmp
  stddev /= len(latencies)
  stddev = math.sqrt( stddev )

  return avg, stddev

def main():
  args = build_args().parse_args()
  
  vid = cv2.VideoCapture( args.input )
  if vid is None or vid.isOpened() == False:
    print( "Failed opening", args.input )
    return 1

  read_frames = args.max_store_frames
  if args.frames < read_frames:
    read_frames = args.frames
  if read_frames < (args.cores + 2):
    read_frames = args.cores + 2


  fps = vid.get(cv2.CAP_PROP_FPS)
  frametime = (1000 / fps)
  cores = args.cores

  async_mode = True if cores > 0 else False
  det = Detector(asynchronous=async_mode, distributed=scenescape.Distributed.NONE)
  det.setParameters( args.model, 'CPU', None, 0.5, cores )
  done = False
  frameNum = 0

  output = []

  frame_store = []

  if read_frames != 0:
    frameNum = 0
    while frameNum < read_frames:
      ret, frame = vid.read()
      if ret == False:
        if frameNum < read_frames:
          vid.release()
          vid = cv2.VideoCapture( args.input )
        else:
          done = True
      else:
        frame_store.append( [frame, frameNum, 0] )
        frameNum += 1

  frameNum = 0

  starttime = time.time()
  prevtime = starttime
  pushed_dets = 0
  num_detections = 0

  while done == False:
    if not args.preprocess:
      curtime = time.time()
      sleep_needed( prevtime, curtime, frametime )
      prevtime = time.time()
      now = prevtime - start_time

    if read_frames == 0:
      ret, frame = vid.read()
      if ret == False:
        if args.frames and frameNum < args.frames:
          vid.release()
          vid = cv2.VideoCapture( args.input )
        else:
          done = True
      else:
        frame_store.append( [frame, frameNum, 0] )
    else:
      idx = frameNum % read_frames
      frame = frame_store[idx][0]
      #idx = (idx+1) % read_frames

    if frame is not None:
      idata = scenescape.IAData([frame], id=frameNum)
      #print( "{} pushing at {:.3f}".format(frameNum, time.time() - start_time ))
      detections = det.detect(idata)
      frame_store[idx][1] = time.time() - start_time
      #print( "{} pushed at {:.3f}".format(frameNum, time.time() - start_time ))
      pushed_dets+=1

      if detections is not None:
        output.append(detections)
        postprocess_store( frame_store, detections.id % read_frames )
        pushed_dets-=1

      detections = det.detect(None)
      while detections is not None:
        postprocess_store( frame_store, detections.id % read_frames )
        output.append(detections)
        detections = det.detect(None)
        pushed_dets-=1

      frameNum += 1
      if args.frames and frameNum == args.frames:
        done = True
      elif frameNum % 100 == 0:
        print( "{} done".format(frameNum) )

  #frameNum -= pushed_dets
  while pushed_dets > 0:
    detections = det.detect(None)
    if detections is not None:
      pushed_dets -= 1
      postprocess_store( frame_store, detections.id % read_frames )
    time.sleep(0.001)
  endtime = time.time()

  for det in output:
    det_data = det.data
    if len(det_data):
      num_detections += len(det_data)

  deltatime = endtime - starttime
  rate = frameNum / deltatime

  avg, stddev = postprocess_latencies()
  maxfps = 1000/avg
  print( "{} dets {} frames in {:.3f}s : FPS {:.3f} Latency {:.3f}ms {:.3f}stddev (max {:.3f} per core)".format( 
          num_detections, frameNum, deltatime, rate, avg, stddev, maxfps)  )

  fpsdelta = 100*(rate) / (maxfps*cores)
  print( "Efficiency at {} cores: {:.2f}%".format( cores, fpsdelta ) )

  return 0

if __name__ == '__main__':
  exit(main() or 0)
