````markdown
# 🧩 Forex Challenge – End-to-End Troubleshooting Guide (OpenShift on AWS)

## 🎯 Objective
This guide captures the real troubleshooting journey of deploying and fixing a broken three-tier app (`forex-challenge`) on OpenShift.  
It walks through failures step-by-step, explaining what went wrong, how to debug, and how to fix.

---

## 🧱 Environment Setup Overview

| Component | Description |
|------------|--------------|
| **Namespace** | `forex-challenge` | ## Please change namespace wiht your unique namespace name
| **Database** | MySQL 8.0 (`forex-db`) |
| **Microservices** | `currency-service` (port 5000), `exchange-rate-service` (port 5001) |
| **StorageClass** | `gp3-csi` |
| **Cluster** | OpenShift on AWS |
| **Intentional Breaks** | NetworkPolicy, ResourceQuota, RBAC, Readiness probe, Missing Service/Route |

---

## 🪜 Step-by-Step Troubleshooting Flow

### 🔹 Step 1 – Deploy Broken Environment
```bash
oc apply -f forex-namespace.yaml
oc apply -f deployments/forex-db.yaml
oc apply -f deployments/currency-service.yaml
oc apply -f deployments/exchange-rate-service.yaml
oc apply -f network/restrictive-networkpolicy.yaml
oc apply -f quotas/resourcequota.yaml
oc apply -f rbac/developer-block.yaml
````

**Observation:**

```bash
oc get pods -n forex-challenge
```

All pods stuck at `0/1` or `Pending`.

---

### 🔹 Step 2 – Identify Initial Failures

```bash
oc get events --sort-by='.lastTimestamp' | tail -n 20
```

**Findings:**

* Pods failing due to **quota enforcement**
* PVC waiting for binding
* Developer permissions restricted
* Network policy blocking communication

---

### ⚠️ Issue 1 – Resource Quota Blocking Pods

**Error:**

```
failed quota: forex-quota: must specify limits.cpu, limits.memory, requests.cpu, requests.memory
```

**Fix:**

```bash
oc patch resourcequota forex-quota -n forex-challenge --type merge \
  -p '{"spec":{"hard":{"pods":"10","requests.cpu":"1","requests.memory":"2Gi","limits.cpu":"2","limits.memory":"4Gi"}}}'
```

**Then add resource limits to all deployments:**

```bash
oc set resources deployment/forex-db \
  --requests=cpu=200m,memory=256Mi --limits=cpu=500m,memory=512Mi -n forex-challenge
oc set resources deployment/currency-service \
  --requests=cpu=200m,memory=256Mi --limits=cpu=500m,memory=512Mi -n forex-challenge
oc set resources deployment/exchange-rate-service \
  --requests=cpu=200m,memory=256Mi --limits=cpu=500m,memory=512Mi -n forex-challenge
```

Restart deployments:

```bash
oc rollout restart deployment/forex-db -n forex-challenge
oc rollout restart deployment/currency-service -n forex-challenge
oc rollout restart deployment/exchange-rate-service -n forex-challenge
```

✅ Verify:

```bash
oc get pods -n forex-challenge
```

---

### ⚠️ Issue 2 – NetworkPolicy Blocking Service Access

**Cause:** Restrictive `block-currency-service` network policy prevented ingress to the service.

**Fix:**

```bash
oc delete networkpolicy block-currency-service -n forex-challenge
```

---

### ⚠️ Issue 3 – Developer RBAC Restrictions

**Cause:** Developer role had only “view” access.

**Fix:**

```bash
oc delete rolebinding block-developer -n forex-challenge
oc adm policy add-role-to-user edit developer -n forex-challenge
```

✅ Verify:

```bash
oc auth can-i create pods --as developer -n forex-challenge
```

Should return **yes**.

---

### ⚠️ Issue 4 – Quota Exhaustion (CPU Limit Reached)

**Event:**

```
Error creating: exceeded quota: forex-quota, requested: limits.cpu=500m, used: limits.cpu=2, limited: limits.cpu=2
```

**Fix:**
Increase CPU and memory quota again:

```bash
oc patch resourcequota forex-quota -n forex-challenge --type merge \
  -p '{"spec":{"hard":{"pods":"10","requests.cpu":"2","requests.memory":"4Gi","limits.cpu":"4","limits.memory":"8Gi"}}}'
```

---

### ⚠️ Issue 5 – Readiness Probe Failure (404)

**Event:**

```
Readiness probe failed: HTTP probe failed with statuscode: 404
```

**Cause:** Wrong probe path `/wrongpath`.

**Fix:**

```bash
oc set probe deployment/exchange-rate-service \
  --readiness --get-url=http://:5001/health -n forex-challenge
oc rollout restart deployment/exchange-rate-service -n forex-challenge
```

✅ Verify:

```bash
oc describe pod -l app=exchange-rate-service -n forex-challenge | grep Readiness
```

---

### ⚠️ Issue 6 – Missing Services and Routes

**Symptom:**

```
$ oc get svc
No resources found in forex-challenge namespace.
```

**Fix:**
Recreate missing Services:

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: forex-db
  namespace: forex-challenge
spec:
  selector:
    app: forex-db
  ports:
  - port: 3306
    targetPort: 3306
EOF

cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: currency-service
  namespace: forex-challenge
spec:
  selector:
    app: currency-service
  ports:
  - port: 5000
    targetPort: 5000
EOF

cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: exchange-rate-service
  namespace: forex-challenge
spec:
  selector:
    app: exchange-rate-service
  ports:
  - port: 5001
    targetPort: 5001
EOF
```

Expose routes:

```bash
oc expose svc currency-service -n forex-challenge
oc expose svc exchange-rate-service -n forex-challenge
```

✅ Verify:

```bash
oc get svc -n forex-challenge
oc get routes -n forex-challenge
```

---

### ✅ Step 7 – Validate Application End-to-End

**Check Pods:**

```bash
oc get pods -n forex-challenge
```

**Check PVC Binding:**

```bash
oc get pvc -n forex-challenge
```

**Access Application:**

```bash
curl -i http://currency-service-forex-challenge.apps.okd-demo.cloudtraining.publicvm.com/
curl -i http://exchange-rate-service-forex-challenge.apps.okd-demo.cloudtraining.publicvm.com/
```

✅ Expected:

```
HTTP/1.1 200 OK
Currency Service is running
Exchange Rate Service is running
```

---

## 🧾 Final Verification Summary

| Check   | Command                          | Expected                   |
| ------- | -------------------------------- | -------------------------- |
| Pods    | `oc get pods -n forex-challenge` | All in `Running` state     |
| Quota   | `oc describe quota forex-quota`  | Enough CPU/memory headroom |
| PVC     | `oc get pvc`                     | `Bound`                    |
| Network | `oc get networkpolicy`           | No blocking rules          |
| Routes  | `oc get routes`                  | Public URLs visible        |
| Health  | `curl -i <route-url>`            | `HTTP/1.1 200 OK`          |

---

## 🧠 Lessons Learned

| Category            | Key Learning                                                   |
| ------------------- | -------------------------------------------------------------- |
| Resource Management | Always define CPU/memory requests and limits when quotas exist |
| RBAC                | Ensure appropriate roles (e.g. `edit`) before troubleshooting  |
| Network Policies    | Test ingress/egress impact using temporary deletions           |
| Probes              | Match probe endpoints with actual application routes           |
| Service Exposure    | `oc expose svc` is essential for external testing              |
| Quotas              | Monitor and tune namespace limits regularly                    |

---

## 🧹 Cleanup

```bash
oc delete project forex-challenge
oc new-project forex-challenge
```

