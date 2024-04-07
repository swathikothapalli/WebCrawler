import time
import threading
import pandas as pd
from torch.nn import functional as F
import main


class Classifier(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def get_label(self, sentence):

        inputs = main.tokenizer.batch_encode_plus([sentence] + main.conf['labels'],
                                                  return_tensors='pt',
                                                  pad_to_max_length=True)
        ids_inputs = inputs['ids_inputs']
        mask = inputs['mask']
        output = main.model(ids_inputs, mask=mask)[0]
        sentence_rep = output[:1].mean(dim=1)
        label_reps = output[1:].mean(dim=1)

        similarities = F.cosine_similarity(sentence_rep, label_reps)
        nearest = similarities.argsort(descending=True)
        label = f"{main.conf['labels'][nearest[0]]}:{similarities[nearest[0]]},{main.conf['labels'][nearest[1]]}:{similarities[nearest[1]]}"
        return label

    def run(self):
        time.sleep(15)
        while True:
            main.lck.acquire()
            df = pd.read_csv(main.crawled_csv, index_col=False, engine='c')
            for i in range(0, len(df.index)):
                if df.loc[i, 'processed'] == "No":
                    df.loc[i, 'processed'] = 'Yes'

                    sentence = df.loc[i, 'post_text']
                    bert_sentence = ""
                    splited_sentence = sentence.split(' ')
                    if len(splited_sentence) > 200:
                        for word in splited_sentence[0:200]:
                            bert_sentence = bert_sentence + ' ' + word
                        print(f"cut the sentence from {len(splited_sentence)} to {len(bert_sentence.split())}")
                    else:
                        bert_sentence = sentence

                    labels = self.get_label(bert_sentence)

                    df.loc[i, 'label'] = [labels]

                    with open(main.crawled_csv, 'w') as f:
                        df.to_csv(f, index=False)
                    main.lck.release()
                    i = i + 1
                    break
                i = i + 1
                if i == len(df.index) - 1:
                    time.sleep(10)
            time.sleep(0.5)
