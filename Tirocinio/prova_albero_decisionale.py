from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, stratify=iris.target, random_state=0)
tree = DecisionTreeClassifier() # max_leaf_nodes: massimo numero di foglie max_depth: profondità massima
                                # min_samples: numero minimo di componenti analizzati nel nodo
                                # min_impurity_decrease: se l'impurità scende troppo poco facendo un nodo figlio non lo fa
                                # questa potatura (pruning) può avvenire prima o dopo la generazione dell'alber (pre e post)
tree.fit(X_train, y_train)

plt.figure(figsize=(10, 8))
plot_tree(tree, feature_names=iris.feature_names, class_names=iris.target_names.tolist(), filled=True)
plt.show()

print(tree.feature_importances_)  # permette di vedere l'importanza che ha rilevato per una feature per classificare
                                    # l'importanza viene data da quanto viene diminuita la sua impurezza paragonando questa feature
