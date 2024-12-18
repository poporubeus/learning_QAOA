from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import networkx as nx
import qiskit_aer as q_aer
from utilities import execution, invert_counts
from maxcut import *
import numpy as np
from scipy.optimize import minimize
from RandomGraphGeneration import RandomGraph, plot
import matplotlib.pyplot as plt
import sys


shots = 10_000
layers = 8
backend = q_aer.Aer.get_backend("qasm_simulator")


class QAOA:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        pass
    def make_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.graph.number_of_nodes())  
        cr = ClassicalRegister(self.graph.number_of_nodes())
        qc = QuantumCircuit(qr, cr, name="Quantum circuit")
        return qc
    def BetaCircuit(self, beta: float) -> QuantumCircuit:
        qc = self.make_circuit()
        for i in self.graph.nodes():
            qc.rx(theta=2*beta, qubit=i)  # I multiply by 1e-2 to understand which optimized parameters correspond to beta
        return qc
    def GammaCircuit(self, gamma: float) -> QuantumCircuit:
        edges = self.graph.edges()
        qc = self.make_circuit()
        for (i, j) in edges:
            qc.cx(control_qubit=i, target_qubit=j)
            qc.rz(phi=2*gamma, qubit=j) 
            qc.cx(control_qubit=i, target_qubit=j)
        return qc
    def merged_qaoa_circuit(self, gamma_intercept: float, gamma_slope: float, beta_intercept: float, beta_slope: float) -> QuantumCircuit:
        """
        Descript.:
        Combine gamma and beta circuits together in this function.
        For each layers we introduce, we update the value of the parameters beta nd gamma,
        optimizing only 4 parameters instead of 2*p where p is the number of layer.
        The circuit is then composed and qubits are measured and stored into classical bits.

        Params:
        gamma_intercept (float) : gamma intercept component to be optimized;
        gamma_slope (float) : gamma slope component to be optimized;
        beta_intercept (float) : beta intercept component to be optimized;
        beta_slope (float) : beta slope component to be optimized;

        Returns:
        qc (qiskit.QuantumCircuit) : quantum circuit.
        """
        nodes = self.graph.number_of_nodes()
        qc = self.make_circuit()

        beta_linear = np.zeros(layers)
        gamma_linear = np.zeros(layers)
        
        for i in range(layers):
            beta_linear[i] = beta_intercept + beta_slope*i/layers
            gamma_linear[i] = gamma_intercept + gamma_slope*i/layers
        
        qc.h(range(nodes))

        for i in range(layers):
            qc.compose(self.GammaCircuit(gamma_linear[i]), inplace=True)
            qc.barrier()
            qc.compose(self.BetaCircuit(beta_linear[i]), inplace=True)
            qc.barrier() 
        qc.measure(range(nodes), range(nodes))
        return qc


def objective_function(G):
    def f(theta):
        gi, gs, bi, bs = theta
        qaoa = QAOA(graph = G)
        qaoa_circuit = qaoa.merged_qaoa_circuit(gamma_intercept=gi, gamma_slope=gs, beta_intercept=bi, beta_slope=bs)
        counts = execution(circuit=qaoa_circuit, backend=backend, shots=shots)
        return compute_energy(invert_counts(counts=counts), G)
    return f
    #return compute_energy(invert_counts(counts=counts), G)



def solve(graph: nx.Graph, maxiter: int):
    initial_params = 2*np.pi*np.random.rand(4)/180
    sol =  minimize(objective_function(graph), initial_params, method="COBYLA", options={"maxiter": maxiter, "disp": False})
    return sol


def plot_circuit(graph: nx.Graph) -> plt.show:
    set_of_betas_gammas = np.random.rand(4)
    qaoa = QAOA(graph = graph)
    qaoa_circuit = qaoa.merged_qaoa_circuit(gamma_intercept=set_of_betas_gammas[0],
                                            gamma_slope=set_of_betas_gammas[1],
                                            beta_intercept=set_of_betas_gammas[2],
                                            beta_slope=set_of_betas_gammas[3])
    qaoa_circuit.draw("mpl", style="iqx")
    plt.show()
    plt.close()



if __name__ == "__main__":

    if sys.argv[1] == "solution":
        g = RandomGraph(4,0.5,8888)
        sol = solve(graph=g, maxiter=1000)
        print("Solution:", sol)
    
    elif sys.argv[1] == "plot":
        g = RandomGraph(4,0.5,8888)
        plot_circuit(graph=g)

    elif sys.argv[1] == "graph":
        new_graph = RandomGraph(node=int(sys.argv[2]), prob=float(sys.argv[3]), seed=int(sys.argv[4]))
        plot(graph=new_graph)

    else:
        raise ValueError(f'Unknown command: {sys.argv[1]}')