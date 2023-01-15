import zmq
import threading
from socket import *
import pickle
from consts import * #-

class WorkThread(threading.Thread):
    def __init__(self, connection, groups, users):
        threading.Thread.__init__(self, daemon=True)
        self.serverSocket = connection
        self.groups = groups
        self.users = users

        self.context = zmq.Context()

    def run(self):
        requisition = bytes.decode(self.serverSocket.recv(1024)).split()
        print(requisition)

        if (not self.validRequisition(requisition)):
            self.serverSocket.send(str.encode("INVALID OPERATION."))
            return

        self.processRequisition(requisition)

        self.serverSocket.close()

    def validRequisition(self, requisition):
        while ("" in requisition):
            requisition.remove("")
        if (len(requisition) == 0):
            return False
        return (
            (requisition[0] == 'SAUDATION' and len(requisition) == 5) or
            (requisition[0] == 'GOODBYE' and len(requisition) == 2) or
            (requisition[0] == 'REGISTER' and len(requisition) == 3) or
            (requisition[0] == 'ADDRESS' and len(requisition) == 2) or
            (requisition[0] == 'LEAVE' and len(requisition) == 3)
        )
    
    def processRequisition(self, requisition):
        if (requisition[0] == 'SAUDATION'):
            self.processSaudation(requisition[1], requisition[2], requisition[3], requisition[4])
        elif (requisition[0] == 'GOODBYE'):
            self.processGoodbye(requisition[1])
        elif (requisition[0] == 'ADDRESS'):
            self.processAddress(requisition[1])
        elif (requisition[0] == 'REGISTER'):
            self.processRegister(requisition[1], requisition[2])
        elif (requisition[0] == 'LEAVE'):
            self.processLeave(requisition[1], requisition[2])

    def processSaudation(self, name, ip, port, specialPort):
        if (name in self.users):
            self.serverSocket.send(str.encode("NACK - NAME ALREADY USE."))
            return
        self.users[name] = "{}/{}/{}".format(ip, port, specialPort)
        self.serverSocket.send(str.encode("ACK"))

    def processGoodbye(self, name):
        self.users.pop(name)
        self.serverSocket.send(str.encode("ACK"))
    
    def processAddress(self, name):
        if (name not in self.users):
            self.serverSocket.send(str.encode("NACK"))
            return
        address = self.users[name].split('/')
        self.serverSocket.send(str.encode(address[0]+'/'+address[2]))
    
    def processRegister(self, name, group):
        alertAllMembers = False

        if (group not in self.groups):
            self.groups[group] = []
        if (name not in self.groups[group]):
            self.groups[group].append(name)
            alertAllMembers = True
        
        if (alertAllMembers):
            addresses = []
            addressToAlert = []
            for member in self.groups[group]:
                if (member != name):
                    address = self.users[member].split('/')
                    addresses.append(address[0]+'/'+address[1])
                    addressToAlert.append(address[0]+'/'+address[2])
            self.serverSocket.send(str.encode(addresses.__str__()[1:-1].replace(',', '').replace("\'",'').replace("\"", '')))

            newMember = '/'.join(self.users[name].split('/')[:2])
            for address in addressToAlert:
                ip, port = address.split('/')
                addressWay = "tcp://"+ ip +":"+ port
                self.specialSocket = self.context.socket(zmq.REQ)
                self.specialSocket.connect(addressWay)
                self.specialSocket.send(str.encode(
                    "SERVER CONNECT {} {} {}".format(newMember, group, name)
                ))
                self.specialSocket.disconnect(addressWay)
        else:
            self.serverSocket.send(str.encode("ACK"))

    def processLeave(self, name, group):
        if ((group not in self.groups) or (name not in self.groups[group])):
            self.serverSocket.send(str.encode("ACK"))
            return

        self.groups[group].remove(name)
        
        addresses = []
        addressToAlert = []
        for member in self.groups[group]:
            address = self.users[member].split('/')
            addresses.append(address[0]+'/'+address[1])
            addressToAlert.append(address[0]+'/'+address[2])
        self.serverSocket.send(str.encode(addresses.__str__()[1:-1].replace(',', '').replace("\'",'').replace("\"", '')))
        notMoreMember = '/'.join(self.users[name].split('/')[:2])
        for address in addressToAlert:
            ip, port = address.split('/')
            addressWay = "tcp://"+ ip +":"+ port
            self.specialSocket = self.context.socket(zmq.REQ)
            self.specialSocket.connect(addressWay)
            self.specialSocket.send(str.encode(
                "SERVER LEAVE {} {} {}".format(notMoreMember, group, name)
            ))
            self.specialSocket.disconnect(addressWay)

class Server():
    def __init__(self):

        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((HOST, int(PORT)))
        self.serverSocket.listen(5)

        self.groups = {}
        self.users = {}

    def start(self):
        print("Server listening...")
        while True:
            conn, addr = self.serverSocket.accept()
            workThread = WorkThread(conn, self.groups, self.users)
            workThread.start()

if (__name__  == '__main__'):
    server = Server()
    server.start()