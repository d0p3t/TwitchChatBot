from parser import Parser

print("===============================================")
print("TWITCH CHAT BOT - SENTENCE GENERATOR BASED ON TWITCH CHAT DATASET")
print("VERSION 0.0.1")
print("===============================================\n")

DATA_PARSER = Parser(key='TWITCHCHAT:CLEAN', batch_size=64, seq_length=32)
