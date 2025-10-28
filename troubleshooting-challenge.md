````markdown
# 🧩 Integrated Troubleshooting Challenge – Hands-On Lab  
---

## 🎯 Objective

This hands-on challenge simulates a **broken Forex Application** deployed on **OpenShift (AWS)**.  
You will identify and fix configuration, networking, and access issues until all components are fully functional.

---

## 🧠 Background

The Forex App contains three major components:

| Component | Port | Description |
|------------|------|-------------|
| `forex-db` | 3306 | MySQL database backend |
| `currency-service` | 5000 | REST API for currency data |
| `exchange-rate-service` | 5001 | REST API for exchange rate conversion |

Your instructor has deployed a deliberately **broken version** to test your troubleshooting skills.  

---

## 🧾 Lab Environment

| Parameter | Value |
|------------|--------|
| Namespace | `forex-challenge` |
| Cluster | OpenShift on AWS |
| Storage Class | `gp3-csi` (default) |

---

# 🧩 Step 1 – Environment Assessment

### 🧭 Inspect Namespace Resources
```bash
oc project forex-challenge
oc get all -n forex-challenge
oc get events -n forex-challenge --sort-by=.lastTimestamp
````

Look for:

* Pods in `CrashLoopBackOff` or `NotReady` state
* Failed probes
* Quota errors or blocked deployments

---

## 🔍 Inspect Pod Details

```bash
oc get pods -n forex-challenge
oc describe pod <pod-name> -n forex-challenge
```

Typical state:

```
currency-service-xxxx     CrashLoopBackOff
exchange-rate-service-xxx  Running (0/1 Ready)
forex-db-xxxxxx            Running
```

---

# 💥 Step 2 – Fix `currency-service` CrashLoopBackOff

### 🔹 Problem

* The service fails to connect to the database.
* Root cause: Incorrect environment variable `DB_HOST`.

### 🔎 Investigation

```bash
oc logs deployment/currency-service -n forex-challenge
```

You’ll likely see:

```
Error: unable to connect to host wrong-db-host:3306
```

### 🧩 Fix

```bash
oc set env deployment/currency-service DB_HOST=forex-db -n forex-challenge
oc rollout restart deployment/currency-service -n forex-challenge
```

### ✅ Verify

```bash
oc get pods -n forex-challenge
oc logs deployment/currency-service -n forex-challenge
```

✅ **Expected Result:** Pod transitions to `Running` with no crash loops.

---

# 💥 Step 3 – Fix Readiness Probe Failure (`exchange-rate-service`)

### 🔹 Problem

* Pod never becomes ready.
* Readiness probe uses incorrect path or port.

### 🔎 Investigation

```bash
oc describe pod <exchange-rate-pod> -n forex-challenge
```

Expected error:

```
Readiness probe failed: HTTP probe failed with statuscode: 404
```

### 🧩 Fix Probe Configuration

```bash
oc set probe deployment/exchange-rate-service \
  --readiness --get-url=http://:5001/ -n forex-challenge
oc rollout restart deployment/exchange-rate-service -n forex-challenge
```

### ✅ Verify

```bash
oc get pods -n forex-challenge
oc describe pod <exchange-rate-pod> -n forex-challenge
```

✅ **Expected Result:** Probe succeeds and pod is marked `Ready 1/1`.

---

# 💥 Step 4 – NetworkPolicy Blocks Access

### 🔹 Problem

* `exchange-rate-service` cannot call `currency-service` on port 5000.
* A restrictive NetworkPolicy blocks ingress.

### 🔎 Investigation

```bash
oc get networkpolicy -n forex-challenge
oc describe networkpolicy block-currency-service -n forex-challenge
```

You’ll see:

```yaml
ingress: []
```

### 🧩 Fix

Create an allow policy.

**File: allow-exchange-to-currency.yaml**

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
    ports:
    - protocol: TCP
      port: 5000
```

Apply:

```bash
oc apply -f allow-exchange-to-currency.yaml
```

### ✅ Verify

```bash
oc exec -it $(oc get pod -l app=exchange-rate-service -n forex-challenge -o name) -n forex-challenge -- curl currency-service:5000
```

✅ **Expected Result:** Response returned successfully (HTTP 200).

---

# 💥 Step 5 – Missing External Route for `exchange-rate-service`

### 🔹 Problem

* No route exists to access the service externally.

### 🔎 Investigation

```bash
oc get route -n forex-challenge
```

Output: none.

### 🧩 Fix

Expose a route on port **5001**:

```bash
oc expose deployment exchange-rate-service \
  --name=exchange-rate-route \
  --port=5001 -n forex-challenge
```

### ✅ Verify

```bash
oc get route -n forex-challenge
```

✅ **Expected Result:** Route available with external hostname (e.g., `exchange-rate-route-forex-challenge.apps.cluster...`).

---

# 💥 Step 6 – ResourceQuota Too Restrictive

### 🔹 Problem

* Pods throttled or pending due to CPU/memory limits.

### 🔎 Investigation

```bash
oc describe quota -n forex-challenge
```

Typical output:

```
pods: 1 used of 1
requests.cpu: 150m hard limit
```

### 🧩 Fix Resource Limits

```bash
oc set resources deployment/currency-service \
  --requests=cpu=200m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi -n forex-challenge
```

Patch quota if required:

```bash
oc patch resourcequota forex-quota -n forex-challenge --type merge -p \
'{"spec":{"hard":{"pods":"5","requests.cpu":"1","limits.cpu":"2"}}}'
```

### ✅ Verify

```bash
oc describe quota -n forex-challenge
oc get pods -n forex-challenge
```

✅ **Expected Result:** All pods scheduled and stable.

---

# 💥 Step 7 – RBAC Restriction

### 🔹 Problem

* Developer cannot create or edit deployments.

### 🔎 Investigation

```bash
oc auth can-i create deployment -n forex-challenge --as developer
```

Output: `no`

### 🧩 Fix

```bash
oc adm policy add-role-to-user edit developer -n forex-challenge
```

### ✅ Verify

```bash
oc auth can-i create deployment -n forex-challenge --as developer
```

✅ **Expected Result:** `yes`

---

# 💥 Step 8 – PVC Mount Path Incorrect (`forex-db`)

### 🔹 Problem

* MySQL database mounted at wrong path `/wrongpath`.

### 🔎 Investigation

```bash
oc describe pod <forex-db-pod> -n forex-challenge | grep Mount
```

### 🧩 Fix

Edit deployment:

```bash
oc edit deployment forex-db -n forex-challenge
```

Change:

```yaml
mountPath: /var/lib/mysql
```

Apply and restart:

```bash
oc rollout restart deployment/forex-db -n forex-challenge
```

### ✅ Verify

```bash
oc exec -it $(oc get pod -l app=forex-db -n forex-challenge -o name) -n forex-challenge -- ls /var/lib/mysql
```

✅ **Expected Result:** MySQL data directory visible.

---

# 💥 Step 9 – Governance & Security Enforcement

Apply OpenShift Pod Security Standards.

```bash
oc label namespace forex-challenge pod-security.kubernetes.io/enforce=restricted
```

✅ **Expected Result:** Namespace labeled successfully.

---

# 🧭 Step 10 – Final Validation

Run final checks:

```bash
oc get pods,svc,route,networkpolicy,quota -n forex-challenge
```

✅ **Expected Results**

| Component             | Port                  | Status  |
| --------------------- | --------------------- | ------- |
| currency-service      | 5000                  | Running |
| exchange-rate-service | 5001                  | Running |
| forex-db              | 3306                  | Running |
| Route                 | Accessible externally |         |
| PVC                   | Bound                 |         |
| RBAC                  | Corrected             |         |
| Quota                 | Adjusted              |         |
| NetworkPolicy         | Fixed                 |         |

---

# 🏁 Challenge Summary

| Issue                               | Root Cause            | Resolution                 |
| ----------------------------------- | --------------------- | -------------------------- |
| `currency-service` CrashLoopBackOff | Wrong DB_HOST         | Set to `forex-db`          |
| `exchange-rate-service` not ready   | Wrong probe path/port | Fixed probe to `:5001/`    |
| NetworkPolicy                       | All ingress blocked   | Created allow policy       |
| Missing route                       | None created          | Exposed route on port 5001 |
| ResourceQuota                       | Too low               | Increased CPU/memory       |
| RBAC                                | View-only             | Granted `edit` role        |
| PVC mount                           | Wrong directory       | Fixed to `/var/lib/mysql`  |

✅ **Final Outcome:** Forex Application fully functional and reachable.

---

# 📸 Screenshots to Capture

1. `oc get pods -n forex-challenge`
2. `oc get route -n forex-challenge`
3. `curl` from exchange-rate → currency-service (5000)
4. Route access output in browser
