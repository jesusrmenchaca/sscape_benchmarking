
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
#     ProxyCommand nc --proxy-type socks5 --proxy proxy-us.intel.com:1080 %h %p
     ProxyCommand nc -X 5 -x proxy-us.intel.com:1080 %h %p


Host github.com
   ProxyCommand=corkscrew proxy-us.intel.com 911 %h %p



Then clone the repos:
git clone git@github.com:intel-sandbox/intel-proxy-setup.git
git clone git@github.com:jesusrmenchaca/sscape_benchmarking.git
git clone git@github.com:intel-innersource/applications.ai.scene-intelligence.opensail.git

