# geo_target_positioning
Repository for Direct Geolocation methods for autonomously identified targets

# Septentrio go X5 Eval Kit Documentation
Septentrio receiver Username: SUAVGEO
Septentrio receiver Password: SUAVGEO

Septentrio go mosaic x5 IP address of USB: 19216831

All cmds can be done in the RxControls Expert terminal


Reciever is currently set to 'UAV' dynmanic configuration with 'high' smoothing, can be verified using 'getReceiverDynamics' cmd. 

Receiver dynamic configuration can be set using 'setReceiverDynamics' cmd.
//srd, High, UAV

Internal logging cmds:
  setGlobalFileNamingOptions, off
  setFileNaming, DSK1, Incremental
  setFileNaming, DSK1, , "septentriotroublesho"


when event is received, receiver sends event block of logs over com 2

cmd: setSBFOutput, Stream2, COM2, +Event, OnChange

setup ardupilot 
setup pi 
setup smartnet corrections (can we use ardupilot ntrip casting with orange cube?)
setup electronics to communicate with eachother

# raspberry pi ssh connection
ssh suav@10.13.41.148
10.13.39.176
password: suavsuav