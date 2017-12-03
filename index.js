const tmi = require("tmi.js");
const redis = require("redis");

const config = require("./config");

const options = {
    options: {
        debug: false
    },
    connection: {
        reconnect: true,
        secure: true
    },
    identity: {
        username: config.username,
        password: config.token
    },
    channels: config.channels
};

const twitchClient = new tmi.client(options);

twitchClient.connect().then((data) => {
    console.log(`CONNECTED to Twitch chat on ${data[0]}:${data[1]}`);
}).catch((err) => {
    console.log(`ERROR ${err}`);
});

const redisClient = redis.createClient();

redisClient.on("connect", () => {
    console.log("CONNECTED to redis");
});

twitchClient.on('message', (channel, userstate, message, self) => {
    if (self) return;

    redisClient.sadd("TWITCHCHAT:TEXT", message, (err, reply) => {
        if(err) {
            console.log(err);
        }
    });
});

twitchClient.on('disconnected', (reason) => {
    console.log('DISCONNECTED from Twitch chat');
    console.log(`REASON ${reason}`);
});

twitchClient.on("connected", (address, port) => {
    console.log(`CONNECTED to Twitch chat ${address}:${port}`);
});