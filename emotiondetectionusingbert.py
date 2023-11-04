# -*- coding: utf-8 -*-
"""emotiondetectionusingbert.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1c36bJ7hLufGmWcS_zAWoZyWKIhHshXFR
"""

import numpy as np
import pandas as pd

df_train = pd.read_csv('train.txt', header =None, sep =';', names = ['Input','Sentiment'], encoding='utf-8')
df_test = pd.read_csv('test.txt', header = None, sep =';', names = ['Input','Sentiment'],encoding='utf-8')
df_val=pd.read_csv('val.txt',header=None,sep=';',names=['Input','Sentiment'],encoding='utf-8')

##
df=pd.read_csv('emotion_dataset_2.csv')
df.head()

##
df.rename(columns = {'Text':'Input','Emotion':'Sentiment'}, inplace = True)
df.head()

##
df=df.iloc[:,[1,0]]

##
df=df.loc[df['Sentiment'] == 'neutral']

df_full = pd.concat([df_train,df_test,df_val,df], axis = 0)
df_full

!pip install text_hammer
import text_hammer as th

# Commented out IPython magic to ensure Python compatibility.
# %%time
# 
# from tqdm._tqdm_notebook import tqdm_notebook
# tqdm_notebook.pandas()
# 
# def text_preprocessing(df,col_name):
#     column = col_name
#     df[column] = df[column].progress_apply(lambda x:str(x).lower())
#     df[column] = df[column].progress_apply(lambda x: th.cont_exp(x))
#     df[column] = df[column].progress_apply(lambda x: th.remove_emails(x))
#     df[column] = df[column].progress_apply(lambda x: th.remove_html_tags(x))
#     df[column] = df[column].progress_apply(lambda x: th.remove_special_chars(x))
#     df[column] = df[column].progress_apply(lambda x: th.remove_accented_chars(x))
#     return(df)

df_cleaned = text_preprocessing(df_full,'Input')
df_cleaned = df_cleaned.copy()
df_cleaned['num_words'] = df_cleaned.Input.apply(lambda x:len(x.split()))
df_cleaned['Sentiment'] = df_cleaned.Sentiment.astype('category')
df_cleaned.Sentiment
df_cleaned.Sentiment.cat.codes
encoded_dict  = {'anger':0,'fear':1, 'joy':2, 'love':3, 'sadness':4, 'surprise':5, 'neutral':6}
df_cleaned['Sentiment']  =  df_cleaned.Sentiment.cat.codes
df_cleaned.Sentiment
df_cleaned.num_words.max()

from sklearn.model_selection import train_test_split
data_train,data_test = train_test_split(df_cleaned, test_size = 0.3, random_state = 42, stratify = df_cleaned.Sentiment)

data_train.shape

data_train

data_test

data_test.shape

from tensorflow.keras.utils import to_categorical
to_categorical(data_train.Sentiment)

to_categorical(data_test.Sentiment)

pip install transformers

from transformers import AutoTokenizer,TFBertModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-cased')
bert = TFBertModel.from_pretrained('bert-base-cased')
tokenizer.save_pretrained('bert-tokenizer')
bert.save_pretrained('bert-model')

import shutil
shutil.make_archive('bert-tokenizer', 'zip', 'bert-tokenizer')
shutil.make_archive('bert-model','zip','bert-model')
from transformers import BertTokenizer, TFBertModel, BertConfig,TFDistilBertModel,DistilBertTokenizer,DistilBertConfig
dbert_model = TFDistilBertModel.from_pretrained('distilbert-base-uncased')

tokenizer('hello its me')
x_train = tokenizer(
    text=data_train.Input.tolist(),
    add_special_tokens=True,
    max_length=70,
    truncation=True,
    padding=True,
    return_tensors='tf',
    return_token_type_ids = False,
    return_attention_mask = True,
    verbose = True)
x_test = tokenizer(
    text=data_test.Input.tolist(),
    add_special_tokens=True,
    max_length=70,
    truncation=True,
    padding=True,
    return_tensors='tf',
    return_token_type_ids = False,
    return_attention_mask = True,
    verbose = True)

x_test['input_ids']

!pip install tensorflow

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.initializers import TruncatedNormal
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.metrics import CategoricalAccuracy
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
tf.config.experimental.list_physical_devices('GPU')

max_len = 70
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense

input_ids = Input(shape=(max_len,), dtype=tf.int32, name="input_ids")
input_mask = Input(shape=(max_len,), dtype=tf.int32, name="attention_mask")



embeddings = bert(input_ids,attention_mask = input_mask)[0]
out = tf.keras.layers.GlobalMaxPool1D()(embeddings)
out = Dense(128, activation='relu')(out)
out = tf.keras.layers.Dropout(0.1)(out)
out = Dense(32,activation = 'relu')(out)

y = Dense(7,activation = 'sigmoid')(out)

model = tf.keras.Model(inputs=[input_ids, input_mask], outputs=y)
model.layers[2].trainable = True

import tensorflow as tf
from tensorflow.keras.losses import categorical_crossentropy
from keras.optimizers import Adam

learning_rate = 5e-05
epsilon = 1e-08
clipnorm = 1.0


lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate=learning_rate,
    decay_steps=10000,
    decay_rate=0.01
)

optimizer = Adam(learning_rate=lr_schedule, epsilon=epsilon, clipnorm=clipnorm)


optimizer = Adam(
    learning_rate=5e-05,
    epsilon=1e-08,
    decay=0.01,
    clipnorm=1.0)

loss =CategoricalCrossentropy(from_logits = True)
metric = CategoricalAccuracy('balanced_accuracy'),

model.compile(
    optimizer = optimizer,
    loss = loss,
    metrics = metric)

model.summary()
tf.config.experimental_run_functions_eagerly(True)
tf.config.run_functions_eagerly(True)

from keras.callbacks import EarlyStopping, ModelCheckpoint
es = EarlyStopping(monitor = 'val_loss', mode = 'min', verbose = 1, patience = 5)
mc = ModelCheckpoint('./model.h5', monitor = 'val_accuracy', mode = 'max', verbose = 1, save_best_only = True)

import warnings
warnings.filterwarnings('ignore')
train_history = model.fit(
    x ={'input_ids':x_train['input_ids'],'attention_mask':x_train['attention_mask']} ,
    y = to_categorical(data_train.Sentiment),
    validation_data = (
    {'input_ids':x_test['input_ids'],'attention_mask':x_test['attention_mask']}, to_categorical(data_test.Sentiment)
    ),
  epochs=1,
    verbose=1,
    batch_size=36
)

model.save_weights('sentiment_weights.h5')

max_len = 70
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense

input_ids = Input(shape=(max_len,), dtype=tf.int32, name="input_ids")
input_mask = Input(shape=(max_len,), dtype=tf.int32, name="attention_mask")



embeddings = bert(input_ids,attention_mask = input_mask)[0]
out = tf.keras.layers.GlobalMaxPool1D()(embeddings)
out = Dense(128, activation='relu')(out)
out = tf.keras.layers.Dropout(0.1)(out)
out = Dense(32,activation = 'relu')(out)

y = Dense(7,activation = 'sigmoid')(out)

new_model = tf.keras.Model(inputs=[input_ids, input_mask], outputs=y)
new_model.layers[2].trainable = True


new_model.load_weights('sentiment_weights.h5')

predicted_raw = model.predict({'input_ids':x_test['input_ids'],'attention_mask':x_test['attention_mask']})

predicted_raw[0]
y_predicted = np.argmax(predicted_raw, axis = 1)
data_test.Sentiment
from sklearn.metrics import classification_report
print(classification_report(data_test.Sentiment, y_predicted))

texts = input(str('input the text '))

x_val = tokenizer(
    text=texts,
    add_special_tokens=True,
    max_length=70,
    truncation=True,
    padding='max_length',
    return_tensors='tf',
    return_token_type_ids = False,
    return_attention_mask = True,
    verbose = True)
validation = model.predict({'input_ids':x_val['input_ids'],'attention_mask':x_val['attention_mask']})*100
validation
max_value = -1
max_key = None

for key , value in zip(encoded_dict.keys(),validation[0]):
    if value > max_value:
        max_value = value
        max_key = key
print(f"Emotion: {max_key}")

print("All predictions:\n")
for key , value in zip(encoded_dict.keys(),validation[0]):
    print(key,value)

texts = input(str('input the text '))

x_val = tokenizer(
    text=texts,
    add_special_tokens=True,
    max_length=70,
    truncation=True,
    padding='max_length',
    return_tensors='tf',
    return_token_type_ids = False,
    return_attention_mask = True,
    verbose = True)
validation = model.predict({'input_ids':x_val['input_ids'],'attention_mask':x_val['attention_mask']})*100
validation
max_value = -1
max_key = None

for key , value in zip(encoded_dict.keys(),validation[0]):
    if value > max_value:
        max_value = value
        max_key = key
print(f"Emotion: {max_key}")

print("All predictions:\n")
for key , value in zip(encoded_dict.keys(),validation[0]):
    print(key,value)

texts = input(str('input the text '))

x_val = tokenizer(
    text=texts,
    add_special_tokens=True,
    max_length=70,
    truncation=True,
    padding='max_length',
    return_tensors='tf',
    return_token_type_ids = False,
    return_attention_mask = True,
    verbose = True)
validation = model.predict({'input_ids':x_val['input_ids'],'attention_mask':x_val['attention_mask']})*100
validation
max_value = -1
max_key = None

for key , value in zip(encoded_dict.keys(),validation[0]):
    if value > max_value:
        max_value = value
        max_key = key
print(f"Emotion: {max_key}")

print("All predictions:\n")
for key , value in zip(encoded_dict.keys(),validation[0]):
    print(key,value)