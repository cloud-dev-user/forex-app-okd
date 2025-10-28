
## Lab Guide: End-to-End Backup & Restore of MySQL on OpenShift (AWS)

---

### 🎯 Objective
In this lab, you will:

- Deploy a **MySQL 8.0** database backed by a Persistent Volume Claim (PVC)
- Insert sample data
- Back up the database, deployment manifests, and PVC snapshot
- Simulate data loss and restore the database

**Namespace:** `forex-app-user5`  
**Storage Class:** `gp3-csi`  

---

## 🧰 Prerequisites
- Access to an OpenShift cluster on AWS  
- `oc` CLI configured and logged in  
- A `VolumeSnapshotClass` (example: `csi-aws-vsc`)

Check available snapshot classes:
```bash
oc get volumesnapshotclass
````

---

## 🧩 Part 1 – Create Namespace and PVC

### 1️⃣ Create a Namespace

```bash
oc new-project forex-app-user5
```

### 2️⃣ Create PVC – `2_mysql-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: forex-app-user5
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: gp3-csi
```

Apply and verify:

```bash
oc apply -f manifests/2_mysql-pvc.yaml
oc get pvc -n forex-app-user5
```

✅ **Expected Result:** PVC status shows `pending`. It will go to `bound ` state once pod is created

---

## 🧱 Part 2 – Deploy MySQL

### Deployment – `3_mysql-deploy.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-db
  namespace: forex-app-user5
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql-db
  template:
    metadata:
      labels:
        app: mysql-db
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: redhat
        - name: MYSQL_DATABASE
          value: forexdb
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        persistentVolumeClaim:
          claimName: mysql-pvc
```

### Service – `4_mysql-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: forex-app-user5
spec:
  selector:
    app: mysql-db
  ports:
  - port: 3306
    targetPort: 3306
```

Apply:

```bash
oc apply -f manifests/3_mysql-deploy.yaml
oc apply -f manifests/4_mysql-service.yaml
oc get pods,svc -n forex-app-user5
```

✅ **Expected Result:** MySQL pod and service are running

---

## 💾 Part 3 – Insert Sample Data

Access MySQL pod:

```bash
oc rsh -n forex-app-user5 $(oc get pod -l app=mysql-db -o name -n forex-app-user5)
```

Login:

```bash
mysql -uroot -predhat forexdb
```

Insert data:

```sql
CREATE TABLE currency_rate (
  id INT AUTO_INCREMENT PRIMARY KEY,
  currency VARCHAR(10),
  rate FLOAT
);

INSERT INTO currency_rate (currency, rate)
VALUES ('USD',83.25),('EUR',89.50),('GBP',101.30);

SELECT * FROM currency_rate;
```

Exit:

```bash
exit
exit
```

✅ **Expected Result:** Table created and data inserted

---

## 🧩 Part 4 – Backup

### 1️⃣ Create backup folder and SQL Dump

```bash
mkdir backup
oc exec -i $(oc get pod -l app=mysql-db -o name -n forex-app-user5) -n forex-app-user5 -- \
  mysqldump -uroot -predhat forexdb > backup/forex-db-dump.sql
```

### 2️⃣ Backup Deployment YAMLs

```bash
oc get deploy,svc,configmap,secret -o yaml -n forex-app-user5 > backup/forex-db-backup.yaml
```

### 3️⃣ PVC Snapshot – `5_mysql-snapshot.yaml`

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-db-snapshot
  namespace: forex-app-user5
spec:
  volumeSnapshotClassName: csi-aws-vsc
  source:
    persistentVolumeClaimName: mysql-pvc
```

Apply and verify:

```bash
oc apply -f manifests/5_mysql-snapshot.yaml
oc get volumesnapshot -n forex-app-user5
```

✅ **Expected Result:** Snapshot shows `ReadyToUse: true`

---

## 💥 Part 5 – Simulate Data Loss

Delete DB and PVC:

```bash
oc delete deploy mysql-db -n forex-app-user5
oc delete pvc mysql-pvc -n forex-app-user5
```

✅ **Expected Result:** Pod and PVC deleted

---

## ♻️ Part 6 – Restore PVC from Snapshot

Create `6_mysql-restore-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: forex-app-user5
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: gp3-csi
  dataSource:
    name: mysql-db-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

Apply:

```bash
oc apply -f manifests/6_mysql-restore-pvc.yaml
oc get pvc -n forex-app-user5
```

✅ **Expected Result:** PVC recreated and *Bound*

---

## 🧱 Part 7 – Restore Deployment & Service

Reapply backups:

```bash
oc apply -f backup/forex-db-backup.yaml
oc get pods,svc -n forex-app-user5
```

✅ **Expected Result:** MySQL pod restarts with restored volume

---

## 🔍 Part 8 – Validate Restored Data

Access restored pod and verify:

```bash
oc rsh -n forex-app-user5 $(oc get pod -l app=mysql-db -o name -n forex-app-user5)
mysql -uroot -predhat forexdb
SELECT * FROM currency_rate;
```

✅ **Expected Result:** Table data (USD, EUR, GBP) appears again

---

## 🧾 Part 9 – (Optional) Restore from SQL Dump

If snapshot unavailable:

```bash
oc cp backup/forex-db-dump.sql $(oc get pod -l app=mysql-db -o name -n forex-app-user5):/tmp/ -n forex-app-user5
oc rsh -n forex-app-user5 $(oc get pod -l app=mysql-db -o name -n forex-app-user5)
mysql -uroot -predhat forexdb < /tmp/forex-db-dump.sql
```

✅ **Expected Result:** Database restored from SQL dump

