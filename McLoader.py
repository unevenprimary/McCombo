from signal import signal, SIGINT
import requests
import random
import time
import sys
import os


data_dir = 'data'
dirs = ['names', 'emails', 'numbers'] #, 'proxies']
url = 'https://mcdonaldsapp.gr/maestro/data.php'
str_succ = 'Μπήκες επιτυχώς στην κλήρωση'
str_fail = 'Έχεις ήδη λάβει μέρος στην κλήρωση.'
patterns = [ bytes(s, 'utf-8') for s in (str_succ, str_fail) ]


class ResponseError(Exception):
    """Base class for response exceptions."""
    pass

class UnknownResponse(ResponseError):
    """Raised when an uncategorised response is recieved.

    Attributes:
        timestamp -- local time on recieving the response
        name -- name used to generate request
        email -- email used to generate request
        phone -- phone used to generate request
        response -- the response recieved
        message -- explanation of why the response is not processed as usual
    """

    def __init__(self, timestamp, name, email, phone, response, message=''):
        self.timestamp = timestamp
        self.name = name
        self.email = email
        self.phone = phone
        self.response = response
        self.message = message
        if not self.message:
            self.message = 'Response is unrecognised!'
        fname = strip_timestamp(timestamp) + '_resp.html'
        with open(fname, 'wb+') as resp_file:
            for line in response:
                resp_file.write(line)
        print(f'Response saved as "{fname}"')

class StatusHolder():
    def __init__(self, init_status=None, exiting=False):
        self.update(init_status)
        self.exiting = exiting

    def __getitem__(self, key):
        return self.status[key]

    def __repr__(self):
        return self.status

    def update(self, new_status):
        self.timestamp = time.ctime(time.time())
        self.status = str(new_status)

    def exit(self):
        self.exiting = True

def ring_the_bell():
    sys.stdout.write('\a')
    sys.stdout.flush()

def strip_timestamp(timestamp):
    r = timestamp.replace(' ', '_').replace(':', '_')
    return r

def update_file(line_count, path_main, path_misc):
    if not line_count:
        return
    name_main = path_main.split('\\')[-1]
    path_temp = path_main + '.tmp'
    with open(path_main, 'r', encoding='utf-8') as file_main:
        with open(path_temp, 'w+', encoding='utf-8') as file_temp:
            with open(path_misc, 'a+', encoding='utf-8') as file_misc:
                for i in range(line_count):
                    line = file_main.readline()
                    file_misc.write(line)
                leftover = file_main.read()
                file_temp.write(leftover)
    os.system('del {}'.format(path_main))
    os.system('ren {} {}'.format(path_temp, name_main))
    return


def main(data_dir, dirs, url, patterns):
    STATUS = StatusHolder('INITIAL')
    
    def cleanup(count, rfiles, dirs, paths):
        for f in rfiles.values():
                f.close()
        for i in range(len(dirs)):
                update_file(count, paths[0][i], paths[1][i])
                
    def handler(signal_received, frame):
        print('Interrupted by Ctrl+C. Cleaning up...')
        STATUS.exit()
    
    signal(SIGINT, handler)
    fnames = [ dirs, [f'{d}_used' for d in dirs] ]
    paths = [['{0}\\{1}\\{2}.txt'.format(data_dir, d.split('_')[0], d) \
              for d in fnames[i]]for i in (0,1)]
    rfiles = dict([[fnames[0][i], open(paths[0][i], 'r', encoding='utf-8')] \
                   for i in range(len(paths[0]))])
    uagents = []
    with open(f'{data_dir}\\uagents.txt') as u:
        for line in u:
            uagents.append(line[:-1])

    STATUS = StatusHolder('FIRSTLP')
    count = 0
    while 1:
        if STATUS.exiting:
            cleanup(count, rfiles, dirs, paths)
            input('Program exited, press <ENTER>')
            sys.exit(0)
        time.sleep(0.4)
        STATUS.update('READING')
        try:
            name = rfiles['names'].readline()[:-1]
            email = rfiles['emails'].readline()[:-1]
            phone = rfiles['numbers'].readline()[:-1]
            #proxy = rfiles['proxies'].readline()
            uagent = random.choice(uagents)
            
            proxies = {}

            data = {'name':         name,
                    'email':        email,
                    'confirmemail': email,
                    'phone':        phone,
                    'optin1':       '1',
                    'optin2':       '1'}

            headers = {'Host':       'mcdonaldsapp.gr',
                       'User-agent': uagent,
                       'Origin':     'https://mcdonaldsapp.gr'}
            STATUS.update('REQUEST')
            response = requests.post(url, data=data, headers=headers)
            STATUS.update('PROCESS')
            if patterns[0] in response.content:
                STATUS.update('SUCCESS')
            elif patterns[1] in response.content:
                STATUS.update('SKIPPIN')
            else:
                raise UnknownResponse(STATUS.timestamp, \
                                      name, email, phone, response)
            
        except Exception as err:
            STATUS.update(f'FATAL ON {STATUS}')
            print(f'FATAL FALURE: {err}')
            print('Aborting execution!\n')
            ring_the_bell()
            STATUS.exit()
            '''
            a = ''
            while (a != 'y') and (a != 'n'):
                a = str(input('Abort execution? (Y/N) ')).lower()
            if a == 'y':
                STATUS.update(STATUS, exiting=True)
                break
            else:
                continue
            '''

        finally:
            stat_string = f'{STATUS}: {name}, {email}, {phone}'
            print(stat_string)
            with open('stats.txt', 'a+', encoding='utf-8') as statfile:
                timestamp = STATUS.timestamp
                statfile.write(f'{timestamp} | {stat_string}\n')
            if STATUS[:5] != 'FATAL':
                count += 1

if __name__ == '__main__':
    main(data_dir, dirs, url, patterns)
