'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    def __init__(self, cost=0, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.cost = cost
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    prot_S_length = 1
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst_addr, prot_S, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst_addr, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        p = NetworkPacket(dst_addr, 'data', data_S)
        self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
        print('%s: sending packet "%s"' % (self, p))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        
#You will need to come up with a message that encodes the state of your routing tables.
# My advise would be to come up with a message class that has a to byte S() from byte S() functions.

class Message:
    table_item_length = 1 ##1???

    def __init__(self, zero_one, zero_two, one_one, one_two):
        self.zero_one = zero_one
        self.zero_two = zero_two
        self.one_one = one_one
        self.one_two = one_two

    def __str__(self):
        return self.to_byte_S()

    def to_byte_S(self):
        byte_S = str(self.zero_one).zfill(self.table_item_length)
        byte_S += str(self.zero_two).zfill(self.table_item_length)
        byte_S += str(self.one_one).zfill(self.table_item_length)
        byte_S += str(self.one_two).zfill(self.table_item_length)
        return byte_S

    @classmethod
    def from_byte_S(self, byte_S):
        zero_one = int(byte_S[0:Message.table_item_length])
        zero_two = int(byte_S[Message.table_item_length: Message.table_item_length + Message.table_item_length])
        one_one =  int(byte_S[Message.table_item_length + Message.table_item_length: Message.table_item_length + Message.table_item_length+Message.table_item_length])
        one_two =  int(byte_S[Message.table_item_length + Message.table_item_length+Message.table_item_length : ])
        return self(zero_one, zero_two, one_one,one_two)

## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, in_intf_count, out_intf_cost_L, rt_tbl_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(in_intf_count)]
        #note the number of outgoing interfaces is set up by out_intf_cost_L
        self.out_intf_L = []
        for cost in out_intf_cost_L:
            self.out_intf_L.append(Interface(cost, max_queue_size))
        #set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D 

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.in_intf_L[i].get()
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            
    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is also i
            self.out_intf_L[i].put(p.to_byte_S(), True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    ## forward the packet according to the routing table
    #  @param p Packet containing routing information

    #Modify function to update routing tables (bellman ford)
    #based on updates from router.send_routes
    #receiving an update may mean you should send one as well!!

    #page 384
    def update_routes(self, p):
        #TODO: add logic to update the routing tables and
        print('%s: Received routing update %s' % (self, p))
        send = True

        dict = self.rt_tbl_D
        zero_one = '~'
        zero_two = '~'
        one_one = '~'
        one_two = '~'

        if 1 in dict:
            thing = dict.get(1)
            if 0 in thing:
                zero_one = str(thing.get(0))
            if 1 in thing:
                one_one = str(thing.get(1))

        if 2 in dict:
            thing = dict.get(2)
            if 0 in thing:
                zero_two = str(thing.get(0))
            if 1 in thing:
                one_two = str(thing.get(1))

        #get rid of the first six characters....only want the routing table
        p2 = p.to_byte_S()
        p2 = p2[6: len(p2)]

        ##get the new values from the routing table you got sent

        new_zero_one = p2[0:1]
        new_zero_two = p2[1:2]

        new_one_one =  p2[2:3]
        new_one_two =  p2[3:4]

        #need to compare what you get with what you have...

        if zero_one is '~' and new_zero_one is not '~':
            zero_one = new_zero_one
            send = False
        elif zero_one is not '~' and new_zero_one is not '~' and new_zero_one < zero_one:
            send = False
            zero_one = new_zero_one

        if zero_two is '~' and new_zero_two is not '~':
            send = False
            zero_two = new_zero_two
        elif zero_two is not '~' and new_zero_two is not '~' and new_zero_two < zero_two:
            send = False
            zero_two = new_zero_two

        if one_one is '~' and new_one_one is not '~':
            send = False
            one_one = new_one_one
        elif one_one is not '~' and new_one_one is not '~' and new_one_one < one_one:
            send = False
            one_one = new_one_one

        if one_two is '~' and new_one_two is not '~':
            one_two = new_one_two
            send = False
        elif one_two is not '~' and new_one_two is not '~' and new_one_two < one_two:
            one_two = new_one_two
            send = False



        self.rt_tbl_D[1]={0: zero_one, 1: one_one}
        self.rt_tbl_D[2]={0: zero_two, 1: one_two}

        #print("UPDATE table is", self.rt_tbl_D)


        #need some kind of boolean/loop to keep going until no change
        if send is False:
            if self.name == 'A':
                self.send_routes(0)
            if self.name == 'B':
                self.send_routes(1)


    ## send out route update
    # @param i Interface number on which to send out a routing update

    #send routes based on link state protocol
    #page 379...
        #all link costs are known
        #each node boradcasts link-state packets to all other nodes in network
            #each link state packet contains the identities and costs of its attached links
        #dijkstra?

    def send_routes(self, i):
        # a sample route update packet
        dict = self.rt_tbl_D
        #print("SEND TABLE IS",self.rt_tbl_D)
        zero_one = '~'
        zero_two = '~'
        one_one = '~'
        one_two = '~'

        if 1 in dict:
            thing = dict.get(1)
            if 0 in thing:
                zero_one = str(thing.get(0))
            if 1 in thing:
                one_one = str(thing.get(1))

        if 2 in dict:
            thing = dict.get(2)
            if 0 in thing:
                zero_two = str(thing.get(0))
            if 1 in thing:
                one_two = str(thing.get(1))

        p2 = Message(zero_one,zero_two,one_one,one_two)

        #if you are router A...send it to B over interface 0
        if self.name == 'A':
            i = 0
        #if you are router B...send it to A over interface 1
        if self.name == 'B':
            i = 1

        p = NetworkPacket(0, 'control', p2.to_byte_S())

        try:
            #TODO: add logic to send out a route update
            self.out_intf_L[i].put(p.to_byte_S(), True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        #TODO: print the routes as a two dimensional table for easy inspection
        # Currently the function just prints the route table as a dictionary
        dict = self.rt_tbl_D

        zero_one = '~'
        zero_two = '~'
        one_one = '~'
        one_two = '~'

        if 1 in dict:
            thing=dict.get(1)
            if 0 in thing:
                zero_one = str(thing.get(0))
            if 1 in thing:
                one_one = str(thing.get(1))

        if 2 in dict:
            thing=dict.get(2)
            if 0 in thing:
                zero_two = str(thing.get(0))
            if 1 in thing:
                one_two = str(thing.get(1))

        print('     Cost To:')
        print('         1 2')
        print('        ----')
        print('From: 0| %s %s '%(zero_one, zero_two))
        print('      1| %s %s '%(one_one, one_two))

        ##print(self.rt_tbl_D)


    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
