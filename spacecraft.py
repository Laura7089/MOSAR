#!/usr/bin/env python3
""" shut up error"""
import operator as op

import jsonpickle as pickler
import networkx as nx
from matplotlib import pyplot as plt


class Spacecraft:
    """A generic spacecraft class that contains a dictionary of modules and connections"""
    def __init__(self, dimensions=2, mod_type=3):
        self.modules = {}
        self._dimensions = dimensions
        self.connections = []
        self.positions = {}
        self.goal = None
        self._mod_type = mod_type

    def add_module(self, new_id):
        """Add an unconnected module to the craft dictionary"""
        if not self.modules:
            self.positions[str(new_id)] = (0, 0)
        self.modules[str(new_id)] = [None]*(self._dimensions*2)

    def add_connected_module(self, a_id, b_id, a_port, b_port):
        """Adds a module that is connected and modifies the existing module to connect it"""
        if not self.modules:
            raise KeyError("There are no existing modules to connect to")

        self.modules[str(a_id)] = [None]*(self._dimensions*2)
        self.connect(a_id, b_id, a_port, b_port)

    def connect(self, mod_a, mod_a_port, mod_b, mod_b_port):
        """Connects the 2 passed modules with the specified ports
        as orientation is going to be considered in future code it takes both ports"""
        mod_a = str(mod_a)
        mod_b = str(mod_b)
        mod_a_port = int(mod_a_port)
        mod_b_port = int(mod_b_port)

        # as orienttation is not yet supported checks that modules are all aligned
        if mod_a_port == mod_b_port and {mod_a_port, mod_b_port} != {0, 2}:
            raise ValueError("Ports must match 0, 2 or 1,3 (orientation is not supported")
        if mod_a_port == mod_b_port and {mod_a_port, mod_b_port} != {1, 3}:
            raise ValueError("Ports must match 0, 2 or 1,3 (orientation is not supported")

        # checks that the ports are not already in use
        try:
            if self.modules[mod_a][mod_a_port] is not None:
                raise ValueError("The port %d on %s is already in use" % (mod_a_port, mod_a))

        except IndexError:
            raise IndexError("Port %d does not exist in this dimension" % (mod_a_port))

        try:
            if self.modules[mod_b][mod_b_port] is not None:
                raise ValueError("The port %d on %s is already in use" % (mod_b_port, mod_b))
        except IndexError:
            raise IndexError("Port %d does not exist in this dimension" % (mod_b_port))

        # give postitions to connected module
        if (mod_a in self.positions) and (mod_b in self.positions):
            if abs(sum(tuple(map(op.sub, self.positions[mod_a], self.positions[mod_b])))) != 1:
                raise KeyError("Modules %s, %s cannot be connected" % (mod_a, mod_b))
        elif mod_a in self.positions:
            self.positions[str(mod_b)] = self._position_get(mod_a, mod_a_port)
        elif mod_b in self.positions:
            self.positions[str(mod_a)] = self._position_get(mod_b, mod_b_port)

        self.modules[mod_a][mod_a_port] = mod_b
        self.modules[mod_b][mod_b_port] = mod_a
        self.connections.append((mod_a, mod_b))

    def connect_all(self, mod_id):
        """give a mod id, checks all adjacent positions and connects module to
        adjancent modules"""
        if mod_id not in self.positions:
            raise IndexError("%s does not have a position so it not yet connected" % (mod_id))

        for i in range(2 * self._dimensions):
            if i % 2 == 0:
                int_diff = 1
            else:
                int_diff = -1
            # get a tuple with +/-1 in one dimension to test free space round root
            difference = [0]*self._dimensions
            difference[i % self._dimensions] = int_diff
            difference = tuple(difference)
            destination = tuple(map(op.add, self.positions[mod_id], difference))
            for key, value in self.positions.items():
                if value == destination and key not in self.modules[mod_id]:
                    if sum(difference) == 1:
                        for i in range(len(difference)):
                            if difference[i] != 0:
                                axis = i
                    else:
                        for i in range(len(difference)):
                            if difference[i] != 0:
                                axis = i + 3
                    axis_to_port = [[2, 1, 4, 0, 3, 5],
                                    [0, 3, 5, 2, 1, 4]]
                    # connect module to chain
                    self.connect(mod_id, axis_to_port[0][axis], key, axis_to_port[1][axis])

    def disconnect(self, mod_id, port_id):
        """takes a module id and port number and disconnects that port"""
        mod_id = str(mod_id)
        port_id = int(port_id)
        if self.modules[mod_id][port_id] is None:
            # will now just accept to allow for bath disconnects
            # raise ValueError("Port %d on module: %s is not connected" % (port_id, mod_id))
            return
        # disconnects port on other module
        self.modules[self.modules[mod_id][port_id]][(port_id+2) % (self._dimensions*2)] = None

        # Removes it from the list of connections
        try:
            self.connections.remove((mod_id, self.modules[mod_id][port_id]))
        except ValueError:
            self.connections.remove((self.modules[mod_id][port_id], mod_id))
        self.modules[mod_id][port_id] = None

    def disconnect_all(self, mod_id):
        """disconnects module from all connections"""
        # add a way to avoid disconnect from arm/tug
        for port_id in range(len(self.modules[mod_id])):
            self.disconnect(mod_id, port_id)
        # remove position for module so it can be repositioned
        del self.positions[mod_id]

    def get_connections(self):
        """outputs all the connections between all the modules"""
        output = ""
        for key in self.modules:
            output += key
            output += str(self.modules[key]) + "\n"
        print(output)

    def _position_get(self, mod_id, port):
        """pass port of unconnected module and id of connected module
        returns position of newly connected module"""
        if port in (0, 2):
            position = tuple(map(op.add, self.positions[mod_id], (port-1, 0)))
        elif port in (1, 3):
            position = tuple(map(op.add, self.positions[mod_id], (0, (port-2)*-1)))
        else:
            print(mod_id, "\t", port)
        return position

    def display(self):
        """displays a graph of the modules"""
        graph = nx.Graph()
        graph.add_nodes_from(self.modules.keys())
        if len(self.connections) != 0:
            graph.add_edges_from(self.connections)
        nx.draw(graph, pos=self.positions, with_labels=True)
        plt.show()

    def get_isolated_mod(self, root):
        """gets unconnected module from root and path from root to it"""

        # uses DFS instead of BFS (change at some point)
        to_visit = [root]
        visited = []
        while len(to_visit) != 0:
            current_node = to_visit[0]
            to_return = True
            if all(x is None for x in self.modules[current_node]):
                return current_node, visited

            for child in self.modules[current_node]:
                if child is not None and child not in visited:
                    to_visit = [child] + [to_visit[1:]]
                    to_return = False

            if to_return is True:
                return current_node, visited
            visited.append(current_node)

    def _get_goal_order(self):
        """return the goal order using bfs"""
        root, dump = self.goal.get_isolated_mod(next(iter(self.goal.modules)))
        to_visit = [root]
        visited = []

        while to_visit:
            current_node = to_visit[0]
            visited.append(current_node)

            for child in self.goal.modules[current_node]:
                # broken?
                if child is not None and child not in to_visit and child not in visited:
                    to_visit.append(child)

            to_visit.pop(0)
        return visited

    def get_path(self, root, goal):
        """pass root mod_id and goal mod_id"""
        to_visit = {root}
        est_cost = {root: 0}
        final_cost = {}
        visited = set()
        back_track = {}
        while to_visit:
            current_node = None
            current_score = None
            for mod in to_visit:
                if current_node is None or est_cost[mod] < current_score:
                    current_node = mod
                    current_score = est_cost[mod]
            # and current_node[-self._mod_type-1] != "-"
            # checks if reached goal
            if current_node == goal:
                path = [current_node]
                while current_node in back_track:
                    current_node = back_track[current_node]
                    path.append(current_node)
                # if goal[-self._mod_type:] == path[0][-self._mod_type:]:
                    # del path[0]
                path.reverse()
                # key = current_node
                # self.goal.modules[key.replace("_", "-")] = self.goal.modules.pop(current_node)
                return path

            to_visit.remove(current_node)
            visited.add(current_node)

            for neighbour in self.goal.modules[current_node]:
                if neighbour in visited:
                    continue
                tmp_cost = est_cost[current_node] + 1
                if neighbour not in to_visit:
                    to_visit.add(neighbour)
                elif tmp_cost >= final_cost[neighbour]:
                    continue
                back_track[neighbour] = current_node
                final_cost[neighbour] = tmp_cost
                est_cost[neighbour] = final_cost[neighbour] + 1

    def import_from_file(self, file_name, goal=True):
        """pass json file to import design (have to redifine craft if importing)"""
        with open(file_name, 'r') as file:
            data = file.read().replace("\n", "")

        if goal is False:
            new_craft = pickler.decode(data)
            try:
                new_craft._mod_type
            except AttributeError:
                new_craft._mod_type = 3
            return new_craft
        else:
            self.goal = pickler.decode(data)

    def export_to_file(self, file_name):
        """export current spacecraft as a json file"""
        write_file = open(file_name+".json", "w")
        write_file.write(pickler.encode(self))

    def melt(self, root=None):
        """Places all modules in a line"""
        # get most extreme module or check passed module
        self.display()
        if root is None:
            root, dump_path = self.get_isolated_mod(next(iter(self.modules)))
        else:
            if root not in self.modules:
                raise ValueError("%s is not a valid module" % (root))
            good_root = False
            for port in self.modules[root]:
                if port is None:
                    good_root = True
            if good_root is False:
                raise ValueError("%s is not a valid root" % (root))

        # find coords of free space next to root
        broke = False
        for i in range(2*self._dimensions):
            if i % 2 == 0:
                int_diff = 1
            else:
                int_diff = -1
            # get a tuple with +/-1 in one dimension to test free space round root
            difference = [0]*self._dimensions
            difference[i % self._dimensions] = int_diff
            difference = tuple(difference)
            destination = sum(tuple(map(op.add, self.positions[root], difference)))
            if destination not in self.positions:
                broke = True
                break
        if broke is False:
            raise ValueError("Did not find a free port around root: %s" % (root))

        # moves all modules into chain
        moved = []
        to_move = set(self.modules.keys())

        while len(to_move) != 0:
            current_node, current_path = self.get_isolated_mod(root)
            print(current_node, " path: ", current_path)
            # the path can be used to get real world coordinates
            # use this to move module (when set up morse)

            # disconnect the module and move it
            self.disconnect_all(current_node)
            self.positions[current_node] = tuple(map(op.add, self.positions[root], difference))
            # get the ports to connect
            if sum(difference) == 1:
                for i in range(len(difference)):
                    if difference[i] != 0:
                        axis = i
            else:
                for i in range(len(difference)):
                    if difference[i] != 0:
                        axis = i + 3
            axis_to_port = [[2, 1, 4, 0, 3, 5],
                            [0, 3, 5, 2, 1, 4]]
            # connect module to chain
            self.connect(current_node, axis_to_port[0][axis], root, axis_to_port[1][axis])
            moved.append(current_node)
            to_move.remove(current_node)
            root = current_node
        return moved

    def sort(self, current_order):
        """sorts the chain of modules"""
        if self.goal is None:
            raise TypeError("goal is not set and therefore cannot be achieved")

        # get order for goal then take only module types
        goal_order = self._get_goal_order()
        goal_order = [elem[-self._mod_type:] for elem in goal_order]

        final_places = {}

        if len(goal_order) != len(current_order):
            # handle this (write later)
            raise ValueError("Goal and spacecraft contain different number of modules")

        tmp_order = current_order.copy()
        # finds where each module type need to be moved
        for pos in range(len(goal_order)):
            try:
                index = [idx for idx, s in enumerate(tmp_order) if goal_order[pos] in s][0]
            except IndexError:
                raise IndexError("%s doesn't exist in craft" % (goal_order[pos]))
            final_places[tmp_order[index]] = pos
            del tmp_order[index]

        # find unoccupied dimension and sets the port to use
        for port_id in range(len(self.modules[current_order[len(current_order)//2]])):
            if self.modules[current_order[len(current_order)//2]][port_id] is not None:
                occupied = port_id
                break
        axis_to_port = [[2, 1, 4, 0, 3, 5],
                        [0, 3, 5, 2, 1, 4]]
        lower_port = axis_to_port[0][(occupied+1) % self._dimensions]

        current_order = [current_order]
        # splits the row in 2
        tmp_order = []
        for i in range(len(current_order[0]) // 2):
            tmp_order.insert(0, current_order[0][i])
            self.disconnect_all(current_order[0][i])
            self.connect(current_order[0][i], lower_port, current_order[0][(-i-1)], axis_to_port[1][lower_port])
            self.connect_all(current_order[0][i])

        current_order.append(tmp_order)
        # removes from of row as it has been moved to below
        del current_order[0][:len(current_order[0])//2]

        # if sub-modules work could replace so arm just turns the modules over
        for sub_list in current_order:
            for i in range(len(sub_list)-1):
                for j in range(0, len(sub_list)-i-1):
                    if final_places[sub_list[j]] > final_places[sub_list[j+1]]:
                        pos1 = self.positions[sub_list[j]]
                        pos2 = self.positions[sub_list[j+1]]
                        self.disconnect_all(sub_list[j+1])
                        self.disconnect_all(sub_list[j])
                        self.positions[sub_list[j]], self.positions[sub_list[j+1]] = pos2, pos1
                        # this will need rewriting for morse
                        # connect_all doesn't seem to work here
                        # self.connect_all(sub_list[j+1])
                        # self.connect_all(sub_list[j])
                        sub_list[j], sub_list[j+1] = sub_list[j+1], sub_list[j]

        # connect structure together
        # implement get_path(start, end) to allow for easy traversal
        for key in self.modules:
            self.connect_all(key)

        # merge sorted rows
        if final_places[current_order[0][0]] < final_places[current_order[1][0]]:
            root = current_order[0][0]
            del current_order[0][0]
        else:
            root = current_order[1][0]
            del current_order[1][0]

        if final_places[current_order[0][-1]] > final_places[current_order[1][-1]]:
            self.disconnect_all(root)
            self.connect(current_order[0][-1], 2, root, 0)
        else:
            self.disconnect_all(root)
            self.connect(current_order[1][-1], 2, root, 0)
        final_order = [root]
        while len(current_order[0]) > 0 and len(current_order[1]) > 0:
            if final_places[current_order[0][0]] < final_places[current_order[1][0]]:
                self.disconnect_all(current_order[0][0])
                self.connect(root, 2, current_order[0][0], 0)
                root = current_order[0][0]
                del current_order[0][0]
                final_order.append(root)
            else:
                self.disconnect_all(current_order[1][0])
                self.connect(root, 2, current_order[1][0], 0)
                root = current_order[1][0]
                del current_order[1][0]
                final_order.append(root)
        for mod in current_order[0]:
            self.disconnect_all(mod)
            self.connect(root, 2, mod, 0)
            root = mod
            final_order.append(root)
        for mod in current_order[1]:
            self.disconnect_all(mod)
            self.connect(root, 2, mod, 0)
            root = mod
            final_order.append(root)
        return final_order

    def grow(self, order):
        """moves the sorted module chain to form the goal structure"""
        print(order)
        print()
        for idx in range(len(order)):
            port_finder = [2, 3, 0, 1, 5, 4]
            mod_type = order[idx][-self._mod_type:]
            path = order[idx+1:]

            if idx == 0:
                self.disconnect_all(order[idx])
                self.connect(order[-1], 2, order[idx], 0)
                # self.goal.modules[order[idx].replace("_", "-")] = self.goal.modules.pop(order[idx])
                # order[idx] = order[idx].replace("_", "-")
                print(path)
                continue

            path = path + self.get_path(order[0], order[idx])
            print(path)
            sucess = False
            last_mod = path[-2]
            for port in range(len(self.goal.modules[last_mod])):
                if self.goal.modules[last_mod][port] is None:
                    continue
                elif self.goal.modules[last_mod][port][-self._mod_type:] == mod_type:
                    self.disconnect_all(order[idx])
                    self.connect(order[idx], port_finder[port], path[-1], port)
                    sucess = True

            self.display()
            if not sucess:
                raise ValueError("Didn't connect the module properly, rewrite it dipshit")
