from pybricks.parameters import Button, Color, Direction, Port, Side, Stop
from pupremote import PUPRemoteHub
from pybricks.tools import wait, StopWatch

p=PUPRemoteHub(Port.B)
p.add_command('hl',from_hub_fmt="b", to_hub_fmt="hhhhB")
p.add_command('msg',"repr","repr")
p.add_command('num',from_hub_fmt="3b",to_hub_fmt="3b")
p.add_command('sdata',from_hub_fmt="16B", to_hub_fmt="16B")
p.add_command('ldata',from_hub_fmt="32B", to_hub_fmt="32B")

INIT = -1
COLOR_DETECT = 4

print(p.call('num',1,2,-45))
print(p.call('num',5,-6,42))
# print(p.call('msg',"hello"))

print(p.call('hl',COLOR_DETECT))
print(p.call('hl'))
while 1:
    print(p.call('hl'))