import gym
import tensorflow as tf
import numpy as np
import random
from collections import deque
import cv2
#HYPER PARAMETERS
ENV_NAME = 'Breakout-v0'
EPISODE = 10000
STEP = 300 #Step limitation in An Epision
GAMMA = 0.9
INITIAL_EPSILON = 0.5
FINAL_EPSILON = 0.01
REPLAY_SIZE = 10000
BATCH_SIZE = 32
TEST = 10

def pre_process(state):
    #make state into an image
    state = cv2.cvtColor(cv2.resize(state,(80,110)),cv2.COLOR_BGR2GRAY)
    state = state[30:110,:]
    ret, state = cv2.threshold(state,1,255,cv2.THRESH_BINARY)
    return np.reshape(state,(80,80,1))

def max_pool_2x2(x):
    return tf.nn.max_pool(x,ksize=[1,2,2,1],strides=[1,2,2,1],padding='SAME')

class DQN():
#DQN Agent
    def __init__(self,env):
        
        self.replay_buffer = deque()
        #init some parameters 
        self.time_step = 0
        self.epsilon = INITIAL_EPSILON
        self.action_dim = env.action_space.n
        self.create_Q_network()
        self.create_training_method()
        #Init session
        self.session = tf.InteractiveSession()
        self.session.run(tf.initialize_all_variables())

    def create_Q_network(self):
        W_conv1 = self.weight_variable([8,8,1,32])
        b_conv1 = self.bias_variable([32])

        W_conv2 = self.weight_variable([4,4,32,64])
        b_conv2 = self.bias_variable([64])

        W_conv3 = self.weight_variable([3,3,64,64])
        b_conv3 = self.bias_variable([64])

        W_fc1 = self.weight_variable([256,self.action_dim])
        b_fc1 = self.bias_variable([self.action_dim])

        #Input Layer
        self.state_input = tf.placeholder("float",shape=[None,80,80,1])

        #Hidden Layers
        h_conv1 = tf.nn.relu(tf.nn.conv2d(input=self.state_input,filter=W_conv1,strides=[1,4,4,1],padding='SAME') + b_conv1)
        h_pool1 = max_pool_2x2(h_conv1)
        h_conv2 = tf.nn.relu(tf.nn.conv2d(h_pool1,W_conv2,strides=[1,2,2,1],padding='SAME') + b_conv2)
        h_pool2 = max_pool_2x2(h_conv2)
        h_conv3 = tf.nn.relu(tf.nn.conv2d(h_pool2,W_conv3,strides=[1,1,1,1],padding='SAME') + b_conv3)
        h_pool3 = max_pool_2x2(h_conv3)
        h_reshape = tf.reshape(h_pool3,[-1,256])
        self.Q_value = tf.matmul(h_reshape,W_fc1) + b_fc1
    def weight_variable(self,shape):
        initial = tf.truncated_normal(shape)
        return tf.truncated_normal(shape)
    def bias_variable(self,shape):
        initial = tf.constant(0.01,shape = shape)
        return tf.Variable(initial)
    def perceive(self,state,action,reward,next_state,done):
        one_hot_action = np.zeros(self.action_dim)
        one_hot_action[action] = 1
        self.replay_buffer.append((state,one_hot_action,reward,next_state,done))
        if len(self.replay_buffer) > REPLAY_SIZE:
            self.replay_buffer.popleft()
        if len(self.replay_buffer) > BATCH_SIZE:
            self.train_Q_network()

    def egreedy_action(self,state):
        Q_value = self.Q_value.eval(feed_dict = {self.state_input:[state]})[0]
        if random.random() <= self.epsilon:
            return random.randint(0,self.action_dim -1)

        else:
            return np.argmax(Q_value)
        self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON)/EPISODE
    
    def action(self,state):
        return np.argmax(self.Q_value.eval(feed_dict={self.state_input:[state]})[0])
    
    def create_training_method(self):
        self.action_input = tf.placeholder("float",[None,self.action_dim])
        self.y_input = tf.placeholder("float",[None])
        Q_action = tf.reduce_sum(tf.multiply(self.Q_value,self.action_input),reduction_indices=1)
        self.cost = tf.reduce_mean(tf.square(self.y_input-Q_action))
        self.optimizer = tf.train.AdamOptimizer(0.0001).minimize(self.cost)

    def train_Q_network(self):
        self.time_step += 1 
        minibatch = random.sample(self.replay_buffer,BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        next_state_batch = [data[3] for data in minibatch]

        y_batch = []
        Q_value_batch = self.Q_value.eval(feed_dict={self.state_input:next_state_batch})
        for i in range(0,BATCH_SIZE):
            done = minibatch[i][4]
            if done:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA*np.max(Q_value_batch[i]))
        self.optimizer.run(feed_dict={self.y_input:y_batch,self.action_input:action_batch,self.state_input:state_batch})

def main():
    env = gym.make(ENV_NAME)
    agent = DQN(env)
    for episode in xrange(EPISODE):
        #initialize task
        state = pre_process(env.reset())
        #train
        for step in xrange(STEP):
            action = agent.egreedy_action(state)
            next_state , reward, done, _ = env.step(action)
            next_state = pre_process(next_state)
            #Define reward for agent
            if done:
                reward -= 1
            else:
                reward += 0.1
            agent.perceive(state,action,reward,next_state,done)
            state = next_state
            env.render()
            if done:
                break;
    writer.close()
if __name__ == '__main__':
    main()