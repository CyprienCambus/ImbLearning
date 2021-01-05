# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Od8MiTQLQxXR_-kFt7VORV6B2_h-qBaN
"""

!pip install imbalanced-learn

import pandas as pd
import numpy as np   
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn import tree
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import multilabel_confusion_matrix
from sklearn import preprocessing as pre
import imblearn
from imblearn.over_sampling import RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RepeatedStratifiedKFold
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings("ignore")

# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/content/drive')
# %cd /content/drive/My\ Drive/Projet_Imbalanced_Learning

creditcard = pd.read_csv('creditcard.csv')
insurance_train = pd.read_csv('aug_train.csv')

# Clean dataset and prepare variables and target

## CREDITCARD
# We first need to drop the variable time which does not bring any information of the CreditCard dataset
creditcard = creditcard.drop(columns=['Time'])
CC_class = creditcard.Class
CC_vars = creditcard.drop(columns=['Class'])

## INSURANCE 
insurance_train = insurance_train.drop(columns=['id'])
insurance_class = insurance_train.Response
insurance_vars = insurance_train.drop(columns=['Response'])
# We need to transform categorical variables onto numerical ones in order to run different models
# We get dummies for Gender and Vehicle_Damage because they are non ordinal variables
insurance_vars = pd.get_dummies(insurance_vars, columns=['Gender', 'Vehicle_Damage'])
# We transform the variable Vehicle_Age (ordinal variable with 3 categories) on the variable taking values in {0,1,2}
oe = pre.OrdinalEncoder()
insurance_vars['Vehicle_Age'] = oe.fit_transform(insurance_vars[['Vehicle_Age']])

## Function that allows to get n splits for the cross validation (and make sure that we have some minority class observations in the test set)

def splits(x, y, n):

    np.random.seed(10)
    res_X_train = []
    res_X_test = []
    res_Y_train = []
    res_Y_test = []
    classes = y.unique()
    idx_class_0, idx_class_1 = y[y==classes[0]].index, y[y==classes[1]].index 
    random_idx_0, random_idx_1 = np.random.choice(len(idx_class_0),len(idx_class_0), replace=False), np.random.choice(len(idx_class_1),len(idx_class_1), replace=False)
    idx_split_0, idx_split_1 = np.array_split(random_idx_0,n), np.array_split(random_idx_1,n)
    
    for j in range(n):
      idx_test = np.concatenate((idx_split_0[j], idx_split_1[j]))
      idx_train = list(set(list(x.index)) - set(idx_test))
      X_train, Y_train = x.iloc[idx_train], y.iloc[idx_train]
      X_test, Y_test = x.iloc[idx_test], y.iloc[idx_test]
      res_X_train.append(X_train)
      res_X_test.append(X_test)
      res_Y_train.append(Y_train)
      res_Y_test.append(Y_test)

    return res_X_train, res_Y_train, res_X_test, res_Y_test

## Function that return mean of respectively f1_score, precision and recall scores of our n test sets + confusion matrix if needed.


# parameters_clf and parameters_oversampling should be dictionnaries of parameters 
# pipelines should be a Pipeline already called
# oversampling_strategy is the name of the oversampling strategy (e.g RandomOverSampler or SMOTE)


def get_f1_scores(x, y, n, split,classifier, parameters_clf, oversampling_strategy = None, parameters_oversampling = None, pipelines = None, confusion_mat = False):

  
  if parameters_oversampling != None:
    oversample = oversampling_strategy(**parameters_oversampling)


  f1_scores = np.zeros(n)
  precision_scores = np.zeros(n)
  recall_scores = np.zeros(n)
  classifier = classifier(**parameters_clf)
  conf_mat = []

  for j in range(n):

    X_train, Y_train = split[0][j], split[1][j] 
    X_test, Y_test = split[2][j], split[3][j]

    if pipelines != None:
      print('->->->->-> split number:'+str(j+1))
      X_over, y_over = pipelines.fit_resample(X_train, Y_train)
      clf = classifier.fit(X_over, y_over)
      pred_over =  clf.predict(X_test) 
      f1_scores[j] = f1_score(Y_test, pred_over)
      precision_scores[j] = (precision_score(Y_test, pred_over))
      recall_scores[j] = (recall_score(Y_test, pred_over))
      conf_mat.append(confusion_matrix(Y_test, pred_over))

    else:

      if oversampling_strategy == None:
        print('->->->->-> split number:'+str(j+1))
        clf = classifier.fit(X_train, Y_train)
        pred = clf.predict(X_test)
        f1_scores[j] = (f1_score(Y_test, pred))
        precision_scores[j] = (precision_score(Y_test, pred))
        recall_scores[j] = (recall_score(Y_test, pred))
        conf_mat.append(confusion_matrix(Y_test, pred))

    
      else:
        print('->->->->-> split number:'+str(j+1))
        X_over, y_over = oversample.fit_resample(X_train, Y_train)
        clf = classifier.fit(X_over, y_over)
        pred_over =  clf.predict(X_test) 
        f1_scores[j] = f1_score(Y_test, pred_over)
        precision_scores[j] = (precision_score(Y_test, pred_over))
        recall_scores[j] = (recall_score(Y_test, pred_over))
        conf_mat.append(confusion_matrix(Y_test, pred_over))

    
      
  if confusion_mat == True:
    return {"f1_score" : f1_scores.mean(), "precision" : precision_scores.mean(), "recall" : recall_scores.mean()}, conf_mat
  else:
    return {"f1_score" : f1_scores.mean(), "precision" : precision_scores.mean(), "recall" : recall_scores.mean()}





# Cross validation with oversampling and without oversampling

"""OVERSAMPLING

For Credit Card dataset
"""

## For Credit Card dataset with RandomForest
SPLITS = splits(CC_vars, CC_class, 5)
X = CC_vars
Y = CC_class
N = 5 
CLASSIFIER = RandomForestClassifier
PARAMETERS_CLF = {'max_depth' : 2, 'random_state' : 42}

# OVERSAMPLING - CREDIT_CARD - F1 score without oversampling 

res_credit_card_no_oversampling = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = minority
OVERSAMPLING_STRATEGY = RandomOverSampler
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 'minority'}

res_credit_card_minority_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = 0.5
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.5}
res_credit_card_ratio_half_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = 0.33
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.33}
res_credit_card_ratio_third_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = 0.15
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.15}
res_credit_card_ratio_fifteen_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = 0.11
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.11}
res_credit_card_ratio_eleven_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# OVERSAMPLING - CREDIT_CARD - With oversample strategy = 0.08
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.08}
res_credit_card_ratio_eight_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# Print results 
print(res_credit_card_no_oversampling)
print(res_credit_card_minority_rf)
print(res_credit_card_ratio_half_rf)
print(res_credit_card_ratio_third_rf)
print(res_credit_card_ratio_fifteen_rf)
print(res_credit_card_ratio_eleven_rf)
print(res_credit_card_ratio_eight_rf)

"""For Insurance dataset """

SPLITS = splits(insurance_vars, insurance_class, 5)
X = insurance_vars
Y = insurance_class
N = 5 
CLASSIFIER = RandomForestClassifier
PARAMETERS_CLF = {'n_estimators' : 150,'random_state' : 42}

# OVERSAMPLING - INSURANCE - F1 score without oversampling 
res_insurance_no_oversampling = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, confusion_mat=True)

# OVERSAMPLING - INSURANCE - With oversample strategy = minority
OVERSAMPLING_STRATEGY = RandomOverSampler
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 'minority'}

res_insurance_minority_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING, confusion_mat = True)

# OVERSAMPLING - INSURANCE - With oversample strategy = 0.5
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.5}
res_insurance_ratio_half_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING, confusion_mat = True)

# OVERSAMPLING - INSURANCE - With oversample strategy = 0.33
PARAMETERS_OVERSAMPLING = {'sampling_strategy' : 0.33}
res_insurance_ratio_third_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING, confusion_mat = True)

# Print results 
print(res_insurance_no_oversampling[0])
print(res_insurance_minority_rf[0])
print(res_insurance_ratio_half_rf[0])
print(res_insurance_ratio_third_rf[0])

"""SMOTE

For Credit card dataset
"""

SPLITS = splits(CC_vars, CC_class, 5)
X = CC_vars
Y = CC_class
N = 5 
CLASSIFIER = RandomForestClassifier
PARAMETERS_CLF = {'max_depth' : 2, 'random_state' : 42}

# SMOTE - CREDIT_CARD - With SMOTE strategy = minority
## With smote using no parameters: By default it creates observations untill we have the same proportion of observations in each class

OVERSAMPLING_STRATEGY = SMOTE

res_credit_card_SMOTE_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# SMOTE - CREDIT_CARD - With SMOTE strategy = 0.1 and Undersampling = 0.5
over = SMOTE(sampling_strategy=0.1)
under = RandomUnderSampler(sampling_strategy=0.5)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_credit_card_SMOTEunder_rf1 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - CREDIT_CARD - With SMOTE strategy = 0.2 and Undersampling = 0.3
over = SMOTE(sampling_strategy=0.2)
under = RandomUnderSampler(sampling_strategy=0.3)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_credit_card_SMOTEunder_rf2 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - CREDIT_CARD - With SMOTE strategy = 0.2 and Undersampling = 0.2
over = SMOTE(sampling_strategy=0.2)
under = RandomUnderSampler(sampling_strategy=0.2)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_credit_card_SMOTEunder_rf3 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - CREDIT_CARD - With SMOTE strategy = 0.18 and Undersampling = 0.19
over = SMOTE(sampling_strategy=0.18)
under = RandomUnderSampler(sampling_strategy=0.19)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_credit_card_SMOTEunder_rf4 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# Print results 
print(res_credit_card_SMOTE_rf)
print(res_credit_card_SMOTEunder_rf1)
print(res_credit_card_SMOTEunder_rf2)
print(res_credit_card_SMOTEunder_rf3)
print(res_credit_card_SMOTEunder_rf4)

"""For Insurance dataset"""

SPLITS = splits(CC_vars, CC_class, 5)
X = insurance_vars
Y = insurance_class
N = 5 
CLASSIFIER = RandomForestClassifier
PARAMETERS_CLF = {'max_depth' : 2, 'random_state' : 42}

# SMOTE - INSURANCE - With SMOTE strategy = minority
OVERSAMPLING_STRATEGY = SMOTE
PARAMETERS_OVERSAMPLING = {"sampling_strategy" : 'minority'}
res_insurance_SMOTE_rf = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, oversampling_strategy=OVERSAMPLING_STRATEGY, parameters_oversampling=PARAMETERS_OVERSAMPLING)

# SMOTE - INSURANCE - With SMOTE strategy = 0.1 and Undersampling = 0.5
over = SMOTE(sampling_strategy=0.1)
under = RandomUnderSampler(sampling_strategy=0.5)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_insurance_SMOTEunder_rf1 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - INSURANCE - With SMOTE strategy = 0.2 and Undersampling = 0.3
over = SMOTE(sampling_strategy=0.2)
under = RandomUnderSampler(sampling_strategy=0.3)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_insurance_SMOTEunder_rf2 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - INSURANCE - With SMOTE strategy = 0.2 and Undersampling = 0.2
over = SMOTE(sampling_strategy=0.2)
under = RandomUnderSampler(sampling_strategy=0.2)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_insurance_SMOTEunder_rf3 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# SMOTE - INSURANCE - With SMOTE strategy = 0.18 and Undersampling = 0.19
over = SMOTE(sampling_strategy=0.18)
under = RandomUnderSampler(sampling_strategy=0.19)
steps = [('o', over), ('u', under)]
PIPELINE = Pipeline(steps=steps)

res_insurance_SMOTEunder_rf4 = get_f1_scores(x=X, y=Y, n=N, split=SPLITS, classifier=CLASSIFIER, parameters_clf=PARAMETERS_CLF, pipelines= PIPELINE)

# Print results 
print(res_insurance_SMOTE_rf)
print(res_insurance_SMOTEunder_rf1)
print(res_insurance_SMOTEunder_rf2)
print(res_insurance_SMOTEunder_rf3)
print(res_insurance_SMOTEunder_rf4)