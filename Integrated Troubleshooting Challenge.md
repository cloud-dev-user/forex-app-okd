
1. **Environment setup: Integrated Troubleshooting Challenge** — instructor setup guide (broken app setup).
2. **Integrated Troubleshooting Challenge – Hands-On Lab** — participant lab challenge (troubleshooting tasks).

Below are both documents rewritten in **GitHub-friendly Markdown (MD)** format so you can add them directly to your repo as:

```
/docs/
 ├── environment-setup.md
 └── troubleshooting-challenge.md
```

---

# 🧩 environment-setup.md

### **Environment Setup: Integrated Troubleshooting Challenge**

*(Instructor Guide – SSK Training & Consulting)*

---

### 🧠 Overview

A pre-broken **Forex App** setup used for Module 11 – *Integrated Troubleshooting Challenge*.

This setup intentionally introduces multiple issues for participants to diagnose and fix.

---

### 📁 Folder Structure

```
forex-challenge/
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

### ⚙️ Setup Components

| Component             | Intentional Issue                               |
| --------------------- | ----------------------------------------------- |
| Currency Service      | CrashLoopBackOff due to wrong `DB_HOST` env var |
| Exchange Rate Service | Readiness probe fails (wrong path)              |
| Forex DB PVC          | Mounted to wrong path                           |
| NetworkPolicy         | Blocks currency-service                         |
| ResourceQuota         | Too restrictive (causes throttling)             |
| RBAC                  | Developer cannot deploy                         |
| Route                 | Missing for exchange-rate-service               |

---

### 🧩 Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: forex-challenge
```

```bash
oc apply -f forex-namespace.yaml
```

---

### 💥 Currency Service (CrashLoopBackOff)

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
          value: "wrong-db-host"   # Intentional error
```

---

### 💥 Exchange Rate Service (Readiness Probe Failure)

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
            path: /wrongpath     # Intentional misconfiguration
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

### 💥 Forex DB PVC (Incorrectly Mounted)

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
          mountPath: /wrongpath     # Wrong mount path
      volumes:
      - name: db-storage
        persistentVolumeClaim:
          claimName: forex-db-pvc
```

---

### 💥 Restrictive NetworkPolicy

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

### 💥 ResourceQuota (Throttling)

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

### 💥 RBAC (Developer Block)

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

### 💥 Missing Route (Instructor does not create)

Participants must run:

```bash
oc expose deployment exchange-rate-service --name=exchange-rate-route -n forex-challenge
```

---

### ✅ **Expected Instructor Setup Outcome**

| Component             | Status                     |
| --------------------- | -------------------------- |
| currency-service      | CrashLoopBackOff           |
| exchange-rate-service | Readiness probe fails      |
| currency-service      | Network blocked            |
| exchange-rate-service | Missing route              |
| forex-db              | PVC mount error            |
| Pods                  | Throttled by ResourceQuota |
| Developer             | RBAC blocked               |

---

### 🧭 Deployment Commands

```bash
# 1. Create namespace
oc apply -f forex-namespace.yaml

# 2. Deploy DB + PVC
oc apply -f deployments/forex-db.yaml

# 3. Deploy services
oc apply -f deployments/currency-service.yaml
oc apply -f deployments/exchange-rate-service.yaml

# 4. Apply restrictive network policy
oc apply -f network/restrictive-networkpolicy.yaml

# 5. Apply ResourceQuota
oc apply -f quotas/resourcequota.yaml

# 6. Apply RBAC restrictions
oc apply -f rbac/developer-block.yaml

# 7. Verify pods
oc get pods -n forex-challenge
```

---

# 🧩 troubleshooting-challenge.md

### **Integrated Troubleshooting Challenge – Hands-On Lab**

*(Participant Guide – SSK Training & Consulting)*

---

### 🎯 Objective

Simulate a **broken Forex app** with multiple failures.
Participants must restore full functionality by identifying and fixing all issues.

---

### 🧠 Scenario Setup

Namespace: `forex-challenge`

Instructor has deployed a faulty Forex app with these issues:

1. `currency-service` pod → CrashLoopBackOff (bad env var)
2. `exchange-rate-service` → readiness probe fails
3. NetworkPolicy blocks communication
4. Missing route for `exchange-rate-service`
5. ResourceQuota throttles pods
6. Developer RBAC restrictions
7. PVC mount incorrect for DB

Your challenge:
**“Restore full functionality of the Forex app.”**

---

## 🧩 Step 1: Identify Pod Failures (20 min)

* Check pod status:

  ```bash
  oc get pods -n forex-challenge
  ```
* Review logs and events:

  ```bash
  oc logs <pod-name> -n forex-challenge
  oc describe pod <pod-name> -n forex-challenge
  ```
* Fix misconfigured env var:

  ```bash
  oc set env deployment/currency-service DB_HOST=forex-db -n forex-challenge
  oc rollout restart deployment/currency-service -n forex-challenge
  ```

✅ **Outcome:** All pods reach *Running* state.

---

## 🌐 Step 2: Fix Network Issues (15 min)

1. Check NetworkPolicies:

   ```bash
   oc get networkpolicy -n forex-challenge
   oc describe networkpolicy <policy-name> -n forex-challenge
   ```
2. Test communication:

   ```bash
   oc exec -it <exchange-rate-pod> -n forex-challenge -- curl currency-service:8080
   ```
3. Fix policy:

   * Delete restrictive policy or create allow policy:

     ```yaml
     apiVersion: networking.k8s.io/v1
     kind: NetworkPolicy
     metadata:
       name: allow-exchange-to-currency
       namespace: forex-challenge
     spec:
       podSelector:
         matchLabels:
           app: currency-service
       policyTypes:
       - Ingress
       ingress:
       - from:
         - podSelector:
             matchLabels:
               app: exchange-rate-service
     ```

     ```bash
     oc apply -f allow-exchange-to-currency.yaml
     ```

✅ **Outcome:** Pods can communicate successfully.

---

## 🌍 Step 3: Restore Routes (10 min)

Check routes:

```bash
oc get route -n forex-challenge
```

Expose missing route:

```bash
oc expose deployment exchange-rate-service --name=exchange-rate-route -n forex-challenge
oc get route -n forex-challenge
```

✅ **Outcome:** External access restored.

---

## ⚙️ Step 4: Fix ResourceQuota & Throttling (15 min)

Check resource usage:

```bash
oc describe quota -n forex-challenge
oc describe pod <pod-name> -n forex-challenge
```

Update limits:

```bash
oc set resources deployment/currency-service \
  --requests=cpu=200m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi -n forex-challenge
```

✅ **Outcome:** No throttling; pods stable.

---

## 🔒 Step 5: Resolve RBAC Issues (10 min)

Simulate developer:

```bash
oc auth can-i create deployment -n forex-challenge --as developer
```

Fix RBAC:

```bash
oc adm policy add-role-to-user edit developer -n forex-challenge
```

✅ **Outcome:** Developer can deploy and manage resources.

---

## 🧱 Step 6: Verify Probes & PVC (10 min)

Check probe configuration:

```bash
oc describe pod <pod-name> -n forex-challenge
```

Fix readiness probe:

```bash
oc set probe deployment/exchange-rate-service \
  --readiness --get-url=http://:8080/ -n forex-challenge
```

Check DB PVC:

```bash
oc get pvc -n forex-challenge
oc describe pvc forex-db-pvc -n forex-challenge
```

✅ **Outcome:** Probes healthy, PVC correctly mounted.

---

## 🧭 Step 7: Apply Governance & Optimization (10 min)

```bash
oc label namespace forex-challenge pod-security.kubernetes.io/enforce=restricted
```

Review quotas and optimization best practices.

✅ **Outcome:** Governance and efficiency enforced.

---

## ✅ Step 8: Verification & Wrap-Up (10 min)

Final checks:

```bash
oc get pods -n forex-challenge
oc get route -n forex-challenge
```

All conditions met:

* Pods Running
* Internal & external connectivity
* Quotas respected
* Security enforced

🎉 **Challenge Completed – Forex app fully restored**
