#!/usr/bin/env python

def process_csv_file( fname, results=[] ):
  lineNum = 0
  fileHeaders = []
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
        runParams['data'] = {}
        for r in results:
          runParams['data'][r] = 0
        for d in lineData:
          d = d.rstrip().lstrip().rstrip('\n').lstrip('\n')
          if len(d):

            colName = fileHeaders[col]
            if colName not in results:
              if col >= len(fileHeaders):
                print( "Unknown col {} in {} (known {}".format( col, lineData, fileHeaders ) )
                break

              runParams[colName] = d
              
              if d not in fileData[colName]:
                fileData[colName].append(d)
            else:
              runParams['data'][colName] = d
          
          col+=1
        runResults.append( runParams )
      line = fd.readline()
      lineNum += 1
    fileData['results'] = runResults
    fileData['headers'] = fileHeaders
  return fileData
