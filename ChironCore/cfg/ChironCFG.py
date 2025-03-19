#!/usr/bin/python3.8

import networkx as nx

class BasicBlock:
    def __init__(self, bbname):  # Corrected method name
        self.name = bbname
        self.instrlist = []
        if bbname == "START" or bbname == "END":
            self.irID = bbname
        else:
            self.irID = int(bbname) - 1

    def __str__(self):  # Corrected method name
        return self.name

    def append(self, instruction):
        self.instrlist.append(instruction)

    def extend(self, instructions):
        self.instrlist.extend(instructions)

    def label(self):
        if len(self.instrlist):
            return '\n'.join(str(instr[0]) + '; L' + str(instr[1]) for instr in self.instrlist)
        else:
            return self.name

    def insert_phi(self, variable, predecessors):
        """ Inserts a φ-function for a given variable at the correct position, dynamically updating instruction indices. """

        print("\nBefore insertion, instrlist:")
        for instr in self.instrlist:
            print(instr, type(instr))

        phi_set = set()
        for instr in self.instrlist:
            if isinstance(instr, tuple) and isinstance(instr[0], str) and "φ" in instr[0]:
                phi_set.add(instr[0])

        print("\nAll existing φ-functions:", phi_set)

        phi_str = f"{variable}=φ({', '.join(map(str, predecessors))})"

        if phi_str not in phi_set:
            phi_set.add(phi_str)
            insert_index = 0

            if self.instrlist:
                first_instr_index = self.instrlist[0][1]
            else:
                first_instr_index = 0

            phi_index = first_instr_index
            self.instrlist.insert(insert_index, (phi_str, phi_index))

            for i in range(1, len(self.instrlist)):
                instr, index = self.instrlist[i]
                self.instrlist[i] = (instr, index + 1)

            print("\nInserted φ-function at index:", phi_index, "->", phi_str)

        print("\nAfter insertion, instrlist:")
        for instr in self.instrlist:
            print(instr, type(instr))


class ChironCFG:
    """An adapter for Networkx.DiGraph."""

    def __init__(self, gname='cfg'):  # Corrected method name
        self.name = gname
        self.nxgraph = nx.DiGraph(name=gname)
        self.entry = "0"
        self.exit = "END"

    def __iter__(self):  # Corrected method name
        return iter(self.nxgraph)

    def is_directed(self):
        return True

    def add_node(self, node):
        if not isinstance(node, BasicBlock):
            raise ValueError("wrong type for 'node' parameter")
        self.nxgraph.add_node(node)

    def has_node(self, node):
        return self.nxgraph.has_node(node)

    def add_edge(self, u, v, **attr):
        if self.has_node(u):
            if self.has_node(v):
                self.nxgraph.add_edge(u, v, **attr)
            else:
                raise NameError(v)
        else:
            raise NameError(u)

    def nodes(self):
        return self.nxgraph.nodes()

    def edges(self):
        return self.nxgraph.edges()

    def successors(self, node):
        return self.nxgraph.successors(node)

    def predecessors(self, node):
        return self.nxgraph.predecessors(node)

    def out_degree(self, node):
        return self.nxgraph.out_degree(node)

    def in_degree(self, node):
        return self.nxgraph.in_degree(node)

    def get_edge_label(self, u, v):
        edata = self.nxgraph.get_edge_data(u, v)
        return edata['label'] if len(edata) else 'T'
