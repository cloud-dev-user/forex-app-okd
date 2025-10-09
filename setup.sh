#!/bin/bash
set -e
oc apply -f oc-manifests/namespace-forex.yaml
oc project forex-app
oc apply -n forex-app -f oc-manifests/db/
oc apply -n forex-app -f oc-manifests/currency/
oc apply -n forex-app -f oc-manifests/exchange-rate/
oc apply -n forex-app -f oc-manifests/rbac/
oc apply -n forex-app -f oc-manifests/networkpolicy/
