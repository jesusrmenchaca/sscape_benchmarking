#!/usr/bin/env python3

import pygal
import re
import random
import os
from argparse import ArgumentParser
from pygal.style import Style
from process_csv import process_csv_file


def build_args():
  args = ArgumentParser()
  args.add_argument('--input', action='append', required=True)
  args.add_argument('--outdir', required=True)
  return args

all_colors=[]

def fill_colors(num_variations):
  global all_colors

  perm = (num_variations) #int(all_colors / 3)
  delta = int(255. / perm)
  for c1 in range(perm+1):
    for c2 in range(perm+1):
      for c3 in range(perm+1):
        color = (c1*delta, c2*delta, c3*delta)
        if (c1 == 0 and c2 == 0 and c3 == 0) \
          or (c1 == perm and c2 == perm and c3 == perm):
          continue
        all_colors.append(color)
  #random.shuffle(all_colors)
  return
    
def get_color_str(color):
  final_str = '#'
  for c in color:
    x = hex(c).split('x')[1]
    if len(x) == 1:
      x = '0{}'.format(x)
    final_str += x
  return final_str


def gen_graph_simple( graph_name, unit, graph_data, fname, color_offset=0 ):
  global all_colors
  num_columns = len(graph_data) + color_offset
  colors_str = []
  colors = all_colors[ color_offset:num_columns ]
  #colors = all_colors[ len(all_colors) : len(all_colors) - num_columns : -1 ]
  for c in colors:
    colors_str.append(get_color_str(c))

  print(colors_str)
  mystyle = Style(
    colors=colors_str,
    font_family='Helvetica',
    background='white',
    plot_background='#E0E0E0',
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
    val = graph_data[col]
    c.add( name, [val] )

  c.render_to_file(fname)
  return


def generate_all_charts( outdir, fileData ):
  for col in fileData['headers']:
    print( "Known {} : {}".format( col, fileData[col] ) )

  fileData['charts'] = {}
  for entry in ['MODEL', 'NUM_CORES']:
    fileData['charts'][entry] = {}

  for m in fileData['MODEL']:
    #fileData['MODEL'][m]'charts'] = []
    graph_data = {}

    for c in fileData['NUM_CORES']:
      
      for d in fileData['results']:
        if d['MODEL'] == m and d['NUM_CORES'] == c:
          graph_data[c] = float(d['data']['FPS'])

    fname = '{}/model_{}.svg'.format(outdir, m)
    gen_graph_simple( 'FPS per CORES - model {}'.format(m), 'fps', graph_data, fname )

    #fileData['MODEL'][m]['charts' = fname
    fileData['charts']['MODEL'][m] = fname


  for c in fileData['NUM_CORES']:
    #fileData['NUM_CORES'][c]['charts'] = {}
    graph_data = {}

    for m in fileData['MODEL']:
      
      for d in fileData['results']:
        if d['MODEL'] == m and d['NUM_CORES'] == c:
          print("Adding d {}".format(d))
          graph_data[m] = float(d['data']['FPS'])

    fname = '{}/by_{}_cores.svg'.format(outdir, c)
    gen_graph_simple( 'FPS per MODEL - CORES {}'.format(c), 'fps', graph_data, fname )

    #fileData['NUM_CORES'][c]['chart'] =  fname
    fileData['charts']['NUM_CORES'][c] = fname
  return



def main():
  args = build_args().parse_args()
  fill_colors(16)
  perf_info = []
  
  target_dir = os.path.abspath(args.outdir)
  if not os.path.exists(target_dir):
    os.mkdir(target_dir)
  elif not os.path.isdir(target_dir):
    print(f"Error, {target_dir} exists and is not a directory")
    return 1
  
  for inp in args.input:
    fData = process_csv_file(inp, ["FPS", "LATENCY"])
    generate_all_charts( target_dir, fData )
    
  return 0

if __name__ == '__main__':
  exit(main() or 0)
