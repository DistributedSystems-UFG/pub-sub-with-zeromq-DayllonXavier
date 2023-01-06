import zmq
from consts import * #-

groups = {}
users = {}

class Server():
    def __init__(self):
        self.context = zmq.Context()

        descPoint = "tcp://"+ HOST +":"+ PORT

        self.serverSocket = self.context.socket(zmq.REP)
        self.serverSocket.bind(descPoint)

        self.specialSocket = None

    def validRequisition(self, requisition):
        while ("" in requisition):
            requisition.remove("")
        if (len(requisition) == 0):
            return False
        return (
            (requisition[0] == 'SAUDATION' and len(requisition) == 5) or
            (requisition[0] == 'GOODBYE' and len(requisition) == 2) or
            (requisition[0] == 'REGISTER' and len(requisition) == 3) or
            (requisition[0] == 'ADDRESS' and len(requisition) == 2)
        )

    def start(self):
        print("Server listening...")
        while True:
            requisition = bytes.decode(self.serverSocket.recv()).split()
            print(requisition)
            if (not self.validRequisition(requisition)):
                self.serverSocket.send(str.encode("INVALID OPERATION."))
                continue

            self.processRequisition(requisition)

            #s.send(str.encode(message + "*"))
    
    def processRequisition(self, requisition):
        if (requisition[0] == 'SAUDATION'):
            self.processSaudation(requisition[1], requisition[2], requisition[3], requisition[4])
        elif (requisition[0] == 'GOODBYE'):
            self.processGoodbye(requisition[1])
        elif (requisition[0] == 'ADDRESS'):
            self.processAddress(requisition[1])
        elif (requisition[0] == 'REGISTER'):
            self.processRegister(requisition[1], requisition[2])

    def processSaudation(self, name, ip, port, specialPort):
        if (name in users):
            self.serverSocket.send(str.encode("NACK - NAME ALREADY USE."))
            return
        users[name] = "{}/{}/{}".format(ip, port, specialPort)
        self.serverSocket.send(str.encode("ACK"))

    def processGoodbye(self, name):
        users.pop(name)
        self.serverSocket.send(str.encode("ACK"))
    
    def processAddress(self, name):
        if (name not in users):
            self.serverSocket.send(str.encode("NACK"))
            return
        address = users[name].split('/')
        self.serverSocket.send(str.encode(address[0]+'/'+address[2]))
    
    def processRegister(self, name, group):
        alertAllMembers = False

        if (not group in groups):
            groups[group] = []
        if (not name in groups[group]):
            groups[group].append(name)
            alertAllMembers = True
        
        if (alertAllMembers):
            addresses = []
            addressToAlert = []
            for member in groups[group]:
                if (member != name):
                    address = users[member].split('/')
                    addresses.append(address[0]+'/'+address[1])
                    addressToAlert.append(address[0]+'/'+address[2])
            self.serverSocket.send(str.encode(addresses.__str__()[1:-1].replace(',', '').replace("\'",'').replace("\"", '')))

            newMember = '/'.join(users[name].split('/')[:2])
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

if (__name__  == '__main__'):
    server = Server()
    server.start()

"""
Types of requisitions

SAUDANTION NAME IP PORT
ADDRESS NAME
REGISTER NAME <topic>


"""