import networkx as nx
def markov_blanket(G, n):
    """Returns the Markov blanket of `n`.

    The Markov blanket consists of the parents of `n`, the children of `n`, and
    any other parents of the children of `n`.

    Parameters
    ----------
    G : DiGraph
        A direct acyclic graph.
    n : node
        A node in `G`.

    Returns
    -------
    blanket : set
        The Markov blanket of `n`.

    Notes
    -----
    The procedure works for any directed graph, but the interpretation of the
    result is valid only when `G` is a DAG.

    """
    blanket = set(G.pred[n])
    children = list(G.succ[n].keys())
    blanket.update(children)
    for child in children:
        blanket.update(G.pred[child])
    return blanket

def moralize(G):
    """Returns the moral graph of `G`.

    The moral graph is an undirected graph where every node in `G` is connected
    to its Markov blanket.

    Parameters
    ----------
    G : DiGraph
        A direct acyclic graph.

    Returns
    -------
    MG : Graph
        The moral graph of `G`.

    """
    MG = nx.Graph()
    for u in G:
        blanket = markov_blanket(G, u)
        MG.add_edges_from([(u, v) for v in blanket if v != u])
    return MG