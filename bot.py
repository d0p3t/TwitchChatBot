from __future__ import print_function

import sys
import irc.bot
import requests
import numpy as np
import tensorflow as tf

import argparse
import time
import os
import string
import re
from six.moves import cPickle

from parser import Parser
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

    def on_welcome(self, c, e):
        print(f'Joining {self.channel}')

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):

        self.msg_count += 1

        if self.msg_count % 25 == 0:
            self.do_predict(e)
        # If a chat message starts with an exclamation point, try to run it as a command
        # if e.arguments[0][:1] == '!':
        #     cmd = e.arguments[0].split(' ')[0][1:]
        #     print(f'Received command: {cmd}')
        #     self.do_command(e, cmd)
        return

    def clean_str(self, string):
        string = re.sub(r" 's", "'s", string)
        string = re.sub(r" 've", "'ve", string)
        string = re.sub(r" 't", "n't", string)
        string = re.sub(r" 're", "'re", string)
        string = re.sub(r" 'd", "'d", string)
        string = re.sub(r" 'll", "'ll", string)
        string = re.sub(r" , ", ", ", string)
        string = re.sub(r" . ", ". ", string)
        string = re.sub(r" ! ", "! ", string)
        string = re.sub(r" \( ", " (", string)
        string = re.sub(r" \) ", " )", string)
        string = re.sub(r" \? ", "? ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string

    def do_predict(self, e):
        c = self.connection
        #c.privmsg(self.channel, 'hi there')
        with tf.Session() as sess:
            tf.global_variables_initializer().run()
            saver = tf.train.Saver(tf.global_variables())
            ckpt = tf.train.get_checkpoint_state('datasets')
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)
                output = self.model.sample(sess, self.words, self.vocab, 10, ' ', 1, 2, 4)
                #print(beam)
                print(f"[alpha] {output}")
                for word in output.split():
                    if word == 'kappa':
                        output = string.replace(output, 'kappa', 'Kappa')
                    elif word == 'serpencool':
                        output = string.replace(output, 'serpencool', 'serpenCool')
                    elif word == 'lul':
                        output = string.replace(output, 'lul', 'LUL')
                final_output = self.clean_str(output)
                c.privmsg(self.channel, f"[alpha] {final_output}")

    def do_command(self, e, cmd):
        c = self.connection

        # Poll the API to get current game.
        if cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id,
                       'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['display_name'] +
                      ' is currently playing ' + r['game'])

        # Poll the API the get the current status of the stream
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id,
                       'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['display_name'] +
                      ' channel title is currently ' + r['status'])

        # Provide basic information to viewers for specific commands
        elif cmd == "raffle":
            message = "This is an example bot, replace this text with your raffle text."
            c.privmsg(self.channel, message)
        elif cmd == "schedule":
            message = "This is an example bot, replace this text with your schedule text."
            c.privmsg(self.channel, message)

        # The command was not recognized
        else:
            c.privmsg(self.channel, "Did not understand command: " + cmd)

def main():
    username = "d0p3tbot"
    client_id = "saxy6rk8qyaj31s5h2sxkujauwsr7c"
    token = "oauth:k31tvibwb9i8fquqcctxos4wdj81td"
    channel = "d0p3t"

    bot = TwitchBot(username, client_id, token, channel)
    bot.start()


if __name__ == "__main__":
    main()
