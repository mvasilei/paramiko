#! /usr/bin/env python
import getpass, paramiko, time, signal, re, sys

def signal_handler(sig, frame):
    print('Exiting gracefully Ctrl-C detected...')
    sys.exit(0)

def connection_establishment(USER, PASS, host):
   try:
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      client.connect(host, 22, username=USER, password=PASS)
      channel = client.invoke_shell()
      while not channel.recv_ready():
         time.sleep(1)

      channel.recv(65535)
   except paramiko.AuthenticationException as AuthError:
      print 'Authentication Error'
      return False, False
   except SSHException as sshException:
      print 'Unable to establish SSH connection' + sshException
      return False, False


   return (channel,client)

def connection_teardown(client):
   client.close()

def execute_command(command, channel):

   channel.send(command)
   while not channel.recv_ready():
      time.sleep(1)

   out = channel.recv(65535)

   return (out)

def main():
   # read the file with the hostnames, must be one host per line full fqdn
   # read the commands file, must be one command per line shouldn't include conf t and copy run start commands
   try:
      with open('hostfile', 'r') as h, open('commands', 'r') as c:
         host_lines = h.readlines()
         command_lines = c.readlines()
   except IOError:
      print 'Could not read file'

   warning_list = ['Invalid', 'Incomplete']
   USER = raw_input('Username: ')

   #for each hostname establish connection

   for host in host_lines:
      print host
      PASS = getpass.getpass(prompt='Password: ')
      channel,client = connection_establishment(USER, PASS, host.strip())

      #if connection to the host is successful enter configuration mode and execute the commands in command file
      if channel is not False:
         execute_command('term len 0\n', channel)
         execute_command('configure terminal\n', channel)

         error = False

         for command in command_lines:
            out = execute_command(command + '\n', channel)

            # if an error was raised while configuring the host print a warning terminate the connection and move to the next host
            for warning in warning_list:
               if (warning in out):
                  print 'Error while configuring ' + host + " CMD:" + command
                  connection_teardown(client)
                  error = True
                  continue

            if error:
               connection_teardown(client)
               continue

         execute_command('copy run start\n', channel)
         connection_teardown(client)         


if __name__ == '__main__':
   signal.signal(signal.SIGINT, signal_handler)  # catch ctrl-c and call handler to terminate the script
   main()
