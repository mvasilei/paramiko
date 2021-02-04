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
   except paramiko.AuthenticationException as error:
      print 'Authentication Error'
      return False, False

   return (channel,client)

def connection_teardown(client):
   client.close()

def execute_command(command, channel):
   channel.send('term len 0\n')
   channel.send(command)
   while not channel.recv_ready():
      time.sleep(1)

   out = channel.recv(65535)
   return (out)

def main():
   show_interfaces_status = 'show interface status | i notco|sfp\n'
   # match interfaces and put interface name in group mif description on group description
   pattern = re.compile(r'(?P<mif>^.\D{1,3}(\d{1,4}\/){1,2}\d{1,3})(?P<description>.+(?=notconn|sfpA))')
   # read the file with the hostnames
   try:
      with open('hostfile', 'r') as h:
         lines = h.readlines()
   except IOError:
      print 'Could not read file .hostfile'

   try:
      with open('output.txt', 'w') as o:

         USER = raw_input('Username: ')

         #for each hostname establish connection execute the show command and if the description is empty add entry to the file named
         #after the host to shutdonw the correspondin interface
         for host in lines:
            print host
            PASS = getpass.getpass(prompt='Password: ')
            channel,client = connection_establishment(USER, PASS, host.strip())

            if channel is not False:
               out = execute_command(show_interfaces_status, channel)
               connection_teardown(client)
               o.write(out)

               try:
                  with open(host.strip()+'.txt', 'w') as d:
                     for output_line in out.splitlines():
                        interface = pattern.match(output_line)
                        if interface:
                           if (interface.group('description').isspace() or interface.group('description').strip() == '--'):
                              d.write("interface " + interface.group('mif').strip() +'\r\n shutdown\r\n')
               except IOError:
                  print 'Could open' + host.strip() + '.txt file to write'

   except IOError:
      print 'Could open output.txt file to write'

if __name__ == '__main__':
   signal.signal(signal.SIGINT, signal_handler)  # catch ctrl-c and call handler to terminate the script
   main()
