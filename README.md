
Setup:

Run:
ssh-keygen -q -N '' -f ~/.ssh/id_rsa
mkdir -p jrmencha/builds
cd jrmencha/builds
sudo apt-get update && sudo apt-get install -y corkscrew

Then add the key to github/fmdeviot-ip
cat ~/.ssh/id_rsa.pub

and set this in ~/.ssh/config:
Host fmdeviot-ip
     Hostname 198.175.75.91
     Port 22
     LocalForward 9880 localhost:8080
     ProxyCommand nc -X 5 -x proxy-us.intel.com:1080 %h %p


Host github.com
   ProxyCommand=corkscrew proxy-us.intel.com 911 %h %p



Then clone the repos:
git clone git@github.com:intel-sandbox/intel-proxy-setup.git
git clone git@github.com:jesusrmenchaca/sscape_benchmarking.git
git clone git@github.com:intel-innersource/applications.ai.scene-intelligence.opensail.git



## Running the report
make sscape_benchmarking:
$ make -C postproc

put the report into report/data
$ mkdir -p report/data/<hostname>

Ensure a desc_<hostname>.csv file exists in report/data:
$ cat report/data/desc_sail3.csv

NAME,CORES,FREQ,GPU,BOGOMIPS
sail3,112,2700,0,5400

Put the aggregated report in:
$ ls report/data/sail3/result_inference.csv
$ ls report/data/sail3/result_scene.csv

Generate the report. (hostname and version info are needed)
$ postproc/run.sh <hostname> <version>

The report will be generated in report/report.pdf
