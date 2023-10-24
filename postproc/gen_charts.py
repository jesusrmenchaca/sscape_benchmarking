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


def gen_graph_simple( graph_name, unit, graph_data, fname ):
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
    val = graph_data[col]
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

def process_file_csv( fname, results=[] ):
  lineNum = 0
  fileHeaders = []
  media = []
  fileData = {}
  runResults = [] 
  with open(fname) as fd:
    line = fd.readline()
    while line is not None and len(line) > 0 and lineNum < 10:
      if lineNum == 0:
        tmpFileHeaders = line.split(",")
        for h in tmpFileHeaders:
          h = h.rstrip().lstrip()
          fileHeaders.append(h)
          fileData[h] = []
        print(fileHeaders)
      else:
        col = 0
        lineData = line.split(",")
        if lineNum > 0 and lineNum < 4:
          print(lineData)
        runParams = {}
        runParams['results'] = {}
        for r in results:
          runParams['results'][r] = 0
        for d in lineData:
          d = d.rstrip().lstrip()
          if len(d):

            colName = fileHeaders[col]
            if colName not in results:
              if col >= len(fileHeaders):
                print( "Unknown col {} in {} (known {}".format( col, lineData, fileHeaders ) )
                break

              runParams[colName] = d
              #print( "Column ", col )
              #print( colName )
              
              if d not in fileData[colName]:
                fileData[colName].append(d)
            else:
              runParams['results'][colName] = d

          #if col == 0 and d not in media:
          #  media.append(d)
          #if col == 0 and lineNum == 1:
          #  print(d)
          
          col+=1
        runResults.append( runParams )
      line = fd.readline()
      lineNum += 1

  for col in fileHeaders:
    print( "Known {} : {}".format( col, fileData[col] ) )
  
  print( runResults )

  for m in fileData['MODEL']:
    graph_data = {}

    for c in fileData['NUM_CORES']:
      
      for d in runResults:
        if d['MODEL'] == m and d['NUM_CORES'] == c:
          print("Adding d {}".format(d))
          graph_data[c] = float(d['results']['FPS'])

    fname = 'model_{}.svg'.format(m)
    gen_graph_simple( 'FPS per CORES - model {}'.format(m), 'fps', graph_data, fname )


  for c in fileData['NUM_CORES']:
    graph_data = {}

    for m in fileData['MODEL']:
      
      for d in runResults:
        if d['MODEL'] == m and d['NUM_CORES'] == c:
          print("Adding d {}".format(d))
          graph_data[m] = float(d['results']['FPS'])

    fname = 'by_{}_cores.svg'.format(c)
    gen_graph_simple( 'FPS per MODEL - CORES {}'.format(c), 'fps', graph_data, fname )
    #gen_graph_simple( 'FPS per core', 'fps', graph_data, fname )
  return



def main():
  args = build_args().parse_args()
  fill_colors(16)
  perf_info = []
  for inp in args.input:
    process_file_csv(inp, ["FPS", "LATENCY"])
  return 0

if __name__ == '__main__':
  exit(main() or 0)
