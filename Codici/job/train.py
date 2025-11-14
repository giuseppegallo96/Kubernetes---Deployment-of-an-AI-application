from sklearn import svm
from sklearn import datasets
from joblib import dump, load

clf = svm.SVC()
X, y = datasets.load_iris(return_X_y=True)
clf.fit(X, y)

print ("Model finished training...Hooray")

dump(clf, 'svc_model.model')