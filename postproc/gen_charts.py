#!/usr/bin/env python3

import pygal
import re
from argparse import ArgumentParser

from pygal.style import Style
import random


def build_args():
  args = ArgumentParser()
  args.add_argument('--input', action='append', required=True)
  return args

all_colors=[]#('#ff0000', '#00ff00', '#0000ff')

def fill_colors(num_colors):
  global all_colors

  perm = (num_colors) #int(all_colors / 3)
  delta = int(255. / perm)
  for c1 in range(perm+1):
    for c2 in range(perm+1):
      for c3 in range(perm+1):
        color = (c1*delta, c2*delta, c3*delta)
        if (c1 == 0 and c2 == 0 and c3 == 0) \
          or (c1 == perm and c2 == perm and c3 == perm):
          continue
        all_colors.append(color)
  random.shuffle(all_colors)
  #print('{} - {}'.format(len(all_colors),all_colors))
  return
    
def get_color_str(color):
  final_str = '#'
  for c in color:
    x = hex(c).split('x')[1]
    if len(x) == 1:
      x = '0{}'.format(x)
    final_str += x
  return final_str

def gen_graph_simple( graph_name, graph_data, base, unit, fname ):
  global all_colors
  num_columns = len(graph_data)
  colors_str = []
  colors = all_colors[ :num_columns ]
  #colors = all_colors[ len(all_colors) : len(all_colors) - num_columns : -1 ]
  for c in colors:
    colors_str.append(get_color_str(c))

  print(colors_str)
  mystyle = Style(
    colors=colors_str,
    font_family='Helvetica',
    background='transparent',
    label_font_size=14 )

  c = pygal.Bar(
    title=graph_name,
    style=mystyle,
    y_title=unit,
    width=400,
    x_label_rotation=270 )

  for col in graph_data:
    name = col
    if col == 'total':
      continue
    val = graph_data[col]['time']
    if base is not None:
      #if base == 'total':
      #  val_rel = round(100*val / graph_data['total']['time'])
      #elif base == 'calls':
      if base == 'calls':
        val_rel = 1000*val / graph_data['total']['calls']
        #print('Base is {} : val {}'.format(base, graph_data['total']['calls']))
        #print('col is {} : val {} -> {}'.format(name, graph_data[col]['time'], val_rel))
      elif base == 'time':
        val_rel = 100*val / graph_data['total']['time']
      else:
        #print('Base is {} : val {}'.format(base, graph_data[col]))
        #print('col is {} : val {}'.format(name, graph_data[col]['time']))
        #print('Base is {} : val {}'.format(base, graph_data[col][base]))
        val_rel = val / graph_data[col][base]
      c.add( name, [val_rel] )
    else:
      c.add( name, [val] )

  #c.x_labels = [unit]

  c.render_to_file(fname)
  return

def gen_graph_full( graph_name, graph_data, base, labels, fname ):
  global all_colors
  num_columns = 0
  for idx in graph_data:
    num_columns += 1
  colors_str = []
  colors = all_colors[ :num_columns ]
  for c in colors:
    colors_str.append(get_color_str(c))

  print(colors_str)
  mystyle = Style(
    colors=colors_str,
    font_family='Helvetica',
    background='transparent',
    label_font_size=14 )

  c = pygal.Bar(
    title=graph_name,
    style=mystyle,
    y_title=labels,
    width=800,
    x_label_rotation=270 )

  cam_id = 1
  for idx in graph_data:
    for col in idx:
      if col == 'run':
        name = '{}_{}'.format(col, cam_id)
        cam_id += 1
        val = idx[col]['time']
        if base is not None:
          if base == 'calls':
            #val_rel = round(1000*val / idx['run']['time'])
            #val_rel = round(100*val / idx['total']['time'])
            val_rel = 1000*val / idx[col][base]
          else:
            val_rel = val / idx[col][base]
          c.add( name, [val_rel] )
        else:
          c.add( name, [val] )

  #c.x_labels = labels

  c.render_to_file(fname)
  return

def process_file(fname, base):
  tracker_info = {}
  with open(fname) as fd:
    num_calls = 0
    while True:
      line = fd.readline()
      if not line:
        break
      line = line.rstrip()
      if line.startswith('PERF'):
        #tracker_str = line.split(':').split(' ').split(',')
        tracker_str = re.split(r':| |,', line)
        print(tracker_str)
        if 'Tracker' in line:
          tracker_type = tracker_str[-1]

          if tracker_type not in tracker_info:
            tracker_info[tracker_type] = {}
            tracker_info[tracker_type]['total'] = {}
        if 'Calls' in line:
          fn_name = tracker_str[2]

          if not fn_name in tracker_info[tracker_type]:
            tracker_info[tracker_type][fn_name] = {}
            tracker_info[tracker_type][fn_name]['calls'] = 0
            tracker_info[tracker_type][fn_name]['time'] = 0
            tracker_info[tracker_type][fn_name]['per_msg'] = 0
          tracker_info[tracker_type][fn_name]['calls'] = int(tracker_str[6])
          tracker_info[tracker_type][fn_name]['time'] = float(tracker_str[10])
          if fn_name == base:
            num_calls = tracker_info[tracker_type][fn_name]['calls']
            tracker_info[tracker_type]['total']['calls'] = num_calls
            tracker_info[tracker_type]['total']['time'] = tracker_info[tracker_type][fn_name]['time']
            tracker_info[tracker_type]['total']['per_msg'] = tracker_info[tracker_type][fn_name]['time'] / tracker_info[tracker_type]['total']['calls']
          if tracker_info[tracker_type][fn_name]['calls'] == 0:
            tracker_info[tracker_type][fn_name]['calls'] = num_calls
          if tracker_info[tracker_type][fn_name]['calls'] > 0:
            tracker_info[tracker_type][fn_name]['per_msg'] = tracker_info[tracker_type][fn_name]['time'] / tracker_info[tracker_type][fn_name]['calls']
  for p in tracker_info:
    print('Tracker {}'.format(p))
    print( tracker_info[p] )
    for fn in tracker_info[p]:
      print(tracker_info[p][fn])
      print('fn {} time {:.2f} / calls {} avg {:.4f}'.format(fn, tracker_info[p][fn]['time'], tracker_info[p][fn]['calls'], tracker_info[p][fn]['per_msg'] ))
  return tracker_info

def main():
  args = build_args().parse_args()
  perf_info = []
  for inp in args.input:
    perf_info.append(process_file(inp, 'run'))
  #for every file
  #for idx in range(len(perf_info)):
  #  #for every tracker
  #  for t in perf_info[idx]:
  #    perf_info[idx][t]['total'] = {}
  #    #Count all fn calls
  #    for fn in perf_info[idx][t]:
  #      if fn == 'total':
  #        continue
  #      #And count all parameters
  #      for cat in perf_info[idx][t][fn]:
  #        perf_info[idx][t]['total'][cat] = 0
  #      break

  #for idx in range(len(perf_info)):
  #  for t in perf_info[idx]:
  #    for fn in perf_info[idx][t]:
  #      for cat in perf_info[idx][t][fn]:
  #        #if fn == 'total':
  #        #  continue
  #        if fn == 'run':
  #          perf_info[idx][t]['calls'] = perf_info[idx][t][fn]['calls']
  #        #perf_info[idx][t]['total'][cat] += perf_info[idx][t][fn][cat]

  #print(perf_info)
  fill_colors(2)

  for idx in range(len(perf_info)):
    print("File {}".format(idx))
    for t in perf_info[idx]:
      print("tracker {}".format(t))
      gen_graph_simple( 'Camera {} Tracker {}'.format(idx+1, t), perf_info[idx][t], 'calls', 'ms_per_msg', 'time_{}_{}.svg'.format(t,idx+1))
      gen_graph_simple( 'Camera {} Tracker {} (ms)'.format(idx+1, t), perf_info[idx][t], 'time', 'perc', 'perc_{}_{}.svg'.format(t,idx+1))

  perf_info_trackers = {}
  for idx in range(len(perf_info)):
    for t in perf_info[idx]:
      if not t in perf_info_trackers:
        perf_info_trackers[t] = []
      perf_info_trackers[t].append( perf_info[idx][t] )
  for t in perf_info_trackers:
    #print(perf_info_trackers)
    gen_graph_full( 'Tracker {}'.format(t), perf_info_trackers[t], 'calls', 'ms_per_msg', 'full_{}.svg'.format(t))
    #gen_graph_full( 'Tracker {}'.format(t), perf_info_trackers[t], 'calls', 'ms_per_msg', 'full_{}.svg'.format(t))
  return 0

if __name__ == '__main__':
  exit(main() or 0)
