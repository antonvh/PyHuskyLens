#!python3

# Run this on a Mac or Linux machine to create/update 'SPIKEInstaller.py'
# Copy the contents of SPIKEInstaller.py into an empty SPIKE Prime project
# And run to install

import binascii, mpy_cross, time
import hashlib

SOURCE = 'pyhuskylens.py'
DESTINATION = 'pyhuskylens.mpy'
INSTALLER = 'SPIKEInstaller.py'
mpy_cross.run('-march=armv6', SOURCE,'-o', DESTINATION)

# Should be done in a second!
time.sleep(1)

uartremote=open(DESTINATION,'rb').read()
hash=hashlib.sha256(uartremote).hexdigest()
ur_b64=binascii.b2a_base64(uartremote)

spike_code=f"""import ubinascii, uos, machine,uhashlib
from ubinascii import hexlify
b64=\"\"\"{ur_b64.decode('utf-8')}\"\"\"

def calc_hash(b):
    return hexlify(uhashlib.sha256(b).digest()).decode()

# this is the hash of the compiled mpy
hash_gen='{hash}'

pyhuskylens=ubinascii.a2b_base64(b64)
hash_initial=calc_hash(pyhuskylens)

try: # remove any old versions of pyhuskylens library
    uos.remove('/projects/pyhuskylens.py')
    uos.remove('/projects/pyhuskylens.mpy')
except OSError:
    pass

print('writing pyhuskylens.mpy to folder /projects')
with open('/projects/pyhuskylens.mpy','wb') as f:
    f.write(pyhuskylens)
print('Finished writing pyhuskylens.mpy.')
print('Checking hash.')
pyhuskylens_check=open('/projects/pyhuskylens.mpy','rb').read()
hash_check=calc_hash(pyhuskylens_check)

print('Hash generated: ',hash_gen)
error=False
if hash_initial != hash_gen:
    print('Failed hash of base64 input : '+hash_initial)
    error=True
if hash_check != hash_gen:
    print('Failed hash of .mpy on SPIKE: '+hash_check)
    error=True

if not error:
    print('pyhuskylens library written succesfully. Resetting....')
    machine.reset()
else:
    print('Failure in pyhuskylens library!')

"""
with open(INSTALLER,'w') as f:
    f.write(spike_code)
