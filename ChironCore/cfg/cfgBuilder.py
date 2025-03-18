import sys
import networkx as nx
from networkx.drawing.nx_agraph import to_agraph
from cfg.ChironCFG import *
import ChironAST.ChironAST as ChironAST

def buildCFG(ir, cfgName="", isSingle=False):
    startBB = BasicBlock('START')
    endBB = BasicBlock('END')
    leaderIndices = {0, len(ir)}
    leader2IndicesMap = {startBB: 0, endBB: len(ir)}
    indices2LeadersMap = {0: startBB, len(ir): endBB}

    # Finding leaders in the IR
    for idx, item in enumerate(ir):
        if isinstance(item[0], ChironAST.ConditionCommand) or isSingle:
            if idx + 1 < len(ir) and (idx + 1 not in leaderIndices):
                leaderIndices.add(idx + 1)
                thenBranchLeader = BasicBlock(str(idx + 1))
                leader2IndicesMap[thenBranchLeader] = idx + 1
                indices2LeadersMap[idx + 1] = thenBranchLeader

            if idx + item[1] < len(ir) and (idx + item[1] not in leaderIndices):
                leaderIndices.add(idx + item[1])
                elseBranchLeader = BasicBlock(str(idx + item[1]))
                leader2IndicesMap[elseBranchLeader] = idx + item[1]
                indices2LeadersMap[idx + item[1]] = elseBranchLeader

    # Constructing the CFG
    cfg = ChironCFG(cfgName)
    for leader in leader2IndicesMap.keys():
        cfg.add_node(leader)

    # Partitioning IR into basic blocks
    for currLeader in leader2IndicesMap.keys():
        leaderIdx = leader2IndicesMap[currLeader]
        currIdx = leaderIdx
        while currIdx < len(ir):
            currLeader.append((ir[currIdx][0], currIdx))
            currIdx += 1
            if currIdx in leaderIndices:
                break

    # Adding edges between basic blocks
    for node in cfg:
        listSize = len(node.instrlist)
        if listSize:
            irIdx = (node.instrlist[-1])[1]
            lastInstr = (node.instrlist[-1])[0]
            if isinstance(lastInstr, ChironAST.ConditionCommand):
                if not isinstance(lastInstr.cond, ChironAST.BoolFalse):
                    thenIdx = irIdx + 1 if (irIdx + 1 < len(ir)) else len(ir)
                    thenBB = indices2LeadersMap[thenIdx]
                    cfg.add_edge(node, thenBB, label='Cond_True', color='green')

                if not isinstance(lastInstr.cond, ChironAST.BoolTrue):
                    elseIdx = irIdx + ir[irIdx][1] if (irIdx + ir[irIdx][1] < len(ir)) else len(ir)
                    elseBB = indices2LeadersMap[elseIdx]
                    cfg.add_edge(node, elseBB, label='Cond_False', color='red')
            else:
                nextBB = indices2LeadersMap[irIdx + 1] if (irIdx + 1 < len(ir)) else endBB
                cfg.add_edge(node, nextBB, label='flow_edge', color='blue')

    # Convert CFG to SSA form
    cfg = convert_to_ssa(cfg)

    return cfg

def compute_dominators(cfg):
    entry = next(node for node in cfg if node.name == "START")
    dominators = {node: set(cfg.nodes()) for node in cfg}
    dominators[entry] = {entry}
    changed = True
    
    while changed:
        changed = False
        for node in cfg:
            if node == entry:
                continue
            new_doms = set(cfg.nodes())
            for pred in cfg.predecessors(node):
                new_doms &= dominators[pred]
            new_doms.add(node)
            if new_doms != dominators[node]:
                dominators[node] = new_doms
                changed = True
    return dominators

def compute_dominance_frontiers(cfg, dominators):
    df = {node: set() for node in cfg}
    
    for node in cfg:
        if len(set(cfg.predecessors(node))) > 1:
            for pred in cfg.predecessors(node):
                runner = pred
                while runner not in dominators[node]:
                    df[runner].add(node)
                    runner = next(iter(dominators[runner] - {runner}), None)
                    if runner is None:
                        break
    return df

def insert_phi_functions(cfg, df, variables):
    phi_inserted = {var: set() for var in variables}
    worklist = {var: set() for var in variables}
    
    for node in cfg:
        for instr in node.instrlist:
            if isinstance(instr[0], ChironAST.AssignmentCommand):
                var = instr[0].lvar
                if var in variables:
                    worklist[var].add(node)
    
    for var in variables:
        while worklist[var]:
            block = worklist[var].pop()
            for df_node in df[block]:
                if df_node not in phi_inserted[var]:
                    df_node.insert_phi(var)
                    phi_inserted[var].add(df_node)
                    worklist[var].add(df_node)

def convert_to_ssa(cfg):
    dominators = compute_dominators(cfg)
    df = compute_dominance_frontiers(cfg, dominators)
    variables = {instr[0].lvar for node in cfg for instr in node.instrlist if isinstance(instr[0], ChironAST.AssignmentCommand)}
    insert_phi_functions(cfg, df, variables)
    return cfg

def dumpCFG(cfg, filename="out"):
    G = cfg.nxgraph

    # Generating custom labels for graph nodes
    labels = {node: node.label() for node in cfg}

    G = nx.relabel_nodes(G, labels)
    A = to_agraph(G)
    A.layout('dot')
    A.draw(filename + ".png")