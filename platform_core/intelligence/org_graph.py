import networkx as nx

class OrgGraphSimulator:
    """
    Simulates organizational structures and communication bottlenecks.
    Calculates the impact of removing middle-management layers or specific nodes.
    """
    def __init__(self):
        self.G = nx.DiGraph()
        
    def build_from_logs(self, interactions):
        """
        Interactions should be a list of tuples: (Source, Target, Frequency)
        e.g. ("Alice", "Bob", 15)
        """
        for source, target, weight in interactions:
            self.G.add_edge(source, target, weight=weight)
            
    def analyze_bottlenecks(self):
        """
        Identifies the highest betweenness centrality nodes.
        These are the biggest communication bottlenecks.
        """
        if len(self.G.nodes) == 0:
            return []
            
        centrality = nx.betweenness_centrality(self.G, weight='weight')
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes
        
    def simulate_node_removal(self, node_to_remove):
        """
        Removes a node (e.g. restructuring) and calculates the new average shortest path.
        If the path drops significantly, communication efficiency increased!
        """
        if node_to_remove not in self.G:
            return {"error": f"Node {node_to_remove} not in graph."}
            
        try:
            old_path_length = nx.average_shortest_path_length(self.G)
        except nx.NetworkXError:
            old_path_length = float('inf') # Disconnected graph
            
        H = self.G.copy()
        H.remove_node(node_to_remove)
        
        try:
            new_path_length = nx.average_shortest_path_length(H)
        except nx.NetworkXError:
            new_path_length = float('inf')
            
        if old_path_length == float('inf') or new_path_length == float('inf'):
            impact = "Graph became disconnected. Critical node removed!"
        else:
            diff = old_path_length - new_path_length
            if diff > 0:
                impact = f"Efficiency INCREASED. Path length reduced by {round(diff, 2)} steps."
            else:
                impact = f"Efficiency DECREASED. Path length increased by {round(abs(diff), 2)} steps."
                
        return {
            "node_removed": node_to_remove,
            "old_avg_path": round(old_path_length, 2) if old_path_length != float('inf') else "inf",
            "new_avg_path": round(new_path_length, 2) if new_path_length != float('inf') else "inf",
            "impact": impact
        }

if __name__ == "__main__":
    # Test Organization
    sim = OrgGraphSimulator()
    interactions = [
        ("Engineering", "VP Eng", 50),
        ("VP Eng", "CEO", 20),
        ("Sales", "VP Sales", 40),
        ("VP Sales", "CEO", 30),
        ("Marketing", "VP Sales", 15),
        # Direct paths
        ("Engineering", "Sales", 5),
    ]
    sim.build_from_logs(interactions)
    
    print("Top Bottlenecks:")
    for n, c in sim.analyze_bottlenecks():
        print(f"{n}: {round(c, 2)}")
        
    print("\nSimulating Restructuring (Removing 'VP Eng'):")
    res = sim.simulate_node_removal("VP Eng")
    print(res)
