import sys
import threading
from socket import *
import zmq
from consts import * #-

class SpecialListening(threading.Thread):
    def __init__(self, ip, port, subscriberSocket, countConnectionAddress):
        threading.Thread.__init__(self, daemon=True)
        self.ip = ip
        self.port = port
        self.subscriberSocket = subscriberSocket
        self.countConnectionAddress = countConnectionAddress
        self.context = zmq.Context()
        self.initSocket()
    
    def initSocket(self):
        self.specialListeningSocket = self.context.socket(zmq.REP)
        self.specialListeningSocket.bind("tcp://"+ self.ip +":"+ self.port)
    
    def run(self):
        while True:
            try:
                message = bytes.decode(self.specialListeningSocket.recv()).split()
                if (message[0] == 'INDIVIDUAL'):
                    print("FROM PERSON {}: {}".format(message[1], ' '.join(message[2:])))
                elif (message[0] == 'SERVER'):
                    address = message[2]
                    if (message[1] == 'CONNECT'):
                        print("{} -> ({} JOINED TO THE GROUP)".format(message[3], message[4]))
                        if (address not in self.countConnectionAddress):
                            self.countConnectionAddress[address] = 0
                            ip, port = address.split('/')
                            self.subscriberSocket.connect("tcp://"+ ip +":"+ port)
                        self.countConnectionAddress[address] += 1
                    elif (message[1] == 'LEAVE'):
                        print("{} -> ({} LEAVE THE GROUP)".format(message[3], message[4]))
                        if (address in self.countConnectionAddress):
                            self.countConnectionAddress[address] -= 1
                            if (self.countConnectionAddress[address] == 0):
                                ip, port = address.split('/')
                                self.subscriberSocket.disconnect("tcp://"+ ip +":"+ port)
                                self.countConnectionAddress.pop(address)
            except:
                self.initSocket()

class SubscriberListening(threading.Thread):
    def __init__(self, subscriberSocket, name):
        threading.Thread.__init__(self, daemon=True)
        self.subscriberSocket = subscriberSocket
        self.name = name

    def run(self):
        while(True):
            message = bytes.decode(self.subscriberSocket.recv()).split()
            if (message[1] != self.name):
                print("{} -> {} : {}".format(message[0], message[1], ' '.join(message[2:])))

class User:
    def __init__(self, name, ip, port, specialPort):
        self.listening = True

        self.name = name
        self.ip = ip
        self.port = port
        self.specialPort = specialPort
        self.context = zmq.Context()

        self.socketToIndividual = None
        #self.subscriberSocket = None

        self.friends = {}
        self.myGroups = []
        self.countConnectionAddress = {}

        self.specialListening = None
        self.subscriberListening = None

    def connectToServer(self):
        self.socketToServer = socket(AF_INET, SOCK_STREAM)
        try:
            self.socketToServer.connect((HOST, int(PORT)))
        except:
            print("Server is down. Exiting...")
            exit(1)

    def disconnectToServer(self):
        self.socketToServer.close()

    def initPublisher(self):
        self.publisherSocket = self.context.socket(zmq.PUB)
        self.publisherSocket.bind("tcp://"+ self.ip +":"+ self.port)

    def saudationToServer(self):
        self.connectToServer()
        self.socketToServer.send(str.encode("SAUDATION {} {} {} {}".format(self.name, self.ip, self.port, self.specialPort)))
        response = bytes.decode(self.socketToServer.recv(2048))
        if (response != "ACK"):
            print(response)
            self.listening = False
        self.disconnectToServer()

    def validOperation(self, operation):
        while ("" in operation):
            operation.remove("")
        if (len(operation) == 0):
            return False
        return (
            (operation[0] == 'TO' and len(operation) >= 3) or
            (operation[0] == 'PUB' and len(operation) >= 3) or
            (operation[0] == 'REGISTER' and len(operation) == 2) or
            (operation[0] == 'LEAVE' and len(operation) == 2)
        )

    def start(self):
        self.initPublisher()
        self.subscriberSocket = self.context.socket(zmq.SUB)
        self.subscriberListening = SubscriberListening(self.subscriberSocket, self.name)
        self.specialListening = SpecialListening(self.ip, self.specialPort, self.subscriberSocket, self.countConnectionAddress)
        self.subscriberListening.start()
        self.specialListening.start()
        self.saudationToServer()
        while(self.listening):
            operation = input()
            if (operation == ''):
                continue
            if (operation == 'EXIT'):
                break
            operation = operation.split()
            if (not self.validOperation(operation)):
                print("Invalid Operation.")
                continue
            self.processOperation(operation)
        self.exit()
    
    def exit(self):
        while(len(self.myGroups)):
            self.processLeave(self.myGroups[0])
        self.connectToServer()
        self.socketToServer.send(str.encode("GOODBYE {}".format(self.name)))
        response = bytes.decode(self.socketToServer.recv(2048))
        self.disconnectToServer()

    def processOperation(self, operation):
        if (operation[0] == 'PUB'):
            self.processPublication(operation[1], ' '.join(operation[2:]))
        elif (operation[0] == 'ADDRESS'):
            self.processAddress(operation[1])
        elif (operation[0] == 'REGISTER'):
            self.processRegister(operation[1])
        elif (operation[0] == 'TO'):
            self.processIndividualMessage(operation[1], ' '.join(operation[2:]))
        elif (operation[0] == 'LEAVE'):
            self.processLeave(operation[1])

    def processAddress(self, name):
        self.connectToServer()
        self.socketToServer.send(str.encode("ADDRESS {}".format(name)))
        response = bytes.decode(self.socketToServer.recv(2048))
        if (response == "NACK"):
            print("No user founded.")
            return False
        
        self.friends[name] = response
        self.disconnectToServer()
        return True

    def processRegister(self, group):
        self.connectToServer()
        self.socketToServer.send(str.encode("REGISTER {} {}".format(self.name, group)))
        response = bytes.decode(self.socketToServer.recv(2048))
        if (response == "ACK"):
            return
        self.disconnectToServer()
        self.myGroups.append(group)
        response = response.split()
        for address in response:
            if (address not in self.countConnectionAddress):
                self.countConnectionAddress[address] = 0
                ip, port = address.split('/')
                self.subscriberSocket.connect("tcp://"+ ip +":"+ port)
            self.countConnectionAddress[address] += 1
        self.subscriberSocket.setsockopt_string(zmq.SUBSCRIBE, group)
    
    def processPublication(self, group, message):
        if (group not in self.myGroups):
            print("NO GROUP FOUNDED.")
            return
        self.publisherSocket.send(str.encode("{} {} {}".format(group, self.name, message)))
        #if (self.name == 'DAYLLON'):
        #    self.subscriberSocket.connect("tcp://"+ self.ip +":"+ '9998')

    def processIndividualMessage(self, name, message):
        if (name not in self.friends):
            response = self.processAddress(name)
            if (not response):
                return

        self.socketToIndividual = self.context.socket(zmq.REQ)
        address = self.friends[name].split('/')
        addressWay = "tcp://"+ address[0] +":"+ address[1]
        self.socketToIndividual.connect(addressWay)
        self.socketToIndividual.send(str.encode(
            "INDIVIDUAL {} {}".format(self.name, message)
        ))
        self.socketToIndividual.disconnect(addressWay)
    
    def processLeave(self, group):
        if (group not in self.myGroups):
            print("NO GROUP FOUNDED.")
            return
        
        self.connectToServer()
        self.socketToServer.send(str.encode("LEAVE {} {}".format(self.name, group)))
        response = bytes.decode(self.socketToServer.recv(2048))
        if (response == "ACK"):
            return
        self.disconnectToServer()
        response = response.split()
        for address in response:
            self.countConnectionAddress[address] -= 1
            if (self.countConnectionAddress[address] == 0):
                self.countConnectionAddress.pop(address)
                ip, port = address.split('/')
                self.subscriberSocket.disconnect("tcp://"+ ip +":"+ port)
        self.subscriberSocket.setsockopt_string(zmq.UNSUBSCRIBE, group)
        self.myGroups.remove(group)
        

if (__name__ == '__main__'):
    user = User(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    user.start()