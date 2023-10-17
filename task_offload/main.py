import scipy.io as sio                     # import scipy.io for .mat file I/
import numpy as np                         # import numpy
import MUMT as MU
from memory import MemoryDNN
import time

def plot_gain(gain_his,name=None):
    #display data
    import matplotlib.pyplot as plt
    import pandas as pd
    import matplotlib as mpl
    
    gain_array = np.asarray(gain_his)
    df = pd.DataFrame(gain_his)

    mpl.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(15,8))
    rolling_intv = 60
    df_roll=df.rolling(rolling_intv, min_periods=1).mean()
    if name != None:
        sio.savemat('./data/MUMT(%s)'%name,{'ratio':gain_his})

    plt.plot(np.arange(len(gain_array))+1, df_roll, 'b')
    plt.fill_between(np.arange(len(gain_array))+1, df.rolling(rolling_intv, min_periods=1).min()[0], df.rolling(rolling_intv, min_periods=1).max()[0], color = 'b', alpha = 0.2)
    plt.ylabel('Gain ratio')
    plt.xlabel('learning steps')
    plt.show()

def save_to_txt(gain_his, file_path):
    with open(file_path, 'w') as f:
        for gain in gain_his:
            f.write("%s \n" % gain)

if __name__ == "__main__":
    '''
        This algorithm generates K modes from DNN, and chooses with largest
        reward. The mode with largest reward is stored in the memory, which is
        further used to train the DNN.
    '''
    N = 2000                     # number of channel
    net_num = 3                   # number of DNNs
    WD_num = 3                    # number of WDs in the MERCHANTABILITY
    task_num = 3                  # number of tasks per WD

    # Load data
    task_size = sio.loadmat('./data/MUMT_data_3x3')['task_size']
    gain = sio.loadmat('./data/MUMT_data_3x3')['gain_min']

    # generate the train and test data sample index
    # data are splitted as 80:20
    # training data are randomly sampled with duplication if N > total data size
    split_idx = int(.8* len(task_size))
    num_test = min(len(task_size) - split_idx, N - int(.8* N)) # training data size

    mem = MemoryDNN(net = [WD_num*task_num, 120, 80, WD_num*task_num],
                    net_num=net_num,
                    learning_rate = 0.01,
                    training_interval=10,
                    batch_size=128,
                    memory_size=1024
                    )

    start_time=time.time()

    gain_his = []
    gain_his_ratio = []
    knm_idx_his = []
    m_li=[]
    env = MU.MUMT(3,3,rand_seed=1)
    for i in range(N):
        if i % (N//100) == 0:
           print("----------------------------------------------rate of progress:%0.2f"%(i/N))
        if i < N - num_test:
            #training
            i_idx = i % split_idx
        else:
            # test
            i_idx = i - N + num_test + split_idx
        t1 = task_size[i_idx,:]
        #pretreatment，for better train
        t = t1*10-200


        #produce offloading decision
        m_list = mem.decode(t)
        m_li.append(m_list)
        r_list = []
        for m in m_list:
            r_list.append(env.compute_Q(t1,m))


        # memorize the largest reward and train DNN
        # the train process is included in mem.encode()
        mem.encode(t, m_list[np.argmin(r_list)])

        # record the index of largest reward
        gain_his.append(np.min(r_list))
        knm_idx_his.append(np.argmin(r_list))
        gain_his_ratio.append(gain[0][i_idx]/gain_his[-1])


    total_time=time.time()-start_time
    print('time_cost:%s'%total_time)
    print("gain/max ratio of test: ", sum(gain_his_ratio[-num_test: -1])/num_test)
    print("The number of net: ", net_num)
    mem.plot_cost()
    #cost of DNN
    plot_gain(gain_his_ratio,name=None)
    #draw the ratio of the predicted value to the optimal value
