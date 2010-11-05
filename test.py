import socket
import os
import struct

sp = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)

pid = os.fork()
if pid == 0:
	ipc = sp[0]
	sp[1].close()
	print "[+] Child forked"
	fp = ipc.recvmsg(1)[1][0][0]
	print "[+] Child received the file descriptor, the contents:"
	print(fp.read(10000))
else:
	ipc = sp[1]
	sp[0].close()

	fp = open("/etc/passwd")

	print "[+] Parent forked child with pid", pid
	ret = ipc.sendmsg("x", None, [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
			  struct.pack("i", fp.fileno()))], 0)
	print "[+] Parent has sent the open file descriptor"
