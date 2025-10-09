build:
	docker build -t currency-service ./services/currency-service
	docker build -t exchange-rate-service ./services/exchange-rate-service

deploy:
	oc apply -f oc-manifests/namespace-forex.yaml
	oc apply -n forex-app -f oc-manifests/db/
	oc apply -n forex-app -f oc-manifests/currency/
	oc apply -n forex-app -f oc-manifests/exchange-rate/
	oc apply -n forex-app -f oc-manifests/rbac/
	oc apply -n forex-app -f oc-manifests/networkpolicy/
