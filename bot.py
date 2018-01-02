from __future__ import print_function

import irc.bot
import requests
import tensorflow as tf

import os
import re
import json
import random

from six.moves import cPickle

from model import Model


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        self.msg_count = 0

        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id,
                   'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print(f'Connecting to {server} on port {port}...')
        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port, token)], username, username)

        with open(os.path.join('datasets', 'config.pkl'), 'rb') as f:
            saved_args = cPickle.load(f)
        with open(os.path.join('datasets', 'vocab.pkl'), 'rb') as f:
            self.words, self.vocab = cPickle.load(f)
        self.model = Model(saved_args, True)

        self.twitch_emotes = self.js_r('twitch_global_emotes.json')
        self.custom_emotes = self.js_r('twitch_custom_emotes.json')

    def on_welcome(self, c, e):
        print(f'Joining {self.channel}')

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):

        self.msg_count += 1

        if self.msg_count % 20 == 0:
            self.do_predict(e)

        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            print(f'Received command: {cmd}')
            self.do_command(e, cmd)
        return

    def js_r(self, filename):
        with open(filename) as f_in:
            return(json.load(f_in))

    def clean_str(self, string):
        string = re.sub(r" \(", " ", string)
        string = re.sub(r" \)", " ", string)
        string = re.sub(r" \\\?", "? ", string)
        string = re.sub(r" 's", "'s", string)
        string = re.sub(r" 've", "'ve", string)
        string = re.sub(r" 't", "n't", string)
        string = re.sub(r" 're", "'re", string)
        string = re.sub(r" 'd", "'d", string)
        string = re.sub(r" 'll", "'ll", string)
        string = re.sub(r" n't", "n't", string)
        string = re.sub(r" , ", ", ", string)
        # string = re.sub(r" . ", ". ", string)
        # string = re.sub(r" !", "! ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string

    def do_predict(self, e):
        c = self.connection
        with tf.Session() as sess:
            tf.global_variables_initializer().run()
            saver = tf.train.Saver(tf.global_variables())
            ckpt = tf.train.get_checkpoint_state('datasets')
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)

                output_length = random.randint(3, 10)
                output = self.model.sample(
                    sess, self.words, self.vocab, output_length, ' ', 1, 1, 4)

                print(output)

                for word in output.split():
                    for emote in self.twitch_emotes:
                        if emote.lower() == word:
                            output = str.replace(output, word, emote)
                    for emote in self.custom_emotes:
                        if emote.lower() == word:
                            output = str.replace(output, word, emote)

                final_output = self.clean_str(output)
                c.privmsg(self.channel, final_output)

    def do_command(self, e, cmd):
        c = self.connection

        if cmd == "chatbot":
            message = "/me Using 900,000 chat messages, this chatbot has been trained to emulate a chat user. The model is a RNN trained word-by-word."
            c.privmsg(self.channel, message)


def main():
    username = "d0p3tbot"
    client_id = "saxy6rk8qyaj31s5h2sxkujauwsr7c"
    token = "oauth:k31tvibwb9i8fquqcctxos4wdj81td"
    channel = "serpent_ai"

    bot = TwitchBot(username, client_id, token, channel)
    bot.start()


if __name__ == "__main__":
    main()
