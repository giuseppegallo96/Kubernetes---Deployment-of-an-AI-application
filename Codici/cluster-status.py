from kubernetes import client, config
# Carica la configurazione dal file kubeconfig
config.load_kube_config()
# Crea un oggetto API per interagire con il server Kubernetes
v1 = client.CoreV1Api()
# Ottieni la lista dei nodi
nodes = v1.list_node()
# Stampa informazioni sui nodi
for node in nodes.items:
	print(f"Nome nodo: {node.metadata.name}")
	print(f"Status: {node.status.conditions[−1].type}")
	print(f"Versione Kubernetes: {node.status.node_info.kubelet_version}")
	print("−−−−−−")