## Copyright 2018 Nick Dand
##
## This file is part of psopredict
##
## psopredict is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## psopredict is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with psopredict.  If not, see <https://www.gnu.org/licenses/>.


""" Master script to read parameters file and run machine learning procedure"""


from __future__ import division
import sys
import paramreader, ppscorer
import pandas as pd
import numpy as np
from sklearn.model_selection import (train_test_split, RepeatedStratifiedKFold,
                                     GridSearchCV, StratifiedKFold)
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression


PARAMS_REQD = ['out', 'data', 'target', 'mode', 'model']

if not len(sys.argv) == 2:
    sys.exit('Exiting. Please include parameter file as argument')

## Handle parameters
pr = paramreader.ParamReader(sys.argv[1])
pr.check_params(PARAMS_REQD)
pr.log_params()
pr.interpret_params()
params = pr.get_params()

## Set random seed for reproducible analysis
random_state = np.random.RandomState(params['random_seed'])

## Load data
df = pd.read_hdf(params['data'])
print(df.shape)

X = df.drop(params['target'], axis = 1)
pr.write_to_log('Loaded data comprising ' + str(X.shape[0]) +
                ' records with ' + str(X.shape[1]) + ' features', gap=True)
pr.write_to_log('Preview of predictor data:')
pr.write_to_log(X.iloc[0:5, 0:5], pandas=True, gap=True)

y = df[params['target']]
pr.write_to_log('Preview of outcome data:')
pr.write_to_log(y.iloc[0:5], pandas=True, gap=True)

pr.write_to_log('Removing ' + str(sum(pd.isnull(y))) +
                ' records due to null outcome values', gap=True)
X = X.loc[~pd.isnull(y), :]
y = y.loc[~pd.isnull(y)]

print(X.shape, y.shape)

## Split off test set and ignore
if params['mode'] == 'binary':
    X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size = params['test_pc'], random_state = random_state,
            stratify = y)
elif params['mode'] == 'continuous':
    sys.exit('Exiting. Stratified train/test split for continous outcomes ' +
             'not yet implemented')
else:
    sys.exit('Exiting. "mode" parameter must be one of [binary/continuous]')

## Generate CV indices
#if params['mode'] == 'binary':
#    cv = RepeatedStratifiedKFold(*params['cv_folds'], random_state=random_state)
#    cv_indices = cv.split(X_train, y_train)
#    for fold in cv_indices:
#        print(fold[0][:8])
#        print(fold[1][:8])
#        print('Need some code here to check for stratification')
#else:
#    sys.exit('Exiting. Stratified CV not done for cts outcomes')
#print('Also add code to check the number of times each index is appearing??')

print(X_train.shape, y_train.shape)
print(X_test.shape, y_test.shape)

pps = ppscorer.PPScorer(roc_auc_score)

tmp_cv = StratifiedKFold(params['cv_folds'][0], random_state=random_state)
tmp_clf = GridSearchCV(LogisticRegression(), {'C': [0.1, 1]},
                       cv = tmp_cv, scoring = pps.custom_scorer())
#tmp_clf = GridSearchCV(LogisticRegression(), {'C': [0.1, 1]},
#                       cv = cv, scoring='roc_auc')
print('OK so far')
tmp_clf.fit(X_train, y_train)
print(pps.get_ys()[0])
print('Only showing first element of pps.ys')
print(len(pps.get_ys()))
print(map(lambda x: (len(x[0]), len(x[1])), pps.get_ys()))
print('')
print(tmp_clf.best_params_)
print('')
print('')



## Do some testing - investigate the collecting together code here:
## https://stackoverflow.com/a/49646065

pps2 = ppscorer.PPScorer(roc_auc_score)
tmp_cv2 = StratifiedKFold(3, random_state=random_state)
tmp_clf2 = GridSearchCV(LogisticRegression(), {'C': [0.1]},
                        cv = tmp_cv2, scoring=pps2.custom_scorer())
tmp_clf2.fit(X_train, y_train)
print(map(lambda x: (len(x[0]), len(x[1])), pps2.get_ys()))
print(pps2.get_ys()[0])


