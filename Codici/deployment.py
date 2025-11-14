from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time

#Caricamento della configurazione del cluster
config.load_kube_config()

# Inizializzazione dei client API
v1 = client.CoreV1Api()
batch_v1 = client.BatchV1Api()

CONFIGMAP_NAME = "classifier-py-configmap"
APP_PATH = "/home/studente/Progetto/prediction_app/prediction-app.py"

pods = v1.list_namespaced_pod('default')
for pod in pods.items:
    print(f"Eliminando pod: {pod.metadata.name} nel namespace {pod.metadata.namespace}")
    v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)

# Controllo il pod
try:
    # Prova a leggere il Pod
    v1.read_namespaced_pod(name="classifier-pod", namespace="default")
    print(f"Il Pod 'classifier-pod' esiste già. Verrà eliminato e ricreato.")
    
    # Elimina il Pod se esiste
    v1.delete_namespaced_pod(name="classifier-pod", namespace="default")
    print(f"Il Pod 'classifier-pod' è stato eliminato.")
    # Aspetta che il pod sia effettivamente eliminato
    """ while True:
        try:
            v1.read_namespaced_pod(name="classifier-pod", namespace="default")
            time.sleep(1)  # Aspetta 1 secondo e riprova
        except ApiException as e:
            if e.status == 404:
                print(f"Il pod è stato eliminato con successo.")
                break """
except ApiException as e:
    if e.status == 404:  # Il Pod non esiste, quindi possiamo crearne uno nuovo
        print(f"Il Pod 'classifier-pod' non esiste. Verrà creato un nuovo Pod.")
    else:
        print(f"Errore durante il controllo del Pod: {e}")


# Verifica se il job esiste già
try:
    # Prova a ottenere il job
    batch_v1.read_namespaced_job(name="ml-training-job", namespace="default")
    print(f"Il job 'ml-training-job' esiste già. Verrà eliminato e rilanciato.")
    
    # Elimina il job se esiste
    batch_v1.delete_namespaced_job(name="ml-training-job", namespace="default")
    print(f"Il job 'ml-training-job' è stato eliminato.")
except ApiException as e:
    if e.status == 404:
        print(f"Il job 'ml-training-job' non esiste. Verrà creato un nuovo job.")
    else:
        print(f"Errore durante il controllo del job: {e}")

# Verifica se la config map esiste già
try:
    v1.read_namespaced_config_map(name=CONFIGMAP_NAME, namespace="default")
    print(f"La ConfigMap 'classifier-py' esiste già. Verrà eliminata e ricreata.")
    v1.delete_namespaced_config_map(name=CONFIGMAP_NAME, namespace="default")
except ApiException as e:
    if e.status == 404:
        print(f"La ConfigMap 'classifier-py' non esiste, verrà creata.")

# Verifica se PV claim esiste
try:
    v1.read_namespaced_persistent_volume_claim(name="ml-data-pvc",namespace="default")
    print(f"Il PersistentVolumeClaim 'ml-data-pvc' esiste già. Verrà eliminato e ricreato.")
    v1.delete_namespaced_persistent_volume_claim(name="ml-data-pvc",namespace="default")
except ApiException as e:
    if e.status == 404:  # Non trovato, possiamo crearlo
        print(f"Il PersistentVolumeClaim 'ml-data-pvc' non esiste, verrà creato.")

# Verifica se PV esiste già
try:
    v1.read_persistent_volume(name="beppe-pv")
    print(f"Il PersistentVolume 'beppe-pv' esiste già. Verrà eliminato e ricreato.")
    v1.delete_persistent_volume(name="beppe-pv")
        # Attendi che il PV venga eliminato
    while True:
        try:
            v1.read_persistent_volume(name="beppe-pv")
            time.sleep(2)  # Aspetta prima di provare di nuovo
        except ApiException as e:
            if e.status == 404:
                print(f"PersistentVolume 'beppe-pv' eliminato con successo.")
                break
except ApiException as e:
    if e.status == 404:  # Non trovato, possiamo crearlo
        print(f"Il PersistentVolume 'beppe-pv' non esiste, lo creeremo.")


# Controlla se il Service esiste
try:
    v1.read_namespaced_service(name="classifier-service", namespace="default")
    print(f"Il service esiste già. Verrà eliminato...")
    
    v1.delete_namespaced_service(name="classifier-service", namespace="default")
    time.sleep(2)  # Aspetta un attimo per garantire l'eliminazione
    print(f"Service eliminato con successo.")
except ApiException as e:
    if e.status == 404:
        print(f"Il service non esiste, procedo con la creazione.")
    else:
        print(f"Errore durante la verifica del Service: {e}")
        exit(1)



# Creazione del Persistent Volume (PV)
pv = client.V1PersistentVolume(
    api_version="v1",
    kind="PersistentVolume",
    metadata=client.V1ObjectMeta(name="beppe-pv"),
    spec=client.V1PersistentVolumeSpec(
        capacity={"storage": "1Gi"},
        access_modes=["ReadWriteOnce"],
        persistent_volume_reclaim_policy="Retain",
        host_path=client.V1HostPathVolumeSource(path="/home/studente/Scrivania")
    )
)

v1.create_persistent_volume(body=pv)
print("Persistent Volume creato.")



# Creazione del Persistent Volume Claim (PVC)
pvc = client.V1PersistentVolumeClaim(
    api_version="v1",
    kind="PersistentVolumeClaim",
    metadata=client.V1ObjectMeta(name="ml-data-pvc"),
    spec=client.V1PersistentVolumeClaimSpec(
        access_modes=["ReadWriteOnce"],
        resources=client.V1ResourceRequirements(
            requests={"storage":"300Mi"}
        )
    )
)

v1.create_namespaced_persistent_volume_claim(namespace="default",body=pvc)
print("Persistent Volume Claim creato.")




# Funzione per la creazione di un Job
job = client.V1Job(
    metadata=client.V1ObjectMeta(name="ml-training-job"),
    spec=client.V1JobSpec(
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app":"ml-training"}),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="trainer",
                        image="localhost:5000/ml-training:latest",
                        command=["python3", "/home/jovyan/train.py"],
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/home/volume",  # Monta il volume in /volume nel container
                                name="beppe-pv",     # Nome del volume
                            )
                        ]
                    )
                ],
                restart_policy="OnFailure",
                volumes=[
                    client.V1Volume(
                        name="beppe-pv",
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name="ml-data-pvc"
                        ),
                    )
                ]
            )
        ),
        backoff_limit=4, # Tentativi massimi di fallimento
    )
)

batch_v1.create_namespaced_job(namespace="default",body=job)



# Creazione della ConfigMap

config_map = client.V1ConfigMap(
    metadata=client.V1ObjectMeta(name=CONFIGMAP_NAME),
    data={"prediction-app.py": open(APP_PATH ).read()}  # Carica il contenuto del file prediction-app.py
)
v1.create_namespaced_config_map(namespace="default", body=config_map)
print("ConfigMap creata.")





# Creazione del Pod che monta ConfigMap e PVC
pod = client.V1Pod(
    metadata=client.V1ObjectMeta(
        name="classifier-pod",
        labels={"app": "classifier-pod"}
        ),
    spec=client.V1PodSpec(
        containers=[
            client.V1Container(
                name="classifier",
                image="jupyter/scipy-notebook:latest",
                command=["sh", "-c", "pip install flask && python3 /app/prediction-app.py"],
                volume_mounts=[
                    client.V1VolumeMount(
                        mount_path="/app",
                        name="config-volume"
                    ),
                    client.V1VolumeMount(
                        mount_path="/home/volume",
                        name="beppe-pv"
                    )
                ]
            )
        ],
        volumes=[
            client.V1Volume(
                name="config-volume",
                config_map=client.V1ConfigMapVolumeSource(name="classifier-py-configmap")
            ),
            client.V1Volume(
                name="beppe-pv",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="ml-data-pvc")
            )
        ],
        restart_policy="Never"
    )
)

v1.create_namespaced_pod(namespace="default", body=pod)
print("Pod creato con successo.")



# Definizione del Service
service = client.V1Service(
    api_version="v1",
    kind="Service",
    metadata=client.V1ObjectMeta(name="classifier-service"),
    spec=client.V1ServiceSpec(
        selector={"app": "classifier-pod"},
        ports=[
            client.V1ServicePort(
                protocol="TCP",
                port=5000,        # Porta del servizio
                target_port=5000, # Porta target del pod
                node_port=30000   # Porta esposta sul nodo
            )
        ],
        type="NodePort"
    )
)

# Creazione del Service nel namespace "default"
v1.create_namespaced_service(namespace="default", body=service)
print("Service creato con successo")
