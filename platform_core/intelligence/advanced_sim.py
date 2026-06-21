import math

class Node:
    def __init__(self, name, node_type, baseline_value):
        self.name = name
        self.node_type = node_type  # e.g., 'supply', 'demand', 'revenue', 'cost'
        self.baseline_value = baseline_value
        self.current_value = baseline_value
        self.dependencies = []

    def add_dependency(self, target_node, weight):
        self.dependencies.append({"node": target_node, "weight": weight})

class AdvancedSimulator:
    """
    Elite Business Simulation Engine.
    Handles generic supply-chain, macroeconomic, and organizational shocks.
    """
    def __init__(self):
        self.nodes = {}

    def add_node(self, name, node_type, baseline_value):
        self.nodes[name] = Node(name, node_type, baseline_value)

    def link_nodes(self, source, target, weight):
        """
        Weight indicates how strongly a change in the source affects the target.
        """
        if source in self.nodes and target in self.nodes:
            self.nodes[target].add_dependency(self.nodes[source], weight)

    def apply_shock(self, target_node_name, percent_change):
        """
        Applies a macroeconomic or supply chain shock and calculates
        the cascading effects across the causal graph.
        """
        if target_node_name not in self.nodes:
            return {"error": "Node not found"}

        # 1. Apply primary shock
        primary = self.nodes[target_node_name]
        shock_value = primary.baseline_value * (percent_change / 100.0)
        primary.current_value += shock_value

        # 2. Propagate through dependencies
        # Simple BFS propagation
        queue = [primary]
        visited = set([primary.name])
        
        while queue:
            current = queue.pop(0)
            change_ratio = (current.current_value - current.baseline_value) / current.baseline_value if current.baseline_value != 0 else 0
            
            for node_name, node in self.nodes.items():
                for dep in node.dependencies:
                    if dep["node"].name == current.name:
                        if node.name not in visited:
                            # Apply the weight of the dependency
                            effect = change_ratio * dep["weight"]
                            node.current_value = node.current_value * (1 + effect)
                            visited.add(node.name)
                            queue.append(node)
                            
        # 3. Generate Results
        results = {}
        for name, node in self.nodes.items():
            impact = ((node.current_value - node.baseline_value) / node.baseline_value) * 100 if node.baseline_value != 0 else 0
            results[name] = {
                "baseline": node.baseline_value,
                "simulated": round(node.current_value, 2),
                "impact_percent": round(impact, 2)
            }
            
        return results

if __name__ == "__main__":
    # Test supply chain shock
    sim = AdvancedSimulator()
    sim.add_node("Taiwan Port", "supply", 100)
    sim.add_node("Microchip Inventory", "inventory", 500)
    sim.add_node("Automobile Production", "throughput", 1000)
    sim.add_node("Q3 Revenue", "revenue", 50000)
    
    sim.link_nodes("Taiwan Port", "Microchip Inventory", 0.8)
    sim.link_nodes("Microchip Inventory", "Automobile Production", 0.9)
    sim.link_nodes("Automobile Production", "Q3 Revenue", 1.0)
    
    # Simulate a 50% drop in port capacity
    res = sim.apply_shock("Taiwan Port", -50.0)
    import json
    print(json.dumps(res, indent=2))
