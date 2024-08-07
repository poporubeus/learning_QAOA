import jax
from jax import numpy as jnp
import pennylane as qml
import networkx as nx
from maxcut import *
import optax
from RandomGraphGeneration import RandomGraph
import time
from qaoa_circuit_utils import GammaCircuit, BetaCircuit
import numpy as np
import pandas as pd
import sys
import warnings
from optimal_params import opt_params, variational_opt_gamma, variational_opt_beta


warnings.filterwarnings("ignore")

jax.config.update("jax_enable_x64", True)

save_path = "/home/fv/storage1/qml/QAOA_transferability/results_CORRECT"
shots = 1024
seed = 40
qubits = int(sys.argv[1])
dev = qml.device("lightning.qubit", wires=qubits, shots=shots)
#dev = qml.device("default.qubit.jax", wires=qubits, shots=shots)

fixed_layers = 3

trainable_params = jnp.array([variational_opt_gamma, variational_opt_beta])


def circuit_qnode(graph, edge):
    @jax.jit
    @qml.qnode(dev, interface="jax")
    def qnode(new_params):
        [qml.Hadamard(wires=i) for i in range(qubits)]
        for l in range(fixed_layers):
            GammaCircuit(opt_params[l, 0], graph)
            BetaCircuit(opt_params[l, 1], qubits)

        # variational block
        GammaCircuit(new_params[0], graph)
        BetaCircuit(new_params[1], qubits)

        if edge is None:
            return qml.counts()
        H = qml.PauliZ(edge[0]) @ qml.PauliZ(edge[1])
        return qml.expval(H)
    result = qnode(trainable_params)
    return result


def circuit_qnode_counts(graph, edge=None) -> qml.counts:
    @qml.qnode(dev, interface="jax")
    def qnode(new_params):
        [qml.Hadamard(wires=i) for i in range(qubits)]
        for l in range(fixed_layers):
            GammaCircuit(opt_params[l, 0], graph)
            BetaCircuit(opt_params[l, 1], qubits)
        # variational block
        GammaCircuit(new_params[0], graph)
        BetaCircuit(new_params[1], qubits)
        return qml.counts()
    result = qnode(trainable_params)
    return result


def qaoa_execution(graph: list, graph_sorgent: nx.Graph) -> tuple:
    @jax.jit
    def obj_function(new_params):
        cost = 0
        for edge in graph:
            cost -= 0.5 * (1 - circuit_qnode(graph, edge=edge))
        return cost

    optax_optmizer = optax.adagrad(learning_rate=0.1)  ### Adagrad
    params = trainable_params
    opt_state = optax_optmizer.init(params)
    steps = 10

    for i in range(steps):
        grads = jax.grad(obj_function)(params)
        updates, opt_state = optax_optmizer.update(grads, opt_state)
        params = optax.apply_updates(params, updates)
        print(f"Iteration {i}:", obj_function(params))

    print("Last parameters updated: ", params)

    counts = circuit_qnode_counts(graph, edge=None)

    min_key, min_energy = maximum_cut(counts, graph_sorgent)
    print("The ground states are: ", min_key, "with energy: ", min_energy)

    most_freq_bit_string = max(counts, key=counts.get)
    res = [int(x) for x in str(most_freq_bit_string)]
    maxcut_val = maxcut_obj(res, graph_sorgent)
    print("Most frequent bit-string is: ", most_freq_bit_string)
    print("The cut value of most frequent bit-string is: ",
          maxcut_val)

    approximation_ratio = jnp.divide(obj_function(params), min_energy)
    print(approximation_ratio)

    return -obj_function(params), counts, params, approximation_ratio


def experiment():
    time_list, opt_beta_gamma_res, energy_res, ar_res, counts_res = [], [], [], [], []
    for s in range(seed):
        print(f"It: {s + 1}")
        graph_generator = RandomGraph(qubits, prob=0.7, seed=s)
        graph = list(graph_generator.edges)
        t0 = time.time()
        energy, counts, opt_beta_gamma, ar = qaoa_execution(graph, graph_generator)
        tf = time.time()
        dt = np.subtract(tf, t0)
        time_list.append(np.asarray(dt))
        energy_res.append(np.asarray(energy))
        opt_beta_gamma_res.append(np.asarray(opt_beta_gamma))
        ar_res.append(np.asarray(ar))
        counts_res.append(counts)
    print("Stop.")
    data = [energy_res, opt_beta_gamma_res, counts_res, ar_res, time_list]
    return data


if __name__ == "__main__":
    data = experiment()
    dataset = pd.DataFrame({'Ground energy': data[0],
                            'Opt_gamma_beta': data[1],
                            'Counts': data[2],
                            'Approx. ratio': data[3],
                            'Elapsed time': data[4]})
    data_seed_ = dataset.to_csv(
        save_path + "/data" + str(seed) + "_qubit" + str(qubits) + ".csv")




