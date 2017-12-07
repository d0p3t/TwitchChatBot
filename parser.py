import collections
import os
import re
import redis
import numpy as np

from six.moves import cPickle

REDIS = redis.StrictRedis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True)


class Parser():
    def __init__(self, key, data_dir='datasets', batch_size=64, seq_length=32):
        self.redis = REDIS
        self.key = key
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.seq_length = seq_length

        vocab_file = os.path.join(data_dir, "vocab.pkl")
        tensor_file = os.path.join(data_dir, "data.npy")

        count = self.redis.scard(self.key)

        if count is None:
            print("PARSER - NO CHAT MESSAGES FOUND!")
        else:
            print(f"PARSER - TOTAL CHAT MESSAGES: {count}")

            if (os.path.exists(vocab_file) and os.path.exists(tensor_file)) is False:
                self.preprocess(key=key, vocab_file=vocab_file, tensor_file=tensor_file)
            else:
                self.load_preprocessed(vocab_file=vocab_file, tensor_file=tensor_file)
            self.create_batches()
            self.reset_batch_pointer()

            print("PARSER - READY TO TRAIN")

    def preprocess(self, key, vocab_file, tensor_file):
        print("PARSER - PREPROCESSING DATA...")

        messages = self.redis.smembers(key)
        data = ""
        for message in messages:
            data += " " + message

        clean_data = self.clean_str(string=data)
        x_text = clean_data.split()

        self.vocab, self.chars = self.build_vocab(messages=x_text)
        self.vocab_size = len(self.chars)

        with open(vocab_file, 'wb') as filename:
            cPickle.dump(self.chars, filename)

        self.tensor = np.array(list(map(self.vocab.get, x_text)))
        np.save(tensor_file, self.tensor)

        print(f"PARSER - FOUND {self.vocab_size} UNIQUE WORDS")
        print("PARSER - PREPROCESSING DONE")

    def load_preprocessed(self, vocab_file, tensor_file):
        print("PARSER - LOADING PREPROCESSED DATA...")

        with open(vocab_file, 'rb') as filename:
            self.words = cPickle.load(filename)

        self.vocab_size = len(self.words)
        self.vocab = dict(zip(self.words, range(len(self.words))))
        self.tensor = np.load(tensor_file)
        self.num_batches = int(self.tensor.size / (self.batch_size * self.seq_length))

        print(f"PARSER - FOUND {self.vocab_size} UNIQUE WORDS")
        print("PARSER - LOADED PREPROCESSED DATA")

    def build_vocab(self, messages):
        print("PARSER - BUILDING VOCABULARY...")

        word_counts = collections.Counter(messages)

        vocabulary_inv = [x[0] for x in word_counts.most_common()]
        vocabulary_inv = list(sorted(vocabulary_inv))

        vocabulary = {x: i for i, x in enumerate(vocabulary_inv)}

        print("PARSER - BUILDING VOCABULARY DONE")
        return [vocabulary, vocabulary_inv]

    def create_batches(self):
        print("PARSER - CREATING BATCHES...")

        self.num_batches = int(self.tensor.size / (self.batch_size *
                                                   self.seq_length))
        if self.num_batches == 0:
            assert False, "PARSER - NOT ENOUGH DATA. MAKE SEQ_LENGTH AND BATCH_SIZE SMALLER!"

        self.tensor = self.tensor[:self.num_batches *
                                  self.batch_size * self.seq_length]
        xdata = self.tensor
        ydata = np.copy(self.tensor)

        ydata[:-1] = xdata[1:]
        ydata[-1] = xdata[0]
        self.x_batches = np.split(xdata.reshape(
            self.batch_size, -1), self.num_batches, 1)
        self.y_batches = np.split(ydata.reshape(
            self.batch_size, -1), self.num_batches, 1)

        print("PARSER - CREATING BATCHES DONE")

    def next_batch(self):
        x, y = self.x_batches[self.pointer], self.y_batches[self.pointer]
        self.pointer += 1
        return x, y

    def reset_batch_pointer(self):
        self.pointer = 0

    def clean_str(self, string):
        string = re.sub(
            r"(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)", " ", string)
        string = re.sub(r"[^가-힣A-Za-z0-9(),!?\'\`]", " ", string)
        string = re.sub(u'[\u3131-\ucb4c]', " ", string) # Korean Hangul
        string = re.sub(u'[\u1100-\u11ff]', " ", string) # Korean Hangul
        string = re.sub(u'[\uac00-\ud7a3]', " ", string) # Korean Hangul
        string = re.sub(r"\'s", " \'s", string)
        string = re.sub(r"\'ve", " \'ve", string)
        string = re.sub(r"n\'t", " n\'t", string)
        string = re.sub(r"\'re", " \'re", string)
        string = re.sub(r"\'d", " \'d", string)
        string = re.sub(r"\'ll", " \'ll", string)
        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r"\(", " \( ", string)
        string = re.sub(r"\)", " \) ", string)
        string = re.sub(r"\?", " \? ", string)
        string = re.sub(r"\s{2,}", " ", string)

        return string.strip().lower()
