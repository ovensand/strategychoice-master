import numpy as np
import settings
from random import random, randint


def tanh(x):
    return np.tanh(x)


def tanh_prime(x):
    return 1.0 - x ** 2


# Transform two addends into a binary input matrix.
# so for a representation of 3 + 4, it would produce a matrix like:
# (index)    [ 0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 ]
# (matrix)   [ 0 , 0 , 1 , 1 , 1 , 0 , 0 , 0 , 0 , 0 ,  0 ,  1 ,  1 ,  1 ,  0 ]
# these is the matrix that represents the input units to the neural network
# this should be
# (index)    [ 0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 ]
# (matrix)   [ 0 , 0 , 0 , 1 , 0 , 0 , 0 , 0 , 0 , 0 ,  0 ,  0 ,  1 ,  0 ,  0 ]
# in adults, but in kids the symbolic representation is more fuzzy, so they get confused, hence the extra 1's
def addends_matrix(a1, a2):
    lis = [0] * 14
    lis[a1 - 1] = 1
    lis[a1] = 1
    lis[a1 + 1] = 1
    lis[a2 + 6] = 1
    lis[a2 + 7] = 1
    lis[a2 + 8] = 1
    return lis


# Transform the sum into a binary output matrix.
# the output of the neural network, is of length (13 + length of strategies)
# there is a 1 at the index of the sum, so for 1 + 1 = 2 the result is
# (matrix) [ 0 , 0 , 1 , 0 ......]
def sum_matrix(s):
    lis = [0] * (13 + len(settings.strategies))
    lis[s] = 1
    return lis


class NeuralNetwork:
    def __init__(self, layers):

        self.activation = tanh
        self.activation_prime = tanh_prime

        # Set weights

        self.weights = []

        self.y = []
        # range of weight values (-1,1)
        # input and hidden layers - random((2+1, 2+1)) : 3 x 3

        for i in range(1, len(layers) - 1):
            r = 2 * np.random.random((layers[i - 1] + 1, layers[i] + 1)) - 1
            self.weights.append(r)

        # output layer - random((2+1, 1)) : 3 x 1

        r = 2 * np.random.random((layers[i] + 1, layers[i + 1])) - 1
        self.weights.append(r)

        self.X = []
        for i in range(1, 6):
            for j in range(1, 6):
                self.X.append(addends_matrix(i, j))
        self.X = np.array(self.X)

    # the main forward feeding/backpropagation part
    def fit(self, X, y, learning_rate=0.1, epochs=30000):

        # Add column of ones to X
        # This is to add the bias unit to the input layer

        ones = np.atleast_2d(np.ones(X.shape[0]))
        X = np.concatenate((ones.T, X), axis=1)
        for k in range(epochs):

            # if k % (epochs/10) == 0: print 'epochs:', k

            # choose a random training set

            i = np.random.randint(X.shape[0])
            a = [X[i]]
            for l in range(len(self.weights)):
                dot_value = np.dot(a[l], self.weights[l])
                activation = self.activation(dot_value)
                a.append(activation)

            # output layer

            error = y[i] - a[-1]
            deltas = [error * self.activation_prime(a[-1])]

            # we need to begin at the second to last layer 
            # (a layer before the output layer)

            for l in range(len(a) - 2, 0, -1):
                deltas.append(deltas[-1].dot(self.weights[l].T) * self.activation_prime(a[l]))

            # reverse
            # [level3(output)->level2(hidden)]  => [level2(hidden)->level3(output)]

            deltas.reverse()

            # backpropagation
            # 1. Multiply its output delta and input activation 
            #    to get the gradient of the weight.
            # 2. Subtract a ratio (percentage) of the gradient from the weight.

            for i in range(len(self.weights)):
                layer = np.atleast_2d(a[i])
                delta = np.atleast_2d(deltas[i])
                self.weights[i] += learning_rate * layer.T.dot(delta)

    # outputs a matrix given an input matrix, this is used heavily when we want to "know" what is in the kid's mind
    def predict(self, x):
        a = np.concatenate((np.ones(1).T, np.array(x)), axis=1)
        for l in range(0, len(self.weights)):
            a = self.activation(np.dot(a, self.weights[l]))
        return a

    # returns a random number from a list of numbers above the confidence criterion
    # this is used for the retrieval. when we want to try to retrieve a sum,
    # for example 3 + 4 = 7, we pass in a1 = 3, a2 = 4, beg = 0, and end = 13
    # guess loops through [beg,end) to see the values that are above the cc, and chooses
    # a random number from those values. if there are none, it returns none.
    # it does the same thing for when we want to retrieve a strategy, except beg = 13, and end = 13 + len(strategies)
    def guess(self, a1, a2, beg, end, cc):
        if (a1 > 5) or (a2 > 5):
            return (None)
        # trp(1, "Choose confidence criterion = %s" % cc)
        results_above_cc = []
        #
        for i in range(beg, end):
            if self.y[5 * (a1 - 1) + a2 - 1][i] >= cc:
                results_above_cc.append(i)

        l = len(results_above_cc)
        if l > 0:
            return results_above_cc[randint(0, l - 1)]
        return None

    # we change what we fit the neural network to (which is y) after each update
    # the last step of the learning process, the part where y becomes our updated prediction
    def update_y(self):
        self.y = []
        for i in range(1, 6):
            for j in range(1, 6):
                self.y.append(self.predict(addends_matrix(i, j)))

    # check if al + a2 == ans, if so our_ans is correct so we add to that and decrement others.
    # else we add incr_wrong to our_ans in y
    # so this is adding to y, and afterwards we would fit the nn to y, and then update y
    def update(self, a1, a2, our_ans, ans, beg, end):
        # if (a1 > 5) or (a2 > 5) or (our_ans > 10):
        #     # trp(1, "Addends (%s+%s) or result (%s) is/are larger than the memory table limits -- Ignored!" % (
        #     # a1, a2, result))
        index = 5 * (a1 - 1) + (a2 - 1)
        if a1 + a2 == our_ans:
            self.y[index][ans] += settings.INCR_RIGHT
            for i in range(1, 6):
                for j in range(1, 6):
                    for k in range(beg, end):
                        if (i != a1) and (j != a2) and (k != ans):
                            self.y[5 * (i - 1) + (j - 1)][k] -= settings.DECR_WRONG
        else:
            self.y[index][ans] += settings.INCR_WRONG
