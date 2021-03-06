 %matplotlib inline

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import nltk
from nltk.corpus import stopwords

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, accuracy_score, f1_score
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import confusion_matrix, roc_auc_score, recall_score, precision_score
from sklearn.model_selection import learning_curve

import pickle
from sklearn.externals import joblib

def tokenize(text): 
    '''
    converts sentences into words list: tokenization
    '''
    return nltk.word_tokenize(text)

def stem(doc):
    return (stemmer.stem(w) for w in analyzer(doc))

def report_results(model, X, y):
    pred_proba = model.predict_proba(X)[:, 1]
    pred = model.predict(X)        
    auc = roc_auc_score(y, pred_proba)
    acc = accuracy_score(y, pred)
    f1 = f1_score(y, pred)
    prec = precision_score(y, pred)
    rec = recall_score(y, pred)
    result = {'auc': auc, 'f1': f1, 'acc': acc, 'precision': prec, 'recall': rec}
    return result
    
def get_roc_curve(model, X, y):
    pred_proba = model.predict_proba(X)[:, 1]
    fpr, tpr, _ = roc_curve(y, pred_proba)
    return fpr, tpr
    
def plot_learning_curve(X, y, train_sizes, train_scores, test_scores, title='', ylim=None, figsize=(14,8)):
    plt.figure(figsize=figsize)
    plt.title(title)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xlabel("Training examples")
    plt.ylabel("Score")

    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    plt.grid()

    plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                     train_scores_mean + train_scores_std, alpha=0.1,
                     color="r")
    plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                     test_scores_mean + test_scores_std, alpha=0.1, color="g")
    plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
             label="Training score")
    plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
             label="Cross-validation score")

    plt.legend(loc="lower right")
    return plt
    
def TrainSVM():
    print("1. Loading Data...")
    data = pd.read_csv("../data/final_data.csv", sep="\t")
    print("2. Train-Test Split")
    train, test = train_test_split(data, test_size=0.3, random_state=1)
    X_train = train['reviewText'].values
    X_test = test['reviewText'].values
    y_train = train['sentiment']
    y_test = test['sentiment']
    # get stop words
    # Review ===> 0, 1

    # Review - X - review Text
    # output -y - 0, 1

    en_stopwords = set(stopwords.words("english"))

    # creating vector from word 
    vectorizer = CountVectorizer(
        analyzer = 'word',
        tokenizer = tokenize,
        lowercase = True,
        ngram_range=(1, 1),
        stop_words = en_stopwords)

    print("3. Performing Cross Validation and GridSearch")
    kfolds = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
    np.random.seed(1)
    pipeline_svm = make_pipeline(vectorizer, 
                                SVC(probability=True, kernel="linear", class_weight="balanced"))

    grid_svm = GridSearchCV(pipeline_svm,
                        param_grid = {'svc__C': [0.01, 0.1, 1]}, 
                        cv = kfolds,
                        scoring="roc_auc",
                        verbose=1,   
                        n_jobs=-1) 

    grid_svm.fit(X_train, y_train)
    grid_svm.score(X_test, y_test)
    print("Saving Model")
    joblib.dump(grid_svm, '../saved_model/model.pkl')
    print("3.1 Best Paramerter and Score")
    print(grid_svm.best_params_)
    print(grid_svm.best_score_)
    print("3.2 Test Results")
    print(report_results(grid_svm.best_estimator_, X_test, y_test))
    roc_svm = get_roc_curve(grid_svm.best_estimator_, X_test, y_test)
    print("4. ROC Curve plot") 
    fpr, tpr = roc_svm
    plt.figure(figsize=(14,8))
    plt.plot(fpr, tpr, color="red")
    plt.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Roc curve')
    plt.show()
    print("5.0 Plotting Learning Curve")
    train_sizes, train_scores, test_scores = \
    learning_curve(grid_svm.best_estimator_, X_train, y_train, cv=5, n_jobs=-1, 
                   scoring="roc_auc", train_sizes=np.linspace(.1, 1.0, 10))
    
    plot_learning_curve(X_train, y_train, train_sizes, 
                    train_scores, test_scores, ylim=(0.7, 1.01), figsize=(14,6))
    plt.show()
if __name__=="__main__":
    print("Calling Main function")
    TrainSVM()
