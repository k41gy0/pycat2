# bhnet.py
import sys
import socket
import argparse
from threading import Thread
import subprocess
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                description='BHP Net Tool',
                epilog='''\
Examples:
    bhnet.py -t 192.168.0.1 -p 5555 -l -c
    bhnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe
    bhnet.py -t 192.168.0.1 -p 5555 -l -e 'cat /etc/passwd'
    echo 'ABCDEFGHI' | ./bhnet.py -t 192.168.11.12 -p 135''')
 
parser.add_argument('-l', '--listen', help='listen on [host]:[port] for incoming connections', action='store_true')
parser.add_argument('-e', '--execute', default=None, help='execute the given file upon receiving a connection')
parser.add_argument('-c', '--command', help='initialize a command shell', action='store_true')
parser.add_argument('-u', '--upload', help='upon receiving connection upload a file and write to [destination]')
parser.add_argument('-t', '--target', default=None)
parser.add_argument('-p', '--port', default=None, type=int)
args = parser.parse_args()
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    try:
        client.connect((args.target, args.port))
        if len(buffer):
            client.send(buffer)
 
        while True:
            recv_len = 1
            response = ''
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode('utf-8')
                if recv_len < 4096:
                    break
            print(response.rstrip(), end='')
            buffer = input()
            if buffer == '':
                continue
            if buffer == 'exit':
                client.send(b'exit')
                break
            client.send(buffer.encode('utf-8'))
        client.close()
    except:
        print('[*] Exception! Exiting.')
        client.close()

def server_loop():
    if not args.target:
        args.target = '0.0.0.0'
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.target, args.port))
 
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        client_thread = Thread(target=client_handler, args=[client_socket,])
        client_thread.start()

def run_command(command):
    command = command.rstrip()
 
    try:
        output = subprocess.check_output(
                    command,stderr=subprocess.STDOUT, shell=True)
    except:
        output = b'Failed to execute command.'
 
    return output


def client_handler(client_socket):
    if args.upload:
        file_buffer = b''
 
        while True:
            data = client_socket.recv(1024)
            file_buffer += data
            if len(data) < 1024:
                break
 
        try:
            file_descriptor = open(args.upload, 'wb')
            file_descriptor.write(file_buffer)
            file_descriptor.close()
 
            client_socket.send('Successfully saved file to {}'.format(args.upload).encode('utf-8'))
        except:
            client_socket.send('Failed to save file to {}'.format(args.upload).encode('utf-8'))
 
    if args.execute:
        output = run_command(args.execute)
        client_socket.send(output)
 
    if args.command:
        prompt = b'<BH:#> '
        client_socket.send(prompt)
 
        while True:
            recv_len = 1
            cmd_buffer = ''
            while recv_len:
                buffer = client_socket.recv(1024)
                recv_len = len(buffer)
                cmd_buffer += buffer.decode('utf-8')
                if recv_len < 1024:
                    break
            if cmd_buffer == 'exit':
                client_socket.close()
                break
            response = run_command(cmd_buffer)
 
            client_socket.send(response + prompt)

def main():
    if not args.listen and args.target and args.port:
        buffer = sys.stdin.read()
        client_sender(buffer.encode('utf-8'))
    elif args.listen:
        server_loop()
    else:
        parser.print_help()
        sys.exit(1)
 
if __name__ == '__main__':
    main()