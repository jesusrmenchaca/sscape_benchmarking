
Setup:


Host fmdeviot-ip
     Hostname 198.175.75.91
     Port 22
     LocalForward 9880 localhost:8080
#     ProxyCommand nc --proxy-type socks5 --proxy proxy-us.intel.com:1080 %h %p
     ProxyCommand nc -X 5 -x proxy-us.intel.com:1080 %h %p


Host github.com
   ProxyCommand=corkscrew proxy-us.intel.com 911 %h %p


