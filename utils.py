import re

def clean_str(string):
    string = re.sub(
        r"(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)", " ", string)
    string = re.sub(r"[^가-힣A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\.", " . ", string)
    string = re.sub(r"\,", " , ", string)
    string = re.sub(r"\!", " ! ", string)
    string = re.sub(r"\(", " ( ", string)
    string = re.sub(r"\)", " ) ", string)
    string = re.sub(r"\?", " ? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string


def clean_prediction(string):
    string = re.sub(r"\.", ". ", string)
    string = re.sub(r"\,", ", ", string)
    string = re.sub(r"\!", "! ", string)
    string = re.sub(r"\(", " (", string)
    string = re.sub(r"\)", " )", string)
    string = re.sub(r"\?", "? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string
