import os
import nltk
import json
import re

import pandas as pd


def refresh_descriptions():
    stocks = os.listdir("../stocks/")
    print(len(stocks))

    ticker_to_description = {}
    for stock in stocks:
        with open(f"../stocks/{stock}", 'r') as f:
            ticker_to_description = dict(ticker_to_description, **json.load(f))

    with open('../stock-descriptions.json', 'w') as f:
        json.dump(ticker_to_description, f)


stopwords = nltk.corpus.stopwords.words('english')
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer('english')


# here I define a tokenizer and stemmer which returns the set of stems in the text that it is passed

def tokenize_and_stem(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


def tokenize_only(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens


with open('../stock-descriptions.json', 'r') as f:
    stocks = json.load(f)

tickers = stocks.keys()
descriptions = stocks.values()

from sklearn.feature_extraction.text import TfidfVectorizer

tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=400, min_df=0.05, stop_words='english', use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1,2))

tfidf_matrix = tfidf_vectorizer.fit_transform(descriptions)
print(tfidf_matrix)

terms = tfidf_vectorizer.get_feature_names_out()
print(terms)

from sklearn.metrics.pairwise import cosine_similarity
dist = 1 - cosine_similarity(tfidf_matrix)
print(dist)

from sklearn.cluster import KMeans



def calculate_WSS(points, kmax):
    sse = []
    for k in range(1, kmax + 1):
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(points)
        centroids = kmeans.cluster_centers_
        pred_clusters = kmeans.predict(points)
        curr_sse = 0

        # calculate square of Euclidean distance of each point from its cluster center and add to current WSS
        for i in range(points.shape[0]):
            curr_center = centroids[pred_clusters[i]]
            curr_sse += (points[i, 0] - curr_center[0]) ** 2 + (points[i, 1] - curr_center[1]) ** 2

        sse.append(curr_sse)
    return sse

import matplotlib.pyplot as plt
import matplotlib as mpl

print(tfidf_matrix.shape)

from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

lsa = make_pipeline(TruncatedSVD(n_components=100), Normalizer(copy=False))
X_lsa = lsa.fit_transform(tfidf_matrix)
explained_variance = lsa[0].explained_variance_ratio_.sum()
print(f"Explained variance: {explained_variance * 100:.1f}%")

kmeans = KMeans(
    n_clusters=23,
    max_iter=100,
    n_init=1
)

# k_max = 40
# plt.plot(range(1, k_max+1), calculate_WSS(X_lsa, k_max))
# plt.show()
#
# from sklearn.metrics import silhouette_score
#
# sil = []
# for k in range(2, k_max+1):
#     kmeans = KMeans(n_clusters=k)
#     kmeans.fit(tfidf_matrix)
#     labels = kmeans.labels_
#     sil.append(silhouette_score(X_lsa, labels, metric='euclidean'))
#
# plt.plot(range(2, k_max+1), sil)
# plt.show()



num_sectors = 23
# km = KMeans(n_clusters=num_sectors)

# km.fit(tfidf_matrix)

kmeans = KMeans(
    n_clusters=num_sectors,
    max_iter=100,
    n_init=50
)

kmeans.fit(tfidf_matrix)

clusters = kmeans.labels_
print(clusters)


stocks = {'ticker': tickers, 'description': descriptions, 'cluster': clusters}
frame = pd.DataFrame(stocks, index=[clusters])

print(frame)

print(frame['cluster'].value_counts())

# not super pythonic, no, not at all.
# use extend so it's a big flat list of vocab
totalvocab_stemmed = []
totalvocab_tokenized = []
for i in descriptions:
    allwords_stemmed = tokenize_and_stem(i)  # for each item in 'synopses', tokenize/stem
    totalvocab_stemmed.extend(allwords_stemmed)  # extend the 'totalvocab_stemmed' list

    allwords_tokenized = tokenize_only(i)
    totalvocab_tokenized.extend(allwords_tokenized)

print("Top terms per cluster:")
print()
# sort cluster centers by proximity to centroid
order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

vocab_frame = pd.DataFrame({'words': totalvocab_tokenized}, index = totalvocab_stemmed)
print('there are ' + str(vocab_frame.shape[0]) + ' items in vocab_frame')

cluster_names = {}
for i in range(num_sectors):
    print("Cluster %d words:" % i, end='')

    cluster_words = []
    for ind in order_centroids[i, :6]:  # replace 6 with n words per cluster
        print(' %s' % vocab_frame.loc[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'), end=',')
        cluster_words.append(str(vocab_frame.loc[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore')))

    cluster_names[i] = ','.join(cluster_words)
    print()  # add whitespace
    print()  # add whitespace

    print("Cluster %d tickers:" % i, end='')
    for title in frame.loc[i]['ticker'].values.tolist():
        print(' %s,' % title, end='')
    print()  # add whitespace
    print()  # add whitespace


from sklearn.manifold import MDS

MDS()

mds = MDS(n_components=2, dissimilarity='precomputed', random_state=1)

pos = mds.fit_transform(dist)

xs, ys = pos[:, 0], pos[:, 1]

df = pd.DataFrame(dict(x=xs, y=ys, label=clusters, title=tickers))
groups = df.groupby('label')

fig, ax = plt.subplots(figsize=(17, 9)) # set size
ax.margins(0.05) # Optional, just adds 5% padding to the autoscaling

# iterate through groups to layer the plot
# note that I use the cluster_name and cluster_color dicts with the 'name' lookup to return the appropriate color/label
for name, group in groups:
    ax.plot(group.x, group.y, marker='o', linestyle='', ms=12,
            label=cluster_names[name],
            mec='none')
    ax.set_aspect('auto')
    ax.tick_params(
        axis='x',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom='off',  # ticks along the bottom edge are off
        top='off',  # ticks along the top edge are off
        labelbottom='off')
    ax.tick_params(
        axis='y',  # changes apply to the y-axis
        which='both',  # both major and minor ticks are affected
        left='off',  # ticks along the bottom edge are off
        top='off',  # ticks along the top edge are off
        labelleft='off')

ax.legend(numpoints=1)  # show legend with only 1 point

# add label in x,y position with the label as the film title
for i in range(len(df)):
    ax.text(df.loc[i]['x'], df.loc[i]['y'], df.loc[i]['title'], size=8)

plt.show()  # show the plot



