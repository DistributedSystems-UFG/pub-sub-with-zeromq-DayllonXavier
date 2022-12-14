import sys
import threading
import zmq
from consts import * #-

class SpecialListening(threading.Thread):
    def __init__(self, ip, port, subscriberSocket):
        threading.Thread.__init__(self, daemon=True)
        self.ip = ip
        self.port = port
        self.subscriberSocket = subscriberSocket
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
                    print("{} -> ({} JOINED TO THE GROUP)".format(message[3], message[4]))
                    if (message[1] == 'CONNECT'):
                        ip, port = message[2].split('/')
                        self.subscriberSocket.connect("tcp://"+ ip +":"+ port)
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
        self.socketToServer = self.context.socket(zmq.REQ)
        self.socketToIndividual = None
        #self.subscriberSocket = None

        self.friends = {}
        self.myGroups = []

        self.specialListening = None
        self.subscriberListening = None

    def connectToServer(self):
        serverDescription = "tcp://"+ HOST +":"+ PORT
        self.socketToServer.connect(serverDescription)

        self.saudationToServer()

    def initPublisher(self):
        self.publisherSocket = self.context.socket(zmq.PUB)
        self.publisherSocket.bind("tcp://"+ self.ip +":"+ self.port)

    def saudationToServer(self):
        self.socketToServer.send(str.encode("SAUDATION {} {} {} {}".format(self.name, self.ip, self.port, self.specialPort)))
        response = bytes.decode(self.socketToServer.recv())
        if (response != "ACK"):
            print(response)
            self.listening = False

    def validOperation(self, operation):
        while ("" in operation):
            operation.remove("")
        if (len(operation) == 0):
            return False
        return (
            (operation[0] == 'TO' and len(operation) >= 3) or
            (operation[0] == 'PUB' and len(operation) >= 3) or
            (operation[0] == 'REGISTER' and len(operation) == 2)
        )

    def start(self):
        self.initPublisher()
        self.subscriberSocket = self.context.socket(zmq.SUB)
        self.subscriberListening = SubscriberListening(self.subscriberSocket, self.name)
        self.specialListening = SpecialListening(self.ip, self.specialPort, self.subscriberSocket)
        self.subscriberListening.start()
        self.specialListening.start()
        self.connectToServer()
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
        self.socketToServer.send(str.encode("GOODBYE {}".format(self.name)))
        response = bytes.decode(self.socketToServer.recv())

    def processOperation(self, operation):
        if (operation[0] == 'PUB'):
            self.processPublication(operation[1], ' '.join(operation[2:]))
        elif (operation[0] == 'ADDRESS'):
            self.processAddress(operation[1])
        elif (operation[0] == 'REGISTER'):
            self.processRegister(operation[1])
        elif (operation[0] == 'TO'):
            self.processIndividualMessage(operation[1], ' '.join(operation[2:]))

    def processAddress(self, name):
        self.socketToServer.send(str.encode("ADDRESS {}".format(name)))
        response = bytes.decode(self.socketToServer.recv())
        if (response == "NACK"):
            print("No user founded.")
            return False
        
        self.friends[name] = response
        return True

    def processRegister(self, group):
        self.socketToServer.send(str.encode("REGISTER {} {}".format(self.name, group)))
        response = bytes.decode(self.socketToServer.recv())
        if (response != "ACK"):
            self.myGroups.append(group)
        response = response.split()
        for address in response:
            ip, port = address.split('/')
            self.subscriberSocket.connect("tcp://"+ ip +":"+ port)
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
        

if (__name__ == '__main__'):
    user = User(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    user.start()

#s.send(str.encode("LEAVE NANAN"))
#message = bytes.decode(s.recv())
#print(message)