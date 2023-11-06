#!/usr/bin/env python3

import pygal
import re
import random
import os

from datetime import date
from argparse import ArgumentParser
from pygal.style import Style
from gen_charts import gen_graph_simple, generate_all_charts, fill_colors
from process_csv import process_csv_file
from parse_config import parse_config, default_config

def build_args():
  args = ArgumentParser()
  args.add_argument('--date')
  args.add_argument('--version', required=True)
  args.add_argument('--host', action='append', required=True)
  args.add_argument('--outdir', required=True)
  args.add_argument('--datadir', default='.')
  args.add_argument('--config')
  args.add_argument('--output', default='report.tex')
  return args

def tex_insert_paragraph( f, p ):
  f.write( "\n\n" )
  f.write( p )
  f.write( "\n" )
  return

def tex_escape( string ):
  if type(string) == str:
    return string.replace( '_', '\_' )
  return string

num_figures = 0

def tex_insert_graphic( f, fname, run_type, run_name, run_system ):
  global num_figures
  f.write( "\\begin{figure}[hb]\n" )
  f.write( "\\centering\n" )
  f.write( "\\def\\svgwidth{\\columnwidth}\n" )
  f.write( "\\input{{{}.pdf_tex}}\n".format(fname.replace(".svg", "")) )
  fig_label = 'graph_{}'.format(num_figures)
  fig_caption = 'Performance for {} {}, system {}'.format( run_type, run_name, run_system )
  f.write( "\\caption{{{}}}\n".format(fig_caption) )
  f.write( "\\label{{fig:{}}}\n".format(fig_label) )
  f.write( "\\end{figure}\n" )
  num_figures += 1
  return fig_label

def tex_insert_table( f, tableData ):
  numColumns = len(tableData['columns'])
  numRows = len(tableData['rows'])
  if numColumns == 0 or numRows == 0:
    f.write( "empty table goes here \n" )
    return
  f.write( "\\begin{table}[!ht]\n" )
  f.write( "\\begin{center}\n" )
  f.write( "\\begin{tabularx}{\\textwidth}{|")
  for col in tableData['columns']:
    f.write( " C" )
  f.write( "|}\n" )
  # Write Header row
  for c in range( numColumns ):
    f.write( "{} ".format( tex_escape( tableData['columns'][c] ) ) )
    if c != numColumns - 1:
      f.write( "& " )
  f.write( "\\\\\n" )
  if tableData['header']:
    f.write( "\\hline\n" )
  # Write data rows
  for r in range( numRows ):
    for c in range( numColumns ):
      f.write( "{}".format( tex_escape( tableData['rows'][r][c] ) ) )
      if c != numColumns - 1:
        f.write( "& " )
    if r != numRows - 1:
      f.write( "\\\\" )
    f.write( "\n" )

  f.write( "\\end{tabularx}\n" )
  f.write( "\\end{center}\n" )
  f.write( "\\end{table}\n" )
  return

def tex_describe_host( f, hostData ):
  hostName = hostData['results'][0]['NAME']
  f.write( "\n" )
  tex_insert_paragraph( f, "Host information for {}\n".format(hostName) )
  tex_insert_paragraph( f, "{} has {} cores, running at {} MHz.\n".format( hostName, 
      hostData['results'][0]['CORES'], 
      hostData['results'][0]['FREQ'] ))
  if hostData['results'][0]['GPU'] != 0:
    f.write( "{} has the following GPU: {}\n".format( hostName, hostData['results'][0]['GPU'] ) )
  else:
    f.write( "{} does not have a GPU\n".format(hostName) )
  f.write( "\n" )
  
  return


def tex_experiment_inference( f, expData, resultColumns ):
  desiredColumns = ['DEVICE', 'NUM_CORES', 'INPUT', 'RESULTS']
  print(expData)
  for m in expData['MODEL']:
    f.write( "\\par\n" )
    f.write( "The following results were measured on model {}\n".format(m) )
    
    rows = 3
    columns = 5 #Model xyz: Device streams/Cores Resolution FPS latency
    tableData = {}
    headerData = []
    headerSet = False
    tableData['rows'] = []

    print("Model",m, "headerset", headerSet)
    for res in expData['results']:
      if m == res['MODEL']:
        columnData = []
        for desired in desiredColumns:
          if 'RESULTS' == desired:
            for resCol in resultColumns:
              columnData.append( res['data'][resCol] )
              if headerSet is False:
                headerData.append( resCol )
          else:
            columnData.append( res[desired] )
            if headerSet is False:
              headerData.append( desired )
        tableData['rows'].append(columnData)
        headerSet = True
    tableData['columns'] = headerData
    tableData['header'] = True
    g_label = tex_insert_graphic( f, expData['charts']['MODEL'][m], 'model', m, 'localhost' )
    f.write( "Refer to \\ref{{fig:{}}}\n".format(g_label) )
    tex_insert_table( f, tableData )
    print( "Done with model ", m )
  return

def tex_generate_header( f, config, date, version ):
  f.write( "\\documentclass{article}\n" )
  f.write( "\\usepackage{hyperref,graphicx,fancyhdr}\n" )
  # For breaking up cells
  f.write( "\\usepackage{tabularx,array}\n" )
  f.write( "\\usepackage{titlesec}\n" )
  f.write( "\\newcolumntype{C}{>{\\centering\\arraybackslash}X}\n" )
  f.write( "\\newcommand{\\sectionbreak}{\\clearpage}\n" )
  f.write( "\\pagestyle{fancy}\n" )

  f.write( "\\lhead{{\includegraphics[width=1cm]{{ {} }} }}\n".format(config['report']['lheader'] ))
  f.write( "\\rhead{{ {} }}\n".format(config['report']['rheader'] ))
  f.write( "\\cfoot{{ {} - {}}}\n".format(config['report']['footer'], version) )

  f.write( "\\begin{document}\n" )
  documentTitle = "This is a sample report for SceneScape, generated on {}, using version {}".format(
    date, version )
  tex_insert_paragraph( f, documentTitle )
  return

def tex_generate_appendix( f, config ):
  f.write( "\\appendix\n" )
  f.write( "\\section{Test descriptions}\n" )
  tableData = {}
  tableData['header'] = False
  tableData['columns'] = ['Test', 'Description']
  tableData['rows'] = []
  for test in config:
    if type(config[test]) == dict:
      if 'description' in config[test]:
        tableData['rows'].append( [ test, config[test]['description'] ] )
  tex_insert_table( f, tableData )
  f.write( "\n" )
  return

def tex_hosts_combined_report( f, config ):
  f.write("\\section{ Host comparison }\n" )
  f.write( "\n EMPTY \n" )
  return

def tex_host_description( f, hostData ):
  f.write("\\section{ Hosts description }\n" )
  tex_describe_host( f, hostData )
  return

def tex_host_report( f, config, hostData, experimentData ):
  f.write("\\section{{ Execution on {} }}\n".format( hostData['results'][0]['NAME'] ) )
  tex_insert_paragraph( f, "The following tests were performed on host {}:\n\n".format(hostData['results'][0]['NAME']) )

  tableData = {}
  tableData['header'] = False
  tableData['columns'] = ['Test', 'Description']
  tableData['rows'] = []
  for exp in experimentData:
    tableData['rows'].append([ exp, config[exp]['short_desc'] ])

  tex_insert_table( f, tableData )

  for exp in experimentData:
    if exp == 'inference':
      tex_experiment_inference( f, experimentData[exp], config[exp]['results'] )
    else:
      print( 'Unknown exp {}!!!!!'.format(exp) )

  
  tex_insert_paragraph( f, '' )
  f.write( "\\url{{ {} }}\n".format( config['report']['URL'] ) )
  return


def main():
  args = build_args().parse_args()
  
  if args.config is not None:
    config = parse_config( args.config )
  else:
    config = default_config
  if args.date is not None:
    report_date = args.date
  else:
    report_date = '{}'.format(date.today())

  target_dir = os.path.abspath(args.outdir)
  if not os.path.exists(target_dir):
    os.mkdir(target_dir)
  elif not os.path.isdir(target_dir):
    print(f"Error, {target_dir} exists and is not a directory")
    return 1
  
  experiments = ['inference', 'scene']
  fill_colors( len( args.host ) )
  with open("report.tex", 'w') as f:
    allHosts = []
    tex_generate_header(f, config, report_date, args.version)
    for inp in args.host:
      hostFile = "{}/desc_{}.csv".format(args.datadir,inp)
      hostData = process_csv_file(hostFile)
      print(hostData)

      experimentData = {}
      for exp in config['experiments']:
        fname = "{}/{}/results_{}.csv".format(args.datadir,inp,exp)
        if os.path.exists(fname):
          fData = process_csv_file(fname, config[exp]['results'])
          experimentData[exp] = fData
          
          print("File ",inp, "Output:", fData)
          generate_all_charts( target_dir, fData )
    
      tex_host_report(f, config, hostData, experimentData)
      allHosts.append(hostData)

    for host in allHosts:
      tex_host_description( f, host )

    tex_hosts_combined_report(f, config)

    tex_generate_appendix( f, config )
    f.write( "\\end{document}\n" )
  print( "Done" )
  return 0

if __name__ == '__main__':
  exit(main() or 0)
