import os
from time import time

working_dir = '/Users/QiaoLiu1/drug_combin/drug_drug'
# propagation_methods: target_as_1, RWlike
propagation_method = 'RWlike'

activation_method =["relu"]
dropout = [0.2, 0.5, 0.5]
start_lr = 0.03
lr_decay = 0.002
model_type = 'mlp'
FC_layout = [256] * 1 + [64] * 1
n_epochs = 100
batch_size = 256
loss = 'mse'
logfile = os.path.join(working_dir, 'logfile')
NBS_logfile = os.path.join(working_dir, 'NBS_logfile')

synergy_score = os.path.join(working_dir, 'synergy_score', 'combin_data_2.csv')
cl_genes_dp = os.path.join(working_dir, 'cl_gene_dp', 'complete_cl_gene_dp.csv')
#genes_network = '../genes_network/genes_network.csv'
#drugs_profile = '../drugs_profile/drugs_profile.csv'

# networks: string_network, all_tissues_top
network = os.path.join(working_dir, 'network', 'string_network')
network_matrix = os.path.join(working_dir, 'network', 'string_network_matrix.csv')
split_random_seed = 3
index_renewal = False
train_index = os.path.join(working_dir, 'train_index_' + str(split_random_seed))
test_index = os.path.join(working_dir, 'test_index_' + str(split_random_seed))

renew = True
RWlike_simulated_result_matrix = os.path.join(working_dir, 'chemicals', 'normalized_simulated_result_matrix_string.csv')
target_as_1_simulated_result_matrix = os.path.join(working_dir, 'chemicals', 'target_1_simulated_result_matrix_string.csv')
target_as_0_simulated_result_matrix = os.path.join(working_dir, 'chemicals', 'target_0_simulated_result_matrix_string.csv')
gene_expression_simulated_result_matrix = os.path.join(working_dir, 'chemicals', 'gene_expression_simulated_result_matrix_string.csv')
random_walk_simulated_result_matrix = os.path.join(working_dir, 'chemicals', 'random_walk_simulated_result_matrix')
propagated_drug_target = os.path.join(working_dir, 'chemicals', 'propagated_drug_target')


ml_train = False
test_ml_train = True

# estimators: RandomForest, GradientBoosting
estimator = "RandomForest"

if not os.path.exists(os.path.join(working_dir, 'tensorboard_logs')):
    os.mkdir(os.path.join(working_dir, 'tensorboard_logs'))
tensorboard_log = os.path.join(working_dir, "tensorboard_logs/{}".format(time()))

gene_expression_renew = True
expression_data_renew = True
gene_expression = "/Users/QiaoLiu1/microbiome/trial/CCLE.tsv"
backup_expression = "/Users/QiaoLiu1/microbiome/trial/GDSC.tsv"
processed_expression = os.path.join(working_dir, 'processed_expression.csv')


combine_drug_target_renew = True
combine_drug_target_matrix = os.path.join(working_dir, 'chemicals', 'combine_drug_target_matrix.csv')

drug_profiles_renew = True
drug_profiles = os.path.join(working_dir, 'chemicals','drug_profiles.csv')


python_interpreter_path = '/Users/QiaoLiu1/anaconda3/envs/pynbs_env/bin/python'