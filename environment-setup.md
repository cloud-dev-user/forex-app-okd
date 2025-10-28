## 🧩 **environment-setup.md**

### **Environment Setup: Integrated Troubleshooting Challenge**

---

### 🧠 Overview

A pre-broken **Forex App** setup for Module 11 – *Integrated Troubleshooting Challenge*.
Each YAML contains intentional issues that participants must troubleshoot.

---

### 📁 Folder Structure

```
forex-challenge/
├── forex-namespace.yaml
├── deployments/
│   ├── currency-service.yaml
│   ├── exchange-rate-service.yaml
│   └── forex-db.yaml
├── network/
│   └── restrictive-networkpolicy.yaml
├── quotas/
│   └── resourcequota.yaml
├── rbac/
│   └── developer-block.yaml
└── README.md
```

---

### 🧩 **File: forex-namespace.yaml**     
*(Make sure to use change namespace name below and in other file references for your forex chanllenge environment)*
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: forex-challenge
```

**Command:**

```bash
oc apply -f forex-namespace.yaml
```

---

### 💥 **File: deployments/currency-service.yaml**

*(Intentional: CrashLoopBackOff due to bad env var)*

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: currency-service
  namespace: forex-challenge
  labels:
    app: currency-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: currency-service
  template:
    metadata:
      labels:
        app: currency-service
    spec:
      containers:
      - name: currency-service
        image: quay.io/openshiftlabs/hello-openshift:v1
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          value: "wrong-db-host"   # Intentional misconfiguration
```

---

### 💥 **File: deployments/exchange-rate-service.yaml**

*(Intentional: Readiness probe failure)*

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: exchange-rate-service
  namespace: forex-challenge
  labels:
    app: exchange-rate-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: exchange-rate-service
  template:
    metadata:
      labels:
        app: exchange-rate-service
    spec:
      containers:
      - name: exchange-rate-service
        image: quay.io/openshiftlabs/hello-openshift:v1
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /wrongpath     # Intentional wrong probe
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

### 💥 **File: deployments/forex-db.yaml**

*(Intentional: PVC mount path incorrect)*

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: forex-db-pvc
  namespace: forex-challenge
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forex-db
  namespace: forex-challenge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: forex-db
  template:
    metadata:
      labels:
        app: forex-db
    spec:
      containers:
      - name: forex-db
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: redhat
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: db-storage
          mountPath: /wrongpath    # Intentional incorrect mount
      volumes:
      - name: db-storage
        persistentVolumeClaim:
          claimName: forex-db-pvc
```

---

### 💥 **File: network/restrictive-networkpolicy.yaml**

*(Intentional: Blocks all ingress to currency-service)*

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-currency-service
  namespace: forex-challenge
spec:
  podSelector:
    matchLabels:
      app: currency-service
  policyTypes:
    - Ingress
  ingress: []
```

---

### 💥 **File: quotas/resourcequota.yaml**

*(Intentional: Too restrictive, causes throttling)*

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: forex-quota
  namespace: forex-challenge
spec:
  hard:
    pods: "1"
    requests.cpu: "150m"
    requests.memory: "128Mi"
    limits.cpu: "200m"
    limits.memory: "256Mi"
```

---

### 💥 **File: rbac/developer-block.yaml**

*(Intentional: Developer user limited to view only)*

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: block-developer
  namespace: forex-challenge
subjects:
- kind: User
  name: developer
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: view
  apiGroup: rbac.authorization.k8s.io
```

---

### 💥 Missing Route

Participants must run:

```bash
oc expose deployment exchange-rate-service --name=exchange-rate-route -n forex-challenge
```

---

### ✅ **Expected  Setup Outcome**

| Component             | Status                     |
| --------------------- | -------------------------- |
| currency-service      | CrashLoopBackOff           |
| exchange-rate-service | Readiness probe fails      |
| currency-service      | Network blocked            |
| exchange-rate-service | Missing route              |
| forex-db              | PVC mount error            |
| Pods                  | Throttled by ResourceQuota |
| Developer             | RBAC restricted            |

---

### 🧭 **Commands**

```bash
oc apply -f forex-namespace.yaml
oc apply -f deployments/forex-db.yaml
oc apply -f deployments/currency-service.yaml
oc apply -f deployments/exchange-rate-service.yaml
oc apply -f network/restrictive-networkpolicy.yaml
oc apply -f quotas/resourcequota.yaml
oc apply -f rbac/developer-block.yaml
oc get pods -n forex-challenge
```


