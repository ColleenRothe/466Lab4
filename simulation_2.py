'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import network
import link
import threading
from time import sleep
import sys

##configuration parameters
router_queue_size = 0  # 0 means unlimited
build_tables_time = 8 # give sim enough time to build tables before send packets between routers
simulation_time = 4  # give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    # create network hosts
    host_one = network.Host(1)
    object_L.append(host_one)
    host_two = network.Host(2)
    object_L.append(host_two)
    host_three = network.Host(3)
    object_L.append(host_three)

    # create routers and routing tables for connected clients (subnets)
    # destination, interface, cost
    router_a_rt_tbl_D = {'1': {0: 1,   1: '~', 2: '~', 3: '~'},
                         '2': {0: '~', 1: '~', 2: '~', 3: 1},
                         '3': {0: '~', 1: '~', 2: '~', 3: '~'},
                         'A': {0: 0,   1: 0,   2: 0,   3: 0},
                         'B': {0: '~', 1: 1,   2: '~', 3: '~'},
                         'C': {0: '~', 1: '~', 2: 2,   3: '~'},
                         'D': {0: '~', 1: '~', 2: '~', 3: '~'}}

    router_b_rt_tbl_D = {'1': {0: '~', 1: '~'},
                         '2': {0: '~', 1: '~'},
                         '3': {0: '~', 1: '~'},
                         'A': {0: 1,   1: '~'},
                         'B': {0: 0,   1: 0},
                         'C': {0: '~', 1: '~'},
                         'D': {0: '~', 1: 2}}

    router_c_rt_tbl_D = {'1': {0: '~', 1: '~'},
                         '2': {0: '~', 1: '~'},
                         '3': {0: '~', 1: '~'},
                         'A': {0: 2,   1: '~'},
                         'B': {0: '~', 1: '~'},
                         'C': {0: 0,   1: 0},
                         'D': {0: '~', 1: 1}}

    router_d_rt_tbl_D = {'1': {0: '~', 1: '~', 2: '~'},
                         '2': {0: '~', 1: '~', 2: '~'},
                         '3': {0: '~', 1: 1,   2: '~'},
                         'A': {0: '~', 1: '~', 2: '~'},
                         'B': {0: 2,   1: '~', 2: '~'},
                         'C': {0: '~', 1: '~', 2: 1},
                         'D': {0: 0,   1: 0,   2: 0}}

    router_a = network.Router(name='A',
                              intf_cost_L=[1, 1, 2, 1],
                              rt_tbl_D=router_a_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_a)

    router_b = network.Router(name='B',
                              intf_cost_L=[1, 2],
                              rt_tbl_D=router_b_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_b)

    router_c = network.Router(name='C',
                              intf_cost_L=[2, 1],
                              rt_tbl_D=router_c_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_c)

    router_d = network.Router(name='D',
                              intf_cost_L=[2, 1, 1],
                              rt_tbl_D=router_d_rt_tbl_D,
                              max_queue_size=router_queue_size)
    object_L.append(router_d)

    # create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    # from intf, to intf
    link_layer.add_link(link.Link(host_one, 0, router_a, 0))
    link_layer.add_link(link.Link(host_two, 0, router_a, 3))
    link_layer.add_link(link.Link(router_a, 1, router_b, 0))
    link_layer.add_link(link.Link(router_a, 2, router_c, 0))
    link_layer.add_link(link.Link(router_b, 1, router_d, 0))
    link_layer.add_link(link.Link(router_c, 1, router_d, 2))
    link_layer.add_link(link.Link(router_d, 1, host_three, 0))

    # start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run))

    for t in thread_L:
        t.start()

    router_a.send_routes(1)  # send routes from A to B
    router_a.send_routes(2)  # send routes from A to C
    router_b.send_routes(0)  # send routes from B to A
    router_b.send_routes(1)  # send routes from B to D
    router_c.send_routes(0)  # send routes from C to A
    router_c.send_routes(1)  # send routes from C to D
    router_d.send_routes(0)  # send routes from D to B
    router_d.send_routes(2)  # send routes from D to C

    # give network suf time to update all routing tables
    sleep(build_tables_time)

    # print the final routing tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network.Router'>":
            obj.print_routes()

    host_one.udt_send(1, 3, 'data', "Nobody expects the Spanish Inquisition")
    sleep(simulation_time)

    host_three.udt_send(3, 1, 'data', "here come dat boi!!!! oh shit waddup!")
    sleep(simulation_time)

    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")



# writes to host periodically
