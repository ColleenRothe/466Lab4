'''
Created on Oct 12, 2016

@author: mwitt_000
'''
from __future__ import print_function
import queue
import threading



## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    def __init__(self, cost=0, maxsize=0):
        self.in_queue = queue.Queue(maxsize);
        self.out_queue = queue.Queue(maxsize);
        self.cost = cost

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                #                 if pkt_S is not None:
                #                     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                #                 if pkt_S is not None:
                #                     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            #             print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            #             print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


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
            raise ('%s: unknown prot_S option: %s' % (self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0: NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[NetworkPacket.dst_addr_S_length: NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise ('%s: unknown prot_S field: %s' % (self, prot_S))
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length:]
        return self(dst_addr, prot_S, data_S)


## Implements a network host for receiving and transmitting data
class Host:
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False  # for thread termination

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        p = NetworkPacket(dst_addr, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out')  # send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return


# You will need to come up with a message that encodes the state of your routing tables.
# My advise would be to come up with a message class that has a to byte S() from byte S() functions.

class Message:
    table_item_length = 1  ##1???
    table_length = 28


    def __init__(self, num_intf, table):
        self.num_intf = num_intf
        self.table = table



    def __str__(self):
        return self.to_byte_S()

    def to_byte_S(self):
        mes = ""
        for x in self.table:
            for y in x:
                mes += str(y).zfill(self.table_item_length)

        byte_S = str(mes).zfill(self.table_length)
        return byte_S

    @classmethod
    def from_byte_S(self, num_intf, byte_S):
        start = 0
        end = self.table_item_length
        table = []
        for i in range(0, 7):
            temp = []
            for j in range(0, num_intf):
                temp.append(str(byte_S[start : end]))
                start += self.table_item_length
                end += self.table_item_length

            table.append(temp)

        return self(num_intf, table)


## Implements a multi-interface router described in class
class Router:
    ##@param name: friendly router name for debugging
    # @param intf_cost_L: outgoing cost of interfaces (and interface number)
    # @param rt_tbl_D: routing table dictionary (starting reachability), eg. {1: {1: 1}} # packet to host 1 through interface 1 for cost 1
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_cost_L, rt_tbl_D, max_queue_size):
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        # note the number of interfaces is set up by out_intf_cost_L
        self.intf_L = []
        for cost in intf_cost_L:
            self.intf_L.append(Interface(cost, max_queue_size))
        # set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D

        ## called when printing the object

    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            # get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            # if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p, i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is (i+1)%2
            self.intf_L[(i + 1) % 2].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, (i + 1) % 2))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        # TODO: add logic to update the routing tables and
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

        # get rid of the first six characters....only want the routing table
        p2 = p.to_byte_S()
        p2 = p2[6: len(p2)]

        ##get the new values from the routing table you got sent

        new_zero_one = p2[0:1]
        new_zero_two = p2[1:2]

        new_one_one = p2[2:3]
        new_one_two = p2[3:4]

        # need to compare what you get with what you have...

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

        self.rt_tbl_D[1] = {0: zero_one, 1: one_one}
        self.rt_tbl_D[2] = {0: zero_two, 1: one_two}

        # print("UPDATE table is", self.rt_tbl_D)


        # need some kind of boolean/loop to keep going until no change
        if send is False:
            if self.name == 'A':
                self.send_routes(1)
            if self.name == 'B':
                self.send_routes(0)


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # a sample route update packet

        table = []
        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            temp = []
            cur = self.rt_tbl_D.get(name)
            for i in range(0, len(self.intf_L)):
                temp.append(cur.get(i))
            table.append(temp)

        p2 = Message(len(self.intf_L), table)

        p = NetworkPacket(0, 'control', p2.to_byte_S())

        try:
            # TODO: add logic to send out a route update
            self.intf_L[i].put(p.to_byte_S(),'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        # TODO: print the routes as a two dimensional table for easy inspection
        # Currently the function just prints the route table as a dictionary
        print("\n     From:  ", end="")
        for i in range(0, len(self.intf_L)):
            print(" ", i, end="")

        print("\n\t    ",end="")
        for i in range(0, len(self.intf_L)):
            print("---", end="")
        print("-", end="")

        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            x = self.rt_tbl_D.get(name)
            if name == 'A':
                print("\nCost To:", name, "|", end="")
            else:
                print("\n\t", name, "|", end="")
            for y in x:
                print(" ", x[y], end="")

        print("\n")


        #print(self.rt_tbl_D)

    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
