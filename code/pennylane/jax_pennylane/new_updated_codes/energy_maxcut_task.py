from pandas import read_csv, DataFrame
from numpy import save, asarray, abs, load, loadtxt
from RandomGraphGeneration import RandomGraph
from maxcut import maxcut_obj


prob = 0.6  ## probability of forming a connection between edges
N = 12 ## number of nodes
seed_list = list(range(40)) ### number of seeds (i.e. # of graphs generated)


def energy_maxcut(file: DataFrame) -> tuple[list, list]:
    """
    :param file: (pd.DataFrame) DataFrame generated by the QAOA algorithm we run;
    :return: (tuple) A tuple containing the energy extracted from the approx. ratio and the maxcut value.
    """
    ar_col = file["Approx. ratio"]
    e_qaoa_col = file["Ground energy"]
    counts_col = file["Counts"]  ### these are strings, must converted to dictonaries

    ### approx ratio = energy_qaoa / min_energy

    energy_list, maxcut_list = [], []

    for (i, j) in zip(range(len(ar_col)), range(len(seed_list))):
        theorical_energy_dict = {"Seed": seed_list[j], "Min energy": int(e_qaoa_col[i] / ar_col[i])}
        energy_list.append(theorical_energy_dict)

    for (i, j) in zip(range(len(counts_col)), range(len(seed_list))):

        current_graph = RandomGraph(node=N, prob=prob, seed=seed_list[j])
        counts_dict = eval(counts_col[i])
        max_cut_bitstring = max(counts_dict, key=counts_dict.get)

        max_cut_value = maxcut_obj(max_cut_bitstring, current_graph)

        maxcut_value_dict = {"Seed": seed_list[j], "Max-Cut": abs(max_cut_value)}
        maxcut_list.append(maxcut_value_dict)

    return (energy_list, maxcut_list)


def Load(filename: str) -> list[dict]:
    """
    Load the .npy files created.
    :param filename: (str) Path to the .npy
    :return: (list) A list of extracted dictionaries.
    """
    return load(filename, allow_pickle=True).tolist()



if __name__ == "__main__":

    common_path = "/Users/francescoaldoventurelli/Desktop/QAOA_transferability"

    self_opt_file_12_nodes = common_path + "/results_selfopt/data50_qubit12.csv"
    best_initializ_12_nodes = common_path + "/results_best_initialization/data50_qubit_with_best_initialization_12.csv"
    two_layers_opt_12_nodes = "/Users/francescoaldoventurelli/Desktop/2lys_updated/data50_qubit_2layers_opt_12.csv"


    self_opt_DF_12_nodes = DataFrame(read_csv(self_opt_file_12_nodes))
    best_initializ_DF_12_nodes = DataFrame(read_csv(best_initializ_12_nodes))
    two_layers_opt_DF_12_nodes = DataFrame(read_csv(two_layers_opt_12_nodes))

    en_theorical_selfopt, maxcut_selfopt = energy_maxcut(self_opt_DF_12_nodes)
    en_theorical_best_init, maxcut_best_init = energy_maxcut(best_initializ_DF_12_nodes)
    en_theorical_two_layers, maxcut_two_layers = energy_maxcut(two_layers_opt_DF_12_nodes)

    print("Theoretical energy SELFOPT:", en_theorical_selfopt)
    print("Max-Cut value SELFOPT:", maxcut_selfopt)
    print("")
    print("Theoretical energy BEST INIT:", en_theorical_best_init)
    print("Max-Cut value BEST INIT:", maxcut_best_init)
    print("")
    print("Theoretical energy 2 LAYERS:", en_theorical_two_layers)
    print("Max-Cut value 2 LAYERS:", maxcut_two_layers)


    ### save in .npy format
    save(common_path + "/selfopt_energy_SAVED.npy", asarray(en_theorical_selfopt))
    save(common_path + "/selfopt_maxcut_SAVED.npy", asarray(maxcut_selfopt))
    save(common_path + "/best_init_energy_SAVED.npy", asarray(en_theorical_best_init))
    save(common_path + "/best_init_maxcut_SAVED.npy", asarray(maxcut_best_init))
    save(common_path + "/2layers_energy_SAVED.npy", asarray(en_theorical_two_layers))
    save(common_path + "/2layers_maxcut_SAVED.npy", asarray(maxcut_two_layers))