#include "Python.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

int recv_fd(int sock) 
{
    struct msghdr msg;
    struct iovec iov[1];
    u_char c;
    
    union {
        struct cmsghdr cm;
        char control[CMSG_SPACE(sizeof(int))];
    } control_un;
    struct cmsghdr *cmptr;
    
    msg.msg_control = control_un.control;
    msg.msg_controllen = sizeof(control_un.control);
    msg.msg_name = NULL;
    msg.msg_namelen = 0;
    
    iov[0].iov_base = &c;
    iov[0].iov_len = 1;
    msg.msg_iov = iov;
    msg.msg_iovlen = 1;
    
    if (recvmsg(sock, &msg, 0) <= 0) {
        perror("recv_fd()");
        return -1;
    }
    
    if ( (cmptr = CMSG_FIRSTHDR(&msg)) != NULL && cmptr->cmsg_len == CMSG_LEN(sizeof(int)) ) {
        if (cmptr->cmsg_level != SOL_SOCKET)
            return -3;
        if (cmptr->cmsg_type != SCM_RIGHTS)
            return -3;
        return *((int *) CMSG_DATA(cmptr));
    } else {
        return -2;
    }
}

int send_fd(int sock, int fd)
{
    struct msghdr msg;
    struct iovec iov[1];
    
    union {
        struct cmsghdr cm;
        char control[CMSG_SPACE(sizeof(int))];
    } control_un;
    struct cmsghdr *cmptr;
    
    msg.msg_name = NULL;
    msg.msg_namelen = 0;
    msg.msg_control = control_un.control;
    msg.msg_controllen = sizeof(control_un.control);
    
    iov[0].iov_base = "";
    iov[0].iov_len = 1;
    msg.msg_iov = iov;
    msg.msg_iovlen = 1;
    
    cmptr = CMSG_FIRSTHDR(&msg);
    cmptr->cmsg_len = CMSG_LEN(sizeof(int));
    cmptr->cmsg_level = SOL_SOCKET;
    cmptr->cmsg_type = SCM_RIGHTS;
    *((int *) CMSG_DATA(cmptr)) = fd;
    
    int ret = sendmsg(sock, &msg, 0);
    if (ret <= 0) {
        perror("sendmsg");
        return ret;
    }
    
    return 0;
}


/*** Python Module ***/
PyDoc_STRVAR(tradesocket__doc__, "Tradesocket, send and recieve a file-descriptor over a unix socket.");


PyDoc_STRVAR(send_fd__doc__, "Send a file-descriptor over a unix socket.");
static PyObject* py_send_fd(PyObject *self, PyObject *args)
{
    int sock, fd;
    int returncode;
	
	if (!PyArg_ParseTuple(args, "ii:send_fd", &sock, &fd))
		return NULL;
	
	returncode = send_fd(sock, fd);
	return Py_BuildValue("i", returncode);
}


PyDoc_STRVAR(recv_fd__doc__, "Recieve a file-descriptor from a socket.");
static PyObject* py_recv_fd(PyObject *self, PyObject *args)
{
    int sock, fd;
	
	if (!PyArg_ParseTuple(args, "i:recv_fd", &sock))
		return NULL;
	
	//recv_fd(&fd, sock);
    fd = recv_fd(sock);
	return Py_BuildValue("i", fd);
}


static PyMethodDef tradesocket_methods[] = {
	{"send_fd",  py_send_fd, METH_VARARGS, send_fd__doc__},
	{"recv_fd",  py_recv_fd, METH_VARARGS, recv_fd__doc__},
	{NULL, NULL}      /* sentinel */
};


PyMODINIT_FUNC inittradesocket(void)
{
	Py_InitModule3("tradesocket", tradesocket_methods, tradesocket__doc__);
}