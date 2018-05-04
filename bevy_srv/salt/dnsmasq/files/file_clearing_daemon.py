#!/usr/bin/env python3
"""
Runs for a long time, looking for an http query from a recently initialized
computer. When it gets the packet, it tries to clear away the PXE boot configuration
for that computer, so that it will boot from its disk from then on.

It expects to receive html GET requests on pillar['pxe_clearing_port']
see the docstring of FileClearingRequestHandler for details.

WARNING: whenever this daemon is running, it will allow anyone to execute shell commands as ROOT.
There is no attempt to filter or authenticate commands.
It will shut itself down when it clears its internal queue of expected work,
or at the end of pillar value 'pxe_clearing_daemon_life_minutes',
or when it receives a 'GET /shutdown' message.

The job queue should be pre-loaded by 'GET /store' lines from the salt-master so that
it knows when to shut down.
"""
from __future__ import print_function
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, time, json, subprocess, urllib
from pathlib import Path

DAEMON_NAME = 'PXE_File_Clearing_Daemon'

try:  # retrieve our pillar to get settings
    jas = subprocess.check_output('sudo salt-call pillar.items --output=json', shell=True)
    pillar = json.loads(jas.decode('utf8'))['local']
except subprocess.CalledProcessError as e:
    raise ValueError('Error calling salt minion. Is salt-call available and master running?') from e

try:
    http_port_number = pillar['pxe_clearing_port']
    wait_time = pillar['pxe_clearing_daemon_life_minutes'] * 60  # seconds
    salt_managed_message = pillar['salt_managed_message']
except KeyError:
    raise ReferenceError('Expected values not found in pillar. Are you including manual_bevy_settings.sls?')

BOOT_FROM_DISK_CONFIG_TEXT = '''
# this file created by {}
default boot0
label boot0
  say Now booting from disk
  localboot 0
'''.format(DAEMON_NAME)


class StoppableHTTPServer(HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()


# HTTPRequestHandler class
# noinspection PySingleQuotedDocstring
class FileClearingRequestHandler(BaseHTTPRequestHandler):
    '''
    Handles the actual http GET requests.
    the query can be:
    Q: /ping
    the response will be
    R: 200 pong

    Q: /shutdown
    R: 200 Will shut down in a few seconds

    Q: /store?mac_addr=01-02-03-04-05-06&pxe_config_file=path/to/PXE/configuration&next_command=some%20shell%20script
        will be sent by the bevy_master server.
      action:  stores the query string in dictionary self.server.job_list to be executed later
        the pxe_config_file and next_command parameters may be repeated.
    R: 201

    Q: /execute?mac_addr=01-02-03-04-05-06[& optional commands]
        will be sent by the just-booted client computer
      action: retrieves data for mac_address
      This query should be sent by the client computer's hands-free install process
      by placing a command at the end of the preseed file (bevy_srv/salt/dnsmasq/files/hands_off.preseed)
      something like this...
    d-i preseed/late_command string in-target wget -q -O - http://{{ pillar['pxe_server_ip'] }}:{{ pillar['pxe_clearing_port'] }}/execute?mac_addr={{ config_mac }}
      Note: After processing by Salt, each target machine has its own preseed file with its own GET/execute command.
    R: 202
      The stored job_list commands have the present query string concatenated, and the
       the following is done *with root privilege*,
      1) any contents of a file named in 'pxe_config_file' will be replaced by BOOT_FROM_DISK_CONFIG_TEXT
           (but only if that file starts with 'salt_managed_message').
      2) any strings in any 'next_command' will be run as a shell script.
    '''

    # noinspection PyPep8Naming
    def do_GET(self):
        print(DAEMON_NAME, '-->', 'got request "{}"'.format(self.path), flush=True)
        work_is_done = False
        job_list = self.server.job_list

        if self.path == '/ping':
            self.send_response_only(200, 'pong')

        elif self.path.startswith('/shutdown'):
            self.send_response(200, 'Will shut down in a few seconds.')
            work_is_done = True
        else:
            args = self.path.strip().split('?')
            if args[0] == '/store':
                try:
                    # store the query string for use when the process completes
                    data = urllib.parse.parse_qs(args[1], keep_blank_values=True)
                    key = data['mac_addr'][0]
                    job_list[key] = args[1]
                except (KeyError, IndexError):
                    pass
                # Send response status code
                self.send_response(201)  # resource created
            elif args[0] == '/execute':
                # parse received query string
                data = urllib.parse.parse_qs(args[1])
                key = None
                try:
                    key = data['mac_addr'][0]  # extract MAC address
                    stored_qs = job_list.get(key, '')  # retrieve stored query string (if any)
                    combined_qs = (stored_qs + '&' if stored_qs else '') + args[1]
                    data = urllib.parse.parse_qs(combined_qs)
                    # do 'pxe_config_file' commands to change our BOOT configuration
                    config_files = data.get('pxe_config_file', [])
                    for config_file in config_files:
                        config_file = Path(config_file)
                        try:
                            if config_file.exists():
                                with config_file.open() as test:
                                    if test.readline().strip() != salt_managed_message:
                                        print(DAEMON_NAME, '-->', 'File "{}" does not start with {}'.format(config_file, salt_managed_message), flush=True)
                                        continue
                                with config_file.open('w') as out:  # re-open for writing
                                    out.write(BOOT_FROM_DISK_CONFIG_TEXT)
                                    print(DAEMON_NAME, '-->', 'Replaced file "{}"'.format(config_file), flush=True)
                            else:
                                print(DAEMON_NAME, '-->', 'File "{}" does not exist.'.format(config_file), flush=True)
                        except OSError as err:
                            print(DAEMON_NAME, '-->', 'Error writing file {} --> {}'.format(config_file, err), flush=True)
                            self.send_error(400, 'OSError', err)

                    next_commands = data['next_command']
                    if len(next_commands) == 0:
                        self.send_response(200)
                    else:
                        for next_command in next_commands:
                            print(DAEMON_NAME, '-->', 'Running command: "{}"'.format(next_command), flush=True)
                            try:
                                # # # Run the command as a shell script
                                proc = subprocess.Popen(next_command, shell=True, universal_newlines=True)
                                return_code = proc.wait(5)
                                print(DAEMON_NAME, '-->', 'Command returned with {}'.format(return_code), flush=True)
                                # # #
                            except subprocess.TimeoutExpired:
                                print(DAEMON_NAME, '-->', 'Command is still running -- moving on...', flush=True)
                            except (subprocess.SubprocessError, OSError) as err:
                                error_text = 'Calling process caused error code {}'.format(err.returncode)
                                print(DAEMON_NAME, '-->', error_text, flush=True)
                                self.send_error(500, 'Error spawning process.', error_text)
                                break
                        self.send_response(202)
                except (KeyError, IndexError):
                    pass
                if key:
                    try:
                        job_list.pop(key)
                        if len(job_list) == 0:
                            print(DAEMON_NAME, '-->', 'All candidates cleared, will exit.', flush=True)
                            work_is_done = True
                    except KeyError:
                        pass
            else:
                self.send_error(400, 'Bad query', 'Query neither "/store?" nor "/execute?"', flush=True)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Send message back to client
        message = '<body>Received query "{}".\n</body></html>'.format(self.path)
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))

        if work_is_done:
            time.sleep(5)
            self.server._BaseServer__shutdown_request = True
        return


def timed_shutdown(http_server):
    print(DAEMON_NAME, '-->', 'Timer expired, requesting shut down.', flush=True)
    http_server.shutdown()
    time.sleep(5)


def run(port_number):
    print(DAEMON_NAME, '-->', "Starting server - port:{}".format(port_number))

    try:
        server_address = ('0.0.0.0', port_number)  # serve all interfaces using our special port
        http_server = StoppableHTTPServer(server_address, FileClearingRequestHandler)
    except OSError as err:
        if err.errno == 98:
            print(DAEMON_NAME, '-->', 'Port {} already in use.'.format(port_number))
            print(DAEMON_NAME, '-->', 'HINT: you can shut down my brother daemon by:')
            print(DAEMON_NAME, '-->', 'wget -O - http://localhost:{}/shutdown'.format(port_number))
            http_server = None
        else:
            raise
    if http_server:
        http_server.job_list = {}  # initialize job list in server instance
        game_over = threading.Timer(wait_time, timed_shutdown, (http_server,))
        game_over.start()
        print(DAEMON_NAME, '-->', 'running server...')
        server = threading.Thread(target=http_server.run)
        server.start()

        server.join()
        print(DAEMON_NAME, '-->', "Server Stopped - port:{}".format(port_number))
        game_over.cancel()
    else:
        print(DAEMON_NAME, '-->', 'Could not create a server.')
        exit(1)


if __name__ == '__main__':
    run(http_port_number)
