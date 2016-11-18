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
    src_addr_S_length = 5
    dst_addr_S_length = 5
    prot_S_length = 1

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, src_addr, dst_addr, prot_S, data_S):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        elif self.prot_S == 'reply':
            byte_S += '3'
        else:
            raise ('%s: unknown prot_S option: %s' % (self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        src_addr = int(byte_S[0: NetworkPacket.src_addr_S_length])
        dst_addr = int(byte_S[NetworkPacket.src_addr_S_length : NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length: NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        elif prot_S == '3':
            prot_S = 'reply'
        else:
            raise ('%s: unknown prot_S field: %s' % (self, prot_S))
        data_S = byte_S[NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length:]
        return self(src_addr, dst_addr, prot_S, data_S)


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
    def udt_send(self, src_addr, dst_addr, prot_S, data_S):
        p = NetworkPacket(src_addr, dst_addr, prot_S, data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out')  # send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            p = NetworkPacket.from_byte_S(pkt_S)
            if p.prot_S == 'data':
                print('%s: received packet "%s"' % (self, pkt_S))
                message = "Reply to: " + p.data_S
                p2 = NetworkPacket(p.dst_addr, p.src_addr, 'reply', message)
                print('%s: sending a reply packet "%s" to Router %s' % (self, message, p.src_addr))
                self.udt_send(self.addr, p.src_addr, 'reply', p2.to_byte_S())
            elif p.prot_S == 'control':
                print('%s: received packet "%s"' % (self, pkt_S))
            elif p.prot_S == 'reply':
                print('%s: reply received packet "%s"' % (self, pkt_S))
            else:
                raise Exception('%s: Unknown packet type in packet %s' % (self, p))


    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


# You will need to come up with a message that encodes the state of your routing tables.
# My advise would be to come up with a message class that has a to byte S() from byte S() functions.

class Message:
    num_intf_length = 1
    route_length = 1
    table_item_length = 1
    message_length = 30

    def __init__(self, route_from, num_intf, table):
        self.route_from = route_from
        self.num_intf = num_intf
        self.table = table

    def __str__(self):
        return self.to_byte_S()

    def to_byte_S(self):
        mes = ""
        mes += str(self.route_from).zfill(self.route_length)
        mes += str(self.num_intf).zfill(self.num_intf_length)
        for x in self.table:
            for y in x:
                mes += str(y).zfill(self.table_item_length)

        byte_S =  str(mes).zfill(self.message_length)
        return byte_S

    @classmethod
    def from_byte_S(self, byte_S):
        route_from = str(byte_S[0: self.route_length])
        num_intf = int(byte_S[self.route_length : self.route_length + self.num_intf_length])
        start = self.route_length + self.num_intf_length
        end = self.route_length + self.num_intf_length + self.table_item_length
        table = []
        for i in range(7):
            temp = []
            for j in range(num_intf):
                cost = str(byte_S[start: end])
                if cost is not '~':
                    cost = int(cost)
                temp.append(cost)
                start += self.table_item_length
                end += self.table_item_length

            table.append(temp)

        return self(route_from, num_intf, table)


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
        self.n_intf = len(self.intf_L)

        ## called when printing the object

    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(self.n_intf):
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
                elif p.prot_S == 'reply':
                    self.forward_packet(p, i)
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
            if self.n_intf == 2:
                self.intf_L[(i + 1) % 2].put(p.to_byte_S(), 'out', True)
            else:
                col = self.rt_tbl_D.get(str(p.dst_addr))
                poss_routes = []
                shortest_route = 100
                for j in col:
                    if col[j] is not '~' and int(col[j]) < shortest_route:
                        if len(poss_routes) is 0:
                            shortest_route = int(col[j])
                            poss_routes.append(j)
                        else:
                            poss_routes.clear()
                            shortest_route = int(col[j])
                            poss_routes.append(j)
                    elif col[j] is not '~' and int(col[j]) == shortest_route:
                        poss_routes.append(j)
                if len(poss_routes) == 1:
                    self.intf_L[poss_routes[0]].put(p.to_byte_S(), 'out', True)
                elif len(poss_routes) > 1:
                    routes = []
                    col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
                    for k in poss_routes:
                        for blah in col_nam:
                            if blah is self.name:
                                continue
                            col = self.rt_tbl_D.get(blah)
                            if col[k] is not '~' and int(col[k]) < shortest_route:
                                if len(routes) is 0:
                                    shortest_route = int(col[k])
                                    routes.append(k)
                                else:
                                    routes.clear()
                                    shortest_route = int(col[k])
                                    routes.append(k)
                            elif col[k] is not '~' and int(col[k]) == shortest_route:
                                routes.append(k)
                    #print("routes: ", routes)
                    if len(routes) == 1:
                        self.intf_L[routes[0]].put(p.to_byte_S(), 'out', True)
                    else:
                        print('SOMETHING WENT WRONG MATE 1')
                else:
                    print('SOMETHING WENT WRONG MATE 2')

            #self.intf_L[(i + 1) % 2].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, (i + 1) % 2))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        print('%s: Received routing update %s' % (self, p))
        send = False
        # get rid of the first six characters....only want the routing table
        p2 = p.to_byte_S()
        p2 = p2[11: len(p2)]
        # get rid of all the excess zeros
        i = 0
        for a in p2:
            if a == '0':
                i += 1
                continue
            else:
                break
        p2 = p2[i: len(p2)]
        # convert this byte_S to a table
        mes = Message.from_byte_S(p2)
        route = str(mes.route_from)
        # find what interfaces and costs to get from self to route
        col_to = self.rt_tbl_D[route]
        cost_to = []
        for q in col_to:
            cost_to.append(col_to[q])

        for row in range(self.n_intf):
            a = cost_to[row]
            if a is '~':
                continue
            else:
                route_table = list(mes.table)
                col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
                col = 0
                for x in route_table:
                    for y in x:
                        # add cost to values from route_table
                        if y is not "~":
                            y = int(y) + int(a)
                            cur_col = self.rt_tbl_D.get(col_nam[col])
                            cur_val = cur_col.get(row)
                            if cur_val is not '~':
                                cur_val= int(cur_val)
                                if cur_val > y:
                                    self.rt_tbl_D[col_nam[col]][row] = y
                                    send = True
                            else:
                                self.rt_tbl_D[col_nam[col]][row] = y
                                send = True
                    col += 1

        # print("UPDATE table is", self.rt_tbl_D)

        # need some kind of boolean/loop to keep going until no change
        if send is True:
            if self.name == 'A':
                self.send_routes(1) # send routes to B
                self.send_routes(2) # send routes to C
            if self.name == 'B':
                self.send_routes(0) # send routes to A
                self.send_routes(1) # send routes to D
            if self.name == 'C':
                self.send_routes(0) # send routes to A
                self.send_routes(1) # send routes to D
            if self.name == 'D':
                self.send_routes(0) # send routes to B
                self.send_routes(2) # send routes to C

    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        table = []
        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            temp = []
            cur = self.rt_tbl_D.get(name)
            for j in range(self.n_intf):
                temp.append(cur.get(j))
            table.append(temp)

        p2 = Message(self.name, self.n_intf, table)

        p = NetworkPacket(0, 0, 'control', p2.to_byte_S())

        try:
            # TODO: add logic to send out a route update
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        num = 11 + self.n_intf * 3
        if num % 2 != 0:
            num += 1
        for i in range(num):
            if i == num/2:
                print("COST", end="")
            else:
                print("-", end="")

        print("-\nFrom Interface:", end="")
        for i in range(self.n_intf):
            print(" ", i, end="")

        print("\n\t       -", end="")
        for i in range(self.n_intf):
            print("---", end="")

        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            x = self.rt_tbl_D.get(name)
            if name == '1':
                print("\nTo Host:   ", name, "|", end="")
            elif name == 'A':
                    print("\nTo Router: ", name, "|", end="")
            #elif name == 'B':
            #    print("   Cost\n\t   ", name, "|", end="")
            else:
                print("\n\t   ", name, "|", end="")
            for y in x:
                print(" ", x[y], end="")

        print("\n")#\t\tCost\n")


    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return
