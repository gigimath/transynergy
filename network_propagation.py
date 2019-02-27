from scipy.sparse import csr_matrix
import pandas as pd
import numpy as np
import setting
import os
import logging


# Setting up log file
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
fh = logging.FileHandler(setting.NBS_logfile, mode='w+')
fh.setFormatter(fmt=formatter)
logger = logging.getLogger("Drug Combination")
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

def combin_drug_target_probabilities_matrix(drug_pairs, drug_target):


    ### drug_pairs: data frame: drugA, drugB
    ### drug_target: drug_target dataframe, index = genes, columns = drugs
    ### return: combine_drug_target_matrix: index = drugA_drugB, columns = genes
    if not setting.combine_drug_target_renew and os.path.exists(setting.combine_drug_target_matrix):
        combine_drug_target_matrix = pd.read_csv(setting.combine_drug_target_matrix)
        return combine_drug_target_matrix

    if len(drug_pairs.columns) != 2:
        drug_pairs = drug_pairs.iloc[:, :2]
        logger.debug("use first two drug pairs columns as drugA and drugB")
    uniq_drug_pairs = drug_pairs.drop_duplicates()
    uniq_drug_pairs.columns = ['DrugA', 'DrugB']
    final_index = uniq_drug_pairs['DrugA'] + '_' + uniq_drug_pairs['DrugB']
    drug_target = drug_target.T
    logger.debug('Computing for combine drugs target matrix')
    new_drug_target_array = np.bitwise_or(drug_target.loc[uniq_drug_pairs['DrugA'],:].astype(int).values,
                                          drug_target.loc[uniq_drug_pairs['DrugB'],:].astype(int).values)
    combine_drug_target_matrix = pd.DataFrame(new_drug_target_array, index=final_index, columns=drug_target.columns)
    logger.debug('Computed for combine drugs target matrix successfully')
    combine_drug_target_matrix.to_csv(setting.combine_drug_target_matrix)
    return combine_drug_target_matrix


def gene_expression_network_propagation(network, gene_expression_df, genes, drug_target, synergy_df, result_matrix_file):

    ### network: gene-gene network
    ### gene_expression_df: index = genes, columns = cell lines
    ### genes: genes list
    ### gene_expression_df: gene expression data, index = gene, columns = cell lines
    ### drug_pairs: data frame: drugA, drugB
    ### drug_target: drug_target dataframe, index = genes, columns = drugs
    ### return data frame: processed drugs: columns: genes, index: drugs

    # if not setting.gene_expression_renew and os.path.exists(result_matrix_file):
    #     result_df = pd.read_csv(result_matrix_file, index_col = 0)
    #     return result_df

    drug_pairs = synergy_df[['drug_a_name', 'drug_b_name']]
    combine_drug_target_matrix = combin_drug_target_probabilities_matrix(drug_pairs, drug_target)
    logger.debug('Computing for target as 0 propagated data frame')
    if os.path.exists(result_matrix_file):
        processed_drug_target = pd.read_csv(result_matrix_file,index_col=0)
        processed_drug_target = 1-processed_drug_target
    else:
        processed_drug_target = target_as_0_network_propagation(network, combine_drug_target_matrix.T, genes, result_matrix_file)
    logger.debug('Computed for target as 0 propagated data frame successfully')
    processed_drug_target = processed_drug_target.loc[:, gene_expression_df.index]
    assert len(processed_drug_target.columns) == len(gene_expression_df.index), "Processed drug target has different genes number from gene expression dataset"
    result_df = synergy_df.apply(lambda row: processed_drug_target.loc[row['drug_a_name']+'_'+row['drug_b_name'], :] *
                                             gene_expression_df[:, row['cell_line']], axis = 1)
    result_df.to_csv(result_matrix_file)
    return result_df

def target_as_0_network_propagation(network, drug_target, genes, result_matrix_file):

    # input drug_target matrix: index = genes, columns = drugs
    # Set target gene feature for a drug to be 0 and non-target gene to be 1-max(probabilites of all edges)
    # Return dataframe: index = drugs, columns = genes
    return 1-target_as_1_network_propagation(network, drug_target, genes, result_matrix_file)

def target_as_1_network_propagation(network, drug_target, genes, result_matrix_file):

    # input drug_target matrix: index = genes, columns = drugs
    # Set target gene feature for a drug to be 1 and non-target gene to be max(probabilites of all edges)

    # if matrix renewal is needed, it will recompute the simulated result matrix
    if not setting.renew and os.path.exists(result_matrix_file):

        result_matrix = pd.read_csv(result_matrix_file, index_col = 0)

    else:

        # constructed a zero network matrix, columns and index are genes
        network_matrix = get_matrix_from_network(network, genes['entrez'])

        # drug_target_matrix: columns = genes, index = Drugs
        drug_target_matrix = drug_target.loc[genes['entrez'], :].T

        # Set target gene feature for a drug to be 1 and non-target gene to be max(probabilites of all edges)
        logger.debug("compute the max probability intermediate data frame")
        result_matrix = get_max_probability(drug_target_matrix, network_matrix)
        logger.debug("computed the max probability intermediate data frame successfully")
        result_matrix.to_csv(result_matrix_file)

    return result_matrix


def get_max_probability(drug_target, network):

    # input drug_target matrix: columns = genes, index = drugs
    result_drug_target = pd.DataFrame(np.zeros(shape=drug_target.shape), columns=drug_target.columns, index = drug_target.index)
    for gene in result_drug_target.columns:
        logger.debug("processing genes {}".format(str(gene)))
        for drug in result_drug_target.index:
            if drug_target.loc[drug, gene] == 1:
                result_drug_target.loc[drug, gene] = 1
            else:
                result_drug_target.loc[drug, gene] = (drug_target.loc[drug, :] * network.loc[gene, :]).max()

    return result_drug_target

def normalize_matrix(raw_matrix, axis):

    def __normalize(vector):

        denominator = sum(vector)
        if not denominator:
            return vector

        return vector/denominator

    # normalize each row
    normalized_matrix = pd.DataFrame(np.zeros(shape=raw_matrix.shape, dtype='float'), columns=raw_matrix.columns, index=raw_matrix.index)
    if axis == 0 or axis == 'index':

        for i in raw_matrix.index:
            normalized_matrix.loc[i, :] = __normalize(raw_matrix.loc[i, :])

    elif axis == 1 or axis == 'column':

        for i in raw_matrix.columns:
            normalized_matrix.loc[:, i] = __normalize(raw_matrix.loc[:, i])

    else:
        logger.debug("axis is out of range")

    return normalized_matrix

def get_matrix_from_network(network, genes):

    # build the matrix from gene gene interaction network, so far
    # gene-gene self interaction weight is 0
    # output: network_matrix: columns: genes entrezids, index: genes entrezids

    if os.path.exists(setting.network_matrix):
        network_matrix = pd.read_csv(setting.network_matrix, index_col=0)
        network_matrix.index = network_matrix.index.astype(int)
        network_matrix.columns = network_matrix.columns.astype(int)
        return network_matrix

    network_matrix = np.zeros(shape=(len(genes), len(genes)), dtype='float')
    network_matrix = pd.DataFrame(data=network_matrix)
    network_matrix.columns, network_matrix.index = genes, genes
    entrez_set = set(genes)

    for row in network.iterrows():

        a, b = int(row[1]['entrez_a']), int(row[1]['entrez_b'])
        if a in entrez_set and b in entrez_set:
            network_matrix.loc[a, b] = row[1]['association']
            network_matrix.loc[b, a] = row[1]['association']

    network_matrix.to_csv(setting.network_matrix)
    return network_matrix

def RWlike_network_propagation(network, drug_target, genes, result_matrix_file):

    # input drug_target matrix: index = genes, columns = drugs
    if not setting.renew and os.path.exists(result_matrix_file):

        result_matrix = pd.read_csv(result_matrix_file, index_col = 0)

    else:

        # build the matrix from gene gene interaction network, so far
        # gene-gene self interaction weight is 0
        network_matrix = get_matrix_from_network(network, genes['entrez'])

        # Normalize gene gene association probability so that the total gene gene
        # association probability weights for one gene is 1
        normalized_network_matrix = normalize_matrix(network_matrix, 0)
        network_sparse_matrix = csr_matrix(normalized_network_matrix.values)

        # drug_target_matrix: columns = genes, index = Drugs
        drug_target_matrix = drug_target.loc[genes['entrez'], :].values.T

        # result_matrix: columns = genes, index = Drugs
        result_matrix = (csr_matrix(drug_target_matrix).dot(network_sparse_matrix)).todense()

        # Set target genes effect to be 1, because it is 1 in drug_target_matrix and all non-target genes
        # effect is less than 1 since the sum of all weights for a gene is 1
        result_matrix = np.array([result_matrix, drug_target_matrix]).max(axis = 0)
        result_matrix = pd.DataFrame(result_matrix, columns=genes['entrez'], index=drug_target.columns)
        result_matrix.to_csv(result_matrix_file)

    return result_matrix

def random_walk_network_propagation(result_matrix_file):

    import subprocess
    import sys
    # input drug_target matrix: index = genes, columns = drugs
    if setting.renew or not os.path.exists(result_matrix_file):

        ### set up correct python_interpreter
        python_interpreter_path = setting.python_interpreter_path
        try:
            bash_command = python_interpreter_path + " " + os.path.join(os.getcwd(), 'network_propagation.py')
            logger.debug("Executing {!r}".format(bash_command))
            retcode = subprocess.call(bash_command, shell=True)
            if retcode < 0:
                logger.debug("Subprocess was terminated by signal {!r}".format(-retcode))
            else:
                logger.debug("Subprocess returned {!r}".format(retcode))
        except OSError as e:
            logger.debug("Execution failed: {!r}".format(e))

    result_matrix = pd.read_csv(result_matrix_file, index_col=0)
    return result_matrix


def pyNBS_random_walk():


    from pyNBS import network_propagation as NBS_propagation
    import setting
    import networkx as nx

    # build the matrix from gene gene interaction network, so far
    # gene-gene self interaction weight is 0
    network = nx.read_edgelist(setting.network, delimiter='\t', nodetype=int,
                               data=(('weight', float),))
    drug_target = pd.read_csv(setting.drug_profiles, index_col=0)
    subnetwork = network.subgraph(list(drug_target.index))

    ### Compute precoputed kernel to speed up random walk
    subnetwork_nodes = subnetwork.nodes()
    I = pd.DataFrame(np.identity(len(subnetwork_nodes)), index=subnetwork_nodes, columns=subnetwork_nodes)
    logger.debug("Preparing network propagation kernel")
    print("Preparing network propagation kernel")
    kernel = NBS_propagation.network_propagation(subnetwork, I, alpha=0.5, symmetric_norm=False, verbose=True)
    logger.debug("Got network propagation kernel. Start propagate ...")
    print("Got network propagation kernel. Start propagate ...")
    propagated_drug_target = NBS_propagation.network_kernel_propagation(network=subnetwork, network_kernel=kernel,
                                                         binary_matrix=drug_target.T)
    logger.debug("Propagation finished")
    print("Propagation finished")
    propagated_drug_target.to_csv(setting.propagated_drug_target)

if __name__ == '__main__':

    pyNBS_random_walk()
